"""
交易会话服务 - 管理交易会话的生命周期
提供会话的创建、结束、统计、查询等完整业务逻辑
创建时间: 2025-10-29
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from decimal import Decimal

from app.repositories.trading_session_repo import TradingSessionRepository
from app.repositories.position_repo import PositionRepository
from app.repositories.trade_repo import TradeRepository
from app.repositories.ai_decision_repo import AIDecisionRepository
from app.models.trading_session import TradingSession
from app.utils.logging import get_logger
from app.utils.exceptions import BusinessException

logger = get_logger(__name__)


class TradingSessionService:
    """交易会话服务"""
    
    def __init__(self, db: Session):
        self.db = db
        self.session_repo = TradingSessionRepository(db)
        self.position_repo = PositionRepository(db)
        self.trade_repo = TradeRepository(db)
        self.decision_repo = AIDecisionRepository(db)
    
    def start_session(
        self,
        session_name: Optional[str] = None,
        initial_capital: Optional[float] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> TradingSession:
        """
        开始新的交易会话
        
        Args:
            session_name: 会话名称
            initial_capital: 初始资金
            config: 配置信息
            
        Returns:
            创建的交易会话
            
        Raises:
            BusinessException: 如果已有活跃会话
        """
        # 检查是否已有活跃会话
        active_session = self.session_repo.get_active_session()
        if active_session:
            raise BusinessException(
                f"已存在活跃会话 (ID: {active_session.id}, 名称: {active_session.session_name})，请先结束该会话",
                error_code="ACTIVE_SESSION_EXISTS"
            )
        
        # 生成会话名称
        if not session_name:
            session_name = f"Trading Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 创建会话
        session = self.session_repo.create_session(
            session_name=session_name,
            initial_capital=initial_capital,
            config=config or {}
        )
        
        logger.info(
            "交易会话已开始",
            session_id=session.id,
            session_name=session_name,
            initial_capital=initial_capital
        )

        return session
    
    def end_session(
        self,
        session_id: Optional[int] = None,
        status: str = 'completed',
        notes: Optional[str] = None
    ) -> TradingSession:
        """
        结束交易会话
        
        Args:
            session_id: 会话 ID，如果不提供则结束当前活跃会话
            status: 结束状态 (completed, stopped, crashed)
            notes: 备注信息
            
        Returns:
            更新后的交易会话
            
        Raises:
            BusinessException: 如果会话不存在或已结束
        """
        # 如果未提供 session_id，获取当前活跃会话
        if not session_id:
            session = self.session_repo.get_active_session()
            if not session:
                raise BusinessException(
                    "没有活跃的交易会话",
                    error_code="NO_ACTIVE_SESSION"
                )
            session_id = session.id
        else:
            session = self.session_repo.get_by_id(session_id)
            if not session:
                raise BusinessException(
                    f"会话 {session_id} 不存在",
                    error_code="SESSION_NOT_FOUND"
                )
        
        # 检查会话状态
        if session.status != 'running':
            raise BusinessException(
                f"会话 {session_id} 已结束 (状态: {session.status})",
                error_code="SESSION_ALREADY_ENDED"
            )
        
        # 计算最终统计
        statistics = self._calculate_session_statistics(session_id)

        # 使用初始资金作为最终资金（如果没有其他数据源）
        final_capital = session.initial_capital

        # 更新会话
        updated_session = self.session_repo.end_session(
            session_id=session_id,
            status=status,
            final_capital=final_capital,
            total_pnl=statistics.get('total_pnl')
        )
        
        # 更新统计信息
        self.session_repo.update_statistics(
            session_id=session_id,
            **statistics
        )
        
        # 更新备注
        if notes:
            self.session_repo.update(session_id, notes=notes)
        
        logger.info(
            "交易会话已结束",
            session_id=session_id,
            status=status,
            final_capital=final_capital,
            total_pnl=statistics.get('total_pnl')
        )
        
        return updated_session
    
    def get_active_session(self) -> Optional[TradingSession]:
        """
        获取当前活跃会话
        
        Returns:
            当前活跃会话或 None
        """
        return self.session_repo.get_active_session()
    
    def get_session_details(self, session_id: int) -> Dict[str, Any]:
        """
        获取会话详细信息
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话详细信息字典
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise BusinessException(
                f"会话 {session_id} 不存在",
                error_code="SESSION_NOT_FOUND"
            )
        
        # 获取持仓
        positions = self.position_repo.get_by_session(session_id)
        active_positions = [p for p in positions if p.status == 'active']
        
        # 获取交易
        trades = self.trade_repo.get_by_session(session_id)
        
        # 获取 AI 决策
        decisions = self.decision_repo.get_by_session(session_id)

        return {
            "session": {
                "id": session.id,
                "session_name": session.session_name,
                "status": session.status,
                "created_at": session.created_at.isoformat(),
                "ended_at": session.ended_at.isoformat() if session.ended_at else None,
                "initial_capital": float(session.initial_capital) if session.initial_capital else None,
                "final_capital": float(session.final_capital) if session.final_capital else None,
                "total_pnl": float(session.total_pnl) if session.total_pnl else None,
                "total_return_pct": float(session.total_return_pct) if session.total_return_pct else None,
                "total_trades": session.total_trades,
                "winning_trades": session.winning_trades,
                "losing_trades": session.losing_trades,
                "config": session.config,
                "notes": session.notes
            },
            "positions": [
                {
                    "id": p.id,
                    "symbol": p.symbol,
                    "side": p.side,
                    "quantity": float(p.quantity) if p.quantity else 0,
                    "entry_price": float(p.entry_price) if p.entry_price else 0,
                    "current_price": float(p.current_price) if p.current_price else 0,
                    "unrealized_pnl": float(p.unrealized_pnl) if p.unrealized_pnl else 0,
                    "unrealized_pnl_pct": float(p.unrealized_pnl) / float(p.entry_price * p.quantity) * 100 if p.entry_price and p.quantity and float(p.entry_price * p.quantity) != 0 else 0,
                    "status": p.status,
                    "leverage": p.leverage,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                }
                for p in positions
            ],
            "trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "side": t.side,
                    "quantity": float(t.quantity) if t.quantity else 0,
                    "price": float(t.price) if t.price else 0,
                    "status": t.status,
                    "order_type": t.order_type,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
                    "executed_at": t.executed_at.isoformat() if t.executed_at else None
                }
                for t in trades
            ],
            "decisions": [
                {
                    "id": d.id,
                    "decision_type": d.decision_type,
                    "symbols": d.symbols,
                    "confidence": float(d.confidence) if d.confidence else None,
                    "reasoning": d.reasoning,
                    "created_at": d.created_at.isoformat() if d.created_at else None
                }
                for d in decisions
            ],
            "statistics": {
                "active_positions_count": len(active_positions),
                "total_positions_count": len(positions),
                "total_trades_count": len(trades),
                "total_decisions_count": len(decisions)
            }
        }
    
    def get_session_list(
        self,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        获取会话列表
        
        Args:
            status: 过滤状态
            limit: 返回数量
            
        Returns:
            会话列表
        """
        if status:
            sessions = self.session_repo.get_by_status(status)[:limit]
        else:
            sessions = self.session_repo.get_latest_sessions(limit)
        
        return [
            {
                "id": s.id,
                "session_name": s.session_name,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
                "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                "initial_capital": float(s.initial_capital) if s.initial_capital else None,
                "final_capital": float(s.final_capital) if s.final_capital else None,
                "total_pnl": float(s.total_pnl) if s.total_pnl else None,
                "total_return_pct": float(s.total_return_pct) if s.total_return_pct else None,
                "total_trades": s.total_trades
            }
            for s in sessions
        ]
    
    def _calculate_session_statistics(self, session_id: int) -> Dict[str, Any]:
        """
        计算会话统计数据
        
        Args:
            session_id: 会话 ID
            
        Returns:
            统计数据字典
        """
        # 交易统计
        trade_stats = self.trade_repo.get_session_statistics(session_id)
        
        # 持仓统计
        positions = self.position_repo.get_by_session(session_id, limit=10000)
        total_pnl = self.position_repo.get_total_pnl(session_id)
        
        return {
            "total_trades": trade_stats["total_trades"],
            "winning_trades": trade_stats["winning_trades"],
            "losing_trades": trade_stats["losing_trades"],
            "total_pnl": trade_stats["total_pnl"]
        }

