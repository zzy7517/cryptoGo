"""
Agent 处理函数
所有 Agent 相关的业务逻辑处理
创建时间: 2025-10-29
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
    1. 使用 DeepSeek AI 分析市场数据
    2. 通过 Function Calling 调用工具（获取数据、执行交易等）
    3. 做出交易决策
    4. 返回决策结果
    
    注意：这是单次执行，不会后台挂机
    
    Args:
        session_id: 交易会话 ID
        request: 请求参数
        
    Returns:
        决策结果
    """
    logger.info(
        "收到 Agent V2 运行请求",
        session_id=session_id,
        symbols=request.symbols,
        model=request.model
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
        # 运行 Agent
        result = await run_trading_agent(
            session_id=session_id,
            symbols=request.symbols,
            risk_params=request.risk_params,
            max_iterations=request.max_iterations
        )
        
        logger.info(
            "Agent V2 运行完成",
            session_id=session_id,
            success=result.get("success"),
            iterations=result.get("iterations")
        )
        
        return RunAgentResponse(
            success=result.get("success", False),
            session_id=session_id,
            decision=result.get("decision"),
            iterations=result.get("iterations", 0),
            tools_used=result.get("tools_used", []),
            error=result.get("error")
        )
        
    except Exception as e:
        logger.exception(f"Agent V2 运行失败: {session_id}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent 运行失败: {str(e)}"
        )


async def start_background_agent(
    session_id: int,
    request: RunAgentRequest
):
    """
    启动后台挂机 Agent
    
    Agent 将在后台线程中持续运行，按设定的间隔自动执行决策
    
    Args:
        session_id: 会话 ID
        request: 配置参数，包含 decision_interval（秒）
    """
    logger.info(
        "启动后台 Agent",
        session_id=session_id,
        symbols=request.symbols
    )
    
    # 验证会话存在
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
                detail=f"会话状态为 {session.status}，不能启动 Agent"
            )
    finally:
        db.close()
    
    try:
        manager = get_background_agent_manager()
        
        # 决策间隔，默认 5 分钟
        decision_interval = request.risk_params.get("decision_interval", 300) if request.risk_params else 300
        
        result = manager.start_background_agent(
            session_id=session_id,
            symbols=request.symbols,
            risk_params=request.risk_params,
            decision_interval=decision_interval,
            max_iterations=request.max_iterations
        )
        
        return {
            "success": True,
            "message": "后台 Agent 已启动",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
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
                "max_leverage": 3,
                "max_positions": 3
            },
            max_iterations=request.max_iterations
        )
        
        return {
            "success": result.get("success", False),
            "decision": result.get("decision"),
            "iterations": result.get("iterations", 0),
            "tools_used": result.get("tools_used", []),
            "error": result.get("error"),
            "note": "这是测试模式，未保存到数据库"
        }
        
    except Exception as e:
        logger.exception("Agent 测试失败")
        raise HTTPException(
            status_code=500,
            detail=f"测试失败: {str(e)}"
        )

