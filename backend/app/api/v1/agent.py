"""
Trading Agent API 路由
提供 Agent 控制相关的 RESTful API 端点
创建时间: 2025-10-29
"""
from fastapi import APIRouter, HTTPException, Body, Depends
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.services.trading_agent_service import get_agent_service
from app.core.database import get_db
from app.repositories.trading_session_repo import TradingSessionRepository
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/start")
async def start_agent(
    session_id: Optional[int] = Body(None, description="会话 ID，不提供则使用当前活跃会话"),
    decision_interval: int = Body(60, ge=10, le=3600, description="决策间隔（秒），10-3600"),
    symbols: Optional[List[str]] = Body(None, description="交易对列表"),
    risk_params: Optional[Dict[str, Any]] = Body(None, description="风险参数"),
    db: Session = Depends(get_db)
):
    """
    启动交易代理
    
    为指定会话或当前活跃会话启动自动交易代理。
    """
    try:
        # 如果未指定 session_id，获取当前活跃会话
        if session_id is None:
            session_repo = TradingSessionRepository(db)
            active_session = session_repo.get_active_session()
            
            if not active_session:
                raise HTTPException(
                    status_code=400,
                    detail="没有活跃的交易会话，请先创建会话"
                )
            
            session_id = active_session.id
            initial_capital = float(active_session.initial_capital) if active_session.initial_capital else 10000.0
        else:
            # 验证会话存在
            session_repo = TradingSessionRepository(db)
            session = session_repo.get_by_id(session_id)
            
            if not session:
                raise HTTPException(
                    status_code=404,
                    detail=f"会话 {session_id} 不存在"
                )
            
            if session.status != 'running':
                raise HTTPException(
                    status_code=400,
                    detail=f"会话 {session_id} 未运行（状态: {session.status}）"
                )
            
            initial_capital = float(session.initial_capital) if session.initial_capital else 10000.0
        
        # 默认交易对
        if symbols is None:
            symbols = ["BTC/USDT:USDT"]
        
        # 启动 Agent
        agent_service = get_agent_service()
        result = agent_service.start_agent(
            session_id=session_id,
            decision_interval=decision_interval,
            symbols=symbols,
            initial_capital=initial_capital,
            risk_params=risk_params
        )
        
        return {
            "success": True,
            "message": "交易代理已启动",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"启动 Agent 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动 Agent 失败: {str(e)}")


@router.post("/stop")
async def stop_agent(
    session_id: Optional[int] = Body(None, description="会话 ID，不提供则停止当前活跃会话的 Agent"),
    db: Session = Depends(get_db)
):
    """
    停止交易代理
    
    停止指定会话或当前活跃会话的交易代理。
    """
    try:
        # 如果未指定 session_id，获取当前活跃会话
        if session_id is None:
            session_repo = TradingSessionRepository(db)
            active_session = session_repo.get_active_session()
            
            if not active_session:
                raise HTTPException(
                    status_code=400,
                    detail="没有活跃的交易会话"
                )
            
            session_id = active_session.id
        
        # 停止 Agent
        agent_service = get_agent_service()
        result = agent_service.stop_agent(session_id)
        
        return {
            "success": True,
            "message": "交易代理已停止",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"停止 Agent 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"停止 Agent 失败: {str(e)}")


@router.get("/status")
async def get_agent_status(
    session_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取 Agent 状态
    
    返回指定会话或当前活跃会话的 Agent 运行状态。
    """
    try:
        # 如果未指定 session_id，获取当前活跃会话
        if session_id is None:
            session_repo = TradingSessionRepository(db)
            active_session = session_repo.get_active_session()
            
            if not active_session:
                return {
                    "success": True,
                    "data": None,
                    "message": "没有活跃的交易会话"
                }
            
            session_id = active_session.id
        
        # 获取 Agent 状态
        agent_service = get_agent_service()
        status = agent_service.get_agent_status(session_id)
        
        if status is None:
            return {
                "success": True,
                "data": None,
                "message": f"Session {session_id} 的 Agent 未运行"
            }
        
        return {
            "success": True,
            "data": status
        }
        
    except Exception as e:
        logger.error(f"获取 Agent 状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取 Agent 状态失败: {str(e)}")


@router.get("/list")
async def list_running_agents():
    """
    列出所有运行中的 Agent
    
    返回所有当前正在运行的交易代理列表。
    """
    try:
        agent_service = get_agent_service()
        agents = agent_service.list_running_agents()
        
        return {
            "success": True,
            "data": agents,
            "count": len(agents)
        }
        
    except Exception as e:
        logger.error(f"列出 Agent 失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"列出 Agent 失败: {str(e)}")


@router.patch("/config")
async def update_agent_config(
    session_id: Optional[int] = Body(None, description="会话 ID"),
    decision_interval: Optional[int] = Body(None, ge=10, le=3600, description="新的决策间隔（秒）"),
    symbols: Optional[List[str]] = Body(None, description="新的交易对列表"),
    risk_params: Optional[Dict[str, Any]] = Body(None, description="新的风险参数"),
    db: Session = Depends(get_db)
):
    """
    更新 Agent 配置
    
    动态更新运行中的 Agent 配置，无需重启。
    """
    try:
        # 如果未指定 session_id，获取当前活跃会话
        if session_id is None:
            session_repo = TradingSessionRepository(db)
            active_session = session_repo.get_active_session()
            
            if not active_session:
                raise HTTPException(
                    status_code=400,
                    detail="没有活跃的交易会话"
                )
            
            session_id = active_session.id
        
        # 更新配置
        agent_service = get_agent_service()
        result = agent_service.update_config(
            session_id=session_id,
            decision_interval=decision_interval,
            symbols=symbols,
            risk_params=risk_params
        )
        
        return {
            "success": True,
            "message": "Agent 配置已更新",
            "data": result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新 Agent 配置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"更新 Agent 配置失败: {str(e)}")

