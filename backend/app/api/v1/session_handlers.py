"""
交易会话处理函数
所有会话相关的业务逻辑处理
创建时间: 2025-10-29
"""
from fastapi import HTTPException, Depends, Query, Body
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.utils.database import get_db
from app.services.trading_session_service import TradingSessionService
from app.services.trading_agent_service import get_background_agent_manager
from app.utils.logging import get_logger
from app.utils.exceptions import BusinessException

logger = get_logger(__name__)


async def start_session(
    session_name: Optional[str] = Body(None, description="会话名称"),
    initial_capital: Optional[float] = Body(None, description="初始资金"),
    config: Optional[Dict[str, Any]] = Body(None, description="配置信息"),
    db: Session = Depends(get_db)
):
    """
    开始新的交易会话
    
    创建一个新的交易会话。如果已有活跃会话，则返回错误。
    """
    try:
        service = TradingSessionService(db)
        session = service.start_session(
            session_name=session_name,
            initial_capital=initial_capital,
            config=config
        )
        
        return {
            "success": True,
            "message": "交易会话已开始",
            "data": {
                "session_id": session.id,
                "session_name": session.session_name,
                "status": session.status,
                "initial_capital": float(session.initial_capital) if session.initial_capital else None,
                "created_at": session.created_at.isoformat()
            }
        }
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"开始会话失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"开始会话失败: {str(e)}")


async def end_session(
    session_id: Optional[int] = Body(None, description="会话 ID，不提供则结束当前活跃会话"),
    status: str = Body("completed", description="结束状态: completed, stopped, crashed"),
    notes: Optional[str] = Body(None, description="备注信息"),
    db: Session = Depends(get_db)
):
    """
    结束交易会话
    
    结束指定会话或当前活跃会话，并计算最终统计数据。
    同时自动停止该会话的交易代理（如果正在运行）。
    """
    try:
        service = TradingSessionService(db)
        session = service.end_session(
            session_id=session_id,
            status=status,
            notes=notes
        )
        
        # 自动停止该会话的 Agent（如果正在运行）
        manager = get_background_agent_manager()
        agent_status = manager.get_agent_status(session.id)
        
        if agent_status:
            try:
                manager.stop_background_agent(session.id)
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
        agent_status = manager.get_agent_status(session.id)
        
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


async def create_snapshot(
    session_id: int,
    total_value: float = Body(..., description="账户总价值"),
    available_cash: float = Body(..., description="可用现金"),
    positions_summary: Optional[Dict[str, Any]] = Body(None, description="持仓汇总"),
    db: Session = Depends(get_db)
):
    """
    创建账户快照
    
    记录指定会话的账户状态快照。
    """
    try:
        service = TradingSessionService(db)
        service.create_snapshot(
            session_id=session_id,
            total_value=total_value,
            available_cash=available_cash,
            positions_summary=positions_summary
        )
        
        return {
            "success": True,
            "message": "快照已创建"
        }
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建快照失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"创建快照失败: {str(e)}")

