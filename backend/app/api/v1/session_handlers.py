"""
交易会话处理函数
所有会话相关的业务逻辑处理
创建时间: 2025-10-29
"""
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
        # 1. 创建会话
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

        # 2. 如果需要，自动启动 Agent
        agent_started = False
        agent_error = None

        if request.auto_start_agent:
            try:
                # 验证必需参数
                if not request.symbols or len(request.symbols) == 0:
                    raise ValueError("启动 Agent 需要至少选择一个交易币种")

                # 获取后台 Agent 管理器
                manager = get_background_agent_manager()

                # 构建风险参数
                risk_params = request.risk_params or {}
                risk_params["decision_interval"] = request.decision_interval

                # 启动后台 Agent
                agent_result = await manager.start_background_agent(
                    session_id=session.id,
                    symbols=request.symbols,
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

        # 3. 返回响应
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
        
        return {
            "success": True,
            "data": {
                "session_id": session.id,
                "session_name": session.session_name,
                "status": session.status,
                "initial_capital": float(session.initial_capital) if session.initial_capital else None,
                "created_at": session.created_at.isoformat(),
                "config": session.config,
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

        # 转换为前端友好的格式
        decisions_data = []
        for d in decisions:
            decisions_data.append({
                "id": d.id,
                "created_at": d.created_at.isoformat(),
                "symbols": d.symbols,
                "decision_type": d.decision_type,
                "confidence": float(d.confidence) if d.confidence else None,
                "prompt_data": d.prompt_data,  # 用户输入（市场数据）
                "ai_response": d.ai_response,  # AI原始回复
                "reasoning": d.reasoning,  # AI推理过程
                "suggested_actions": d.suggested_actions,  # 建议操作
                "executed": d.executed,
                "execution_result": d.execution_result
            })

        return {
            "success": True,
            "data": decisions_data,
            "count": len(decisions_data)
        }
    except Exception as e:
        logger.error(f"获取AI决策记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取AI决策记录失败: {str(e)}")

