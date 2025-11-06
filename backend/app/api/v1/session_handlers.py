"""
交易会话处理函数
所有会话相关的业务逻辑处理
创建时间: 2025-10-29
更新时间: 2025-11-04 - 添加 JSON 反序列化支持（SQLite 兼容）
"""
import json
from fastapi import HTTPException, Depends, Query
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ...utils.database import get_db
from ...services.trading_session_service import TradingSessionService
from ...services.trading_agent_service import get_background_agent_manager
from ...utils.logging import get_logger
from ...utils.exceptions import BusinessException
from ...schemas.session import StartSessionRequest, EndSessionRequest

logger = get_logger(__name__)


async def start_session(
    request: StartSessionRequest,
    db: Session = Depends(get_db)
):
    """
    开始新的交易会话（并可选自动启动 Agent）

    创建一个新的交易会话。如果已有活跃会话，则返回错误。
    如果 auto_start_agent=True，则自动启动后台 Agent。
    """
    try:
        # 1. 检查账户余额（排除保证金）
        if request.initial_capital:
            from ...services.account_service import AccountService
            
            try:
                account_service = AccountService.get_instance()
                account_info = account_service.get_account_info()
                available_balance = account_info.get('availableBalance', 0)
                
                logger.info(
                    f"检查账户余额: 可用余额={available_balance} USDT, 请求金额={request.initial_capital} USDT"
                )
                
                # 如果输入金额大于可用余额，返回错误
                if request.initial_capital > available_balance:
                    raise BusinessException(
                        f"账户余额不足！可用余额: {available_balance:.2f} USDT，请求金额: {request.initial_capital:.2f} USDT",
                        error_code="INSUFFICIENT_BALANCE"
                    )
            except BusinessException:
                # 重新抛出业务异常
                raise
            except Exception as e:
                # 如果获取账户信息失败，记录警告但不阻止会话创建
                logger.warning(f"无法获取账户信息: {str(e)}，跳过余额检查")
        
        # 2. 创建会话
        service = TradingSessionService(db)
        session = service.start_session(
            session_name=request.session_name,
            initial_capital=request.initial_capital,
            config=request.config
        )

        # 准备响应数据
        response_data = {
            "session_id": session.id,
            "session_name": session.session_name,
            "status": session.status,
            "initial_capital": float(session.initial_capital) if session.initial_capital else None,
            "created_at": session.created_at.isoformat()
        }

        # 3. 如果需要，自动启动 Agent
        agent_started = False
        agent_error = None

        if request.auto_start_agent:
            try:
                # 使用默认交易币种（如果没有提供）
                symbols = request.symbols
                if not symbols or len(symbols) == 0:
                    # 默认使用 BTC, ETH, DOGE
                    symbols = ["BTC/USDT:USDT", "ETH/USDT:USDT", "DOGE/USDT:USDT"]
                    logger.info(f"未提供交易币种，使用默认值: {symbols}")

                # 获取后台 Agent 管理器
                manager = get_background_agent_manager()

                # 构建风险参数
                risk_params = request.risk_params or {}
                risk_params["decision_interval"] = request.decision_interval

                # 启动后台 Agent
                agent_result = await manager.start_background_agent(
                    session_id=session.id,
                    symbols=symbols,
                    risk_params=risk_params,
                    decision_interval=request.decision_interval
                )

                agent_started = True
                response_data["agent_status"] = agent_result

                logger.info(
                    f"会话 {session.id} 创建成功，Agent 已自动启动",
                    session_id=session.id,
                    symbols=request.symbols,
                    decision_interval=request.decision_interval
                )

            except Exception as e:
                # Agent 启动失败不影响会话创建
                agent_error = str(e)
                logger.warning(
                    f"会话 {session.id} 创建成功，但 Agent 启动失败: {agent_error}",
                    session_id=session.id
                )

        # 4. 返回响应
        message = "交易会话已开始"
        if agent_started:
            message += "，Agent 已启动"
        elif agent_error:
            message += f"，但 Agent 启动失败: {agent_error}"

        response_data["agent_started"] = agent_started
        if agent_error:
            response_data["agent_error"] = agent_error

        return {
            "success": True,
            "message": message,
            "data": response_data
        }

    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"开始会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"开始会话失败: {str(e)}")


async def end_session(
    request: EndSessionRequest,
    db: Session = Depends(get_db)
):
    """
    结束交易会话
    
    结束指定会话或当前活跃会话，并计算最终统计数据。
    同时自动停止该会话的交易代理（如果正在运行）。
    """
    try:
        logger.info(
            f"收到结束会话请求",
            session_id=request.session_id,
            status=request.status,
            notes=request.notes
        )
        
        service = TradingSessionService(db)
        session = service.end_session(
            session_id=request.session_id,
            status=request.status,
            notes=request.notes
        )
        
        # 自动停止该会话的 Agent（如果正在运行）
        manager = get_background_agent_manager()
        agent_status = await manager.get_agent_status(session.id)
        
        if agent_status:
            try:
                await manager.stop_background_agent(session.id)
                logger.info(f"已自动停止会话 {session.id} 的 Agent")
            except Exception as e:
                logger.warning(f"停止 Agent 失败: {str(e)}")
        
        return {
            "success": True,
            "message": "交易会话已结束",
            "data": {
                "session_id": session.id,
                "session_name": session.session_name,
                "status": session.status,
                "final_capital": float(session.final_capital) if session.final_capital else None,
                "total_pnl": float(session.total_pnl) if session.total_pnl else None,
                "total_return_pct": float(session.total_return_pct) if session.total_return_pct else None,
                "ended_at": session.ended_at.isoformat() if session.ended_at else None
            }
        }
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"结束会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"结束会话失败: {str(e)}")


