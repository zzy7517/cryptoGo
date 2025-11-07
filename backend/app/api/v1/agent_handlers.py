"""
Agent 处理函数（定时循环版本，无 LangChain）
所有 Agent 相关的业务逻辑处理
创建时间: 2025-10-30
"""
from fastapi import HTTPException

from ...schemas.agent import RunAgentRequest
from ...services.trading_agent_service import get_background_agent_manager
from ...repositories.trading_session_repo import TradingSessionRepository
from ...utils.database import get_db
from ...utils.logging import get_logger

logger = get_logger(__name__)


async def start_background_agent(
    session_id: int,
    request: RunAgentRequest
):
    """
    启动后台交易（定时循环模式）

    工作流程:
    1. 验证交易会话是否存在且状态为 running
    2. 获取后台交易管理器（单例模式）
    3. 创建并启动后台 asyncio.Task，使用定时循环执行决策
    4. 每个周期：收集数据 -> 调用 AI -> 执行决策 -> 保存
    5. 返回启动成功的结果

    """
    # 记录启动日志
    logger.info(
        "启动后台 Agent (asyncio 版本)",
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
                detail=f"会话状态为 {session.status}，不能启动后台交易"
            )
    finally:
        db.close()

    try:
        # 步骤2: 获取全局单例的后台交易管理器
        manager = get_background_agent_manager()

        # 步骤3: 解析决策间隔参数
        # 从 risk_params 中获取 decision_interval，默认 180 秒（3 分钟）
        decision_interval = request.risk_params.get("decision_interval", 180) if request.risk_params else 180

        # 步骤4: 启动后台 Agent（asyncio.Task）
        result = await manager.start_background_agent(
            session_id=session_id,
            symbols=request.symbols,
            risk_params=request.risk_params,
            decision_interval=decision_interval  # 定时循环间隔
        )

        # 步骤5: 返回成功结果
        return {
            "success": True,
            "message": "后台 Agent 已启动 (asyncio Task)",
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
    停止后台 Agent (asyncio 版本)
    
    停止指定会话的后台挂机 Agent
    """
    logger.info("停止后台 Agent (asyncio)", session_id=session_id)
    
    try:
        manager = get_background_agent_manager()
        result = await manager.stop_background_agent(session_id)
        
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
    获取后台 Agent 状态 (asyncio 版本)
    
    返回后台挂机 Agent 的运行状态
    """
    manager = get_background_agent_manager()
    status = await manager.get_agent_status(session_id)
    
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


