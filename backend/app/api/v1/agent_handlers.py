"""
Agent 处理函数（定时循环版本，无 LangChain）
所有 Agent 相关的业务逻辑处理
创建时间: 2025-10-30
"""
from fastapi import HTTPException

from app.schemas.agent import RunAgentRequest, RunAgentResponse
from app.services.trading_agent_service import run_trading_agent, get_background_agent_manager
from app.repositories.trading_session_repo import TradingSessionRepository
from app.utils.database import get_db
from app.utils.logging import get_logger

logger = get_logger(__name__)

async def run_agent_once(
    session_id: int,
    request: RunAgentRequest
) -> RunAgentResponse:
    """
    运行一次决策周期（单次执行）
    
    该端点会：
    1. 预先收集所有数据（账户、持仓、市场数据）
    2. 一次性调用 AI 进行分析
    3. AI 返回结构化的决策列表
    4. 执行决策
    5. 保存到数据库
    
    注意：这是单次执行，不会后台挂机
    
    Args:
        session_id: 交易会话 ID
        request: 请求参数
        
    Returns:
        决策结果
    """
    logger.info(
        "收到 Agent 单次运行请求",
        session_id=session_id,
        symbols=request.symbols
    )
    
    # 验证会话是否存在
    db = next(get_db())
    try:
        session_repo = TradingSessionRepository(db)
        session = session_repo.get_by_id(session_id)
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"会话 {session_id} 不存在"
            )
        
        if session.status != "running":
            raise HTTPException(
                status_code=400,
                detail=f"会话状态为 {session.status}，不能运行 Agent"
            )
    finally:
        db.close()
    
    try:
        # 运行 Agent（单次）
        result = await run_trading_agent(
            session_id=session_id,
            symbols=request.symbols,
            risk_params=request.risk_params
        )
        
        logger.info(
            "Agent 单次运行完成",
            session_id=session_id,
            success=result.get("success"),
            decisions_count=result.get("decisions_count", 0)
        )
        
        return RunAgentResponse(
            success=result.get("success", False),
            session_id=session_id,
            decision=result.get("ai_response"),
            iterations=result.get("call_count", 1),
            tools_used=[],  # 不再使用工具调用，返回空列表
            error=result.get("error")
        )
        
    except Exception as e:
        logger.exception(f"Agent 单次运行失败: {session_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 运行失败: {str(e)}"
        )


async def start_background_agent(
    session_id: int,
    request: RunAgentRequest
):
    """
    启动后台交易 Agent（挂机模式 - 定时循环）

    工作流程:
    1. 验证交易会话是否存在且状态为 running
    2. 获取后台 Agent 管理器（单例模式）
    3. 创建并启动后台线程，线程中使用定时循环执行决策
    4. 每个周期：收集数据 -> 调用 AI -> 执行决策 -> 保存
    5. 返回启动成功的结果

    """
    # 记录启动日志
    logger.info(
        "启动后台 Agent（定时循环模式）",
        session_id=session_id,
        symbols=request.symbols
    )

    # 步骤1: 验证会话存在且状态正确
    db = next(get_db())
    try:
        session_repo = TradingSessionRepository(db)
        session = session_repo.get_by_id(session_id)

        # 会话不存在，返回 404 错误
        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"会话 {session_id} 不存在"
            )

        if session.status != "running":
            raise HTTPException(
                status_code=400,
                detail=f"会话状态为 {session.status}，不能启动 Agent"
            )
    finally:
        db.close()

    try:
        # 步骤2: 获取全局单例的后台 Agent 管理器
        manager = get_background_agent_manager()

        # 步骤3: 解析决策间隔参数
        # 从 risk_params 中获取 decision_interval，默认 180 秒（3 分钟）
        decision_interval = request.risk_params.get("decision_interval", 180) if request.risk_params else 180

        # 步骤4: 启动后台 Agent（定时循环）
        result = manager.start_background_agent(
            session_id=session_id,
            symbols=request.symbols,
            risk_params=request.risk_params,
            decision_interval=decision_interval  # 定时循环间隔
        )

        # 步骤5: 返回成功结果
        return {
            "success": True,
            "message": "后台 Agent 已启动（定时循环模式）",
            "data": result
        }

    except ValueError as e:
        # ValueError 通常表示业务逻辑错误（如 Agent 已存在）
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 捕获所有其他异常，记录错误日志
        logger.exception(f"启动后台 Agent 失败: {session_id}")
        raise HTTPException(
            status_code=500,
            detail=f"启动失败: {str(e)}"
        )


async def stop_background_agent(session_id: int):
    """
    停止后台 Agent
    
    停止指定会话的后台挂机 Agent
    """
    logger.info("停止后台 Agent", session_id=session_id)
    
    try:
        manager = get_background_agent_manager()
        result = manager.stop_background_agent(session_id)
        
        return {
            "success": True,
            "message": "后台 Agent 已停止",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"停止后台 Agent 失败: {session_id}")
        raise HTTPException(
            status_code=500,
            detail=f"停止失败: {str(e)}"
        )


async def get_background_status(session_id: int):
    """
    获取后台 Agent 状态
    
    返回后台挂机 Agent 的运行状态
    """
    manager = get_background_agent_manager()
    status = manager.get_agent_status(session_id)
    
    if status is None:
        return {
            "success": True,
            "data": None,
            "message": f"Session {session_id} 的后台 Agent 未运行"
        }
    
    return {
        "success": True,
        "data": status
    }


async def list_background_agents():
    """
    列出所有后台运行的 Agent
    """
    manager = get_background_agent_manager()
    agents = manager.list_agents()
    
    return {
        "success": True,
        "data": agents,
        "count": len(agents)
    }


async def test_agent(request: RunAgentRequest):
    """
    测试 Agent（单次运行，不需要真实会话）
    
    用于快速测试 Agent 功能，使用模拟会话
    """
    logger.info("测试 Agent", symbols=request.symbols)
    
    # 使用会话 ID = 999999 作为测试
    test_session_id = 999999
    
    try:
        result = await run_trading_agent(
            session_id=test_session_id,
            symbols=request.symbols,
            risk_params=request.risk_params or {
                "max_position_size": 0.2,
                "stop_loss_pct": 0.05,
                "take_profit_pct": 0.10,
                "max_leverage": 3
            }
        )
        
        return {
            "success": result.get("success", False),
            "decision": result.get("ai_response"),
            "decisions_count": result.get("decisions_count", 0),
            "call_count": result.get("call_count", 1),
            "error": result.get("error"),
            "note": "这是测试模式，未保存到数据库"
        }
        
    except Exception as e:
        logger.exception("Agent 测试失败")
        raise HTTPException(
            status_code=500,
            detail=f"测试失败: {str(e)}"
        )