async def get_active_session(db: Session = Depends(get_db)):
    """
    获取当前活跃的交易会话
    
    返回当前正在运行的会话信息，包括 Agent 状态。
    """
    try:
        service = TradingSessionService(db)
        session = service.get_active_session()
        
        if not session:
            return {
                "success": True,
                "data": None,
                "message": "没有活跃的交易会话"
            }
        
        # 获取 Agent 状态
        manager = get_background_agent_manager()
        agent_status = await manager.get_agent_status(session.id)

        # 反序列化 JSON 字段
        config = json.loads(session.config) if session.config else None

        return {
            "success": True,
            "data": {
                "session_id": session.id,
                "session_name": session.session_name,
                "status": session.status,
                "initial_capital": float(session.initial_capital) if session.initial_capital else None,
                "created_at": session.created_at.isoformat(),
                "config": config,
                "agent_status": agent_status  # 添加 Agent 状态
            }
        }
    except Exception as e:
        logger.error(f"获取活跃会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取活跃会话失败: {str(e)}")


async def get_session_list(
    status: Optional[str] = Query(None, description="过滤状态: running, completed, stopped, crashed"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取交易会话列表
    
    返回历史会话列表，可以按状态过滤。
    """
    try:
        service = TradingSessionService(db)
        sessions = service.get_session_list(status=status, limit=limit)
        
        return {
            "success": True,
            "data": sessions,
            "count": len(sessions)
        }
    except Exception as e:
        logger.error(f"获取会话列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


async def get_session_details(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    获取会话详细信息

    返回指定会话的完整信息，包括持仓、交易、决策等。
    """
    try:
        service = TradingSessionService(db)
        details = service.get_session_details(session_id)

        return {
            "success": True,
            "data": details
        }
    except BusinessException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取会话详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取会话详情失败: {str(e)}")


async def get_ai_decisions(
    session_id: int,
    limit: int = Query(50, ge=1, le=200, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取会话的AI决策记录

    返回指定会话的AI决策历史，包含完整的prompt数据、AI推理过程和决策结果。
    用于前端展示聊天记录。
    """
    try:
        from ...repositories.ai_decision_repo import AIDecisionRepository

        decision_repo = AIDecisionRepository(db)
        decisions = decision_repo.get_by_session(session_id, limit=limit)

        decisions_data = []
        for d in decisions:
            # 反序列化 JSON 字段
            symbols = json.loads(d.symbols) if d.symbols else []
            prompt_data = json.loads(d.prompt_data) if d.prompt_data else None
            suggested_actions = json.loads(d.suggested_actions) if d.suggested_actions else []
            execution_result = json.loads(d.execution_result) if d.execution_result else None
            
            decisions_data.append({
                "id": d.id,
                "created_at": d.created_at.isoformat(),
                "symbols": symbols,  # 反序列化为数组
                "decision_type": d.decision_type,
                "confidence": float(d.confidence) if d.confidence else None,
                "prompt_data": prompt_data,  # 反序列化为对象
                "ai_response": d.ai_response,  # AI原始回复
                "reasoning": d.reasoning,  # AI推理过程
                "suggested_actions": suggested_actions,  # 反序列化为数组
                "executed": d.executed,
                "execution_result": execution_result  # 反序列化为对象
            })

        return {
            "success": True,
            "data": decisions_data,
            "count": len(decisions_data)
        }
    except Exception as e:
        logger.error(f"获取AI决策记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取AI决策记录失败: {str(e)}")


async def get_asset_timeline(
    session_id: int,
    db: Session = Depends(get_db)
):
    """
    获取会话的资产变化时序数据（全量版）

    返回指定会话的所有AI决策记录，包括账户余额、浮动盈亏和总资产。

    由于AI决策频率较低（通常每3分钟一次），数据量很小，直接返回全量数据。

    参数：
    - session_id: 会话ID
    """
    try:
        from ...repositories.ai_decision_repo import AIDecisionRepository

        decision_repo = AIDecisionRepository(db)

        # 获取所有有账户信息的决策记录（按时间正序）
        all_decisions = decision_repo.get_by_session(session_id, limit=10000)
        all_decisions.reverse()  # 转为正序

        # 过滤出有账户信息的记录
        valid_decisions = [d for d in all_decisions if d.account_balance is not None]

        if not valid_decisions:
            return {
                "success": True,
                "data": [],
                "count": 0,
                "metadata": {
                    "total_records": 0
                }
            }

        # 返回所有数据
        timeline_data = []
        for d in valid_decisions:
            timeline_data.append({
                "timestamp": d.created_at.isoformat(),
                "account_balance": float(d.account_balance),
                "unrealized_pnl": float(d.unrealized_pnl) if d.unrealized_pnl is not None else 0,
                "total_asset": float(d.total_asset) if d.total_asset is not None else float(d.account_balance),
                "decision_type": d.decision_type
            })

        return {
            "success": True,
            "data": timeline_data,
            "count": len(timeline_data),
            "metadata": {
                "total_records": len(valid_decisions)
            }
        }
    except Exception as e:
        logger.error(f"获取资产变化时序数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取资产变化时序数据失败: {str(e)}")

