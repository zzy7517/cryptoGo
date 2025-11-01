"""
交易会话服务 - 管理交易会话的生命周期
提供会话的创建、结束、统计、查询等完整业务逻辑
创建时间: 2025-10-29
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from ..repositories.trading_session_repo import TradingSessionRepository
from ..repositories.trade_repo import TradeRepository
from ..repositories.ai_decision_repo import AIDecisionRepository
from ..models.trading_session import TradingSession
from .account_service import AccountService
from ..utils.logging import get_logger
from ..utils.exceptions import BusinessException

logger = get_logger(__name__)


class TradingSessionService:
    """交易会话服务"""

    def __init__(self, db: Session):
        self.db = db
        self.session_repo = TradingSessionRepository(db)
        self.trade_repo = TradeRepository(db)
        self.decision_repo = AIDecisionRepository(db)
        self.account_service = AccountService.get_instance()
    
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
        return self.session_repo.get_active_session()
    
    def get_session_details(self, session_id: int) -> Dict[str, Any]:
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise BusinessException(
                f"会话 {session_id} 不存在",
                error_code="SESSION_NOT_FOUND"
            )

        # 从交易所API获取实时持仓信息
        try:
            positions = self.account_service.get_positions()
            active_positions = [p for p in positions if float(p.get('contracts', 0)) != 0]
        except Exception as e:
            logger.warning(f"获取持仓信息失败: {str(e)}，返回空列表")
            positions = []
            active_positions = []

        # 获取交易
        trades = self.trade_repo.get_by_session(session_id)

        # 获取 AI 决策
        decisions = self.decision_repo.get_by_session(session_id)

        # 计算 Hold Times（持仓时间占比）
        hold_times = self._calculate_hold_times(session, trades)

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
                    "symbol": p.get('symbol'),
                    "side": p.get('side'),
                    "contracts": float(p.get('contracts', 0)),
                    "contractSize": float(p.get('contractSize', 0)),
                    "entryPrice": float(p.get('entryPrice', 0)),
                    "markPrice": float(p.get('markPrice', 0)),
                    "liquidationPrice": float(p.get('liquidationPrice', 0)),
                    "leverage": float(p.get('leverage', 0)),
                    "unrealizedPnl": float(p.get('unrealizedPnl', 0)),
                    "percentage": float(p.get('percentage', 0)),
                    "notional": float(p.get('notional', 0)),
                    "collateral": float(p.get('collateral', 0)),
                    "marginMode": p.get('marginMode'),
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
                    "order_type": t.order_type,
                    "created_at": t.created_at.isoformat() if t.created_at else None,
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
            },
            "hold_times": hold_times
        }
    
    def get_session_list(
        self,
        status: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
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
        # 交易统计
        trade_stats = self.trade_repo.get_session_statistics(session_id)

        return {
            "total_trades": trade_stats["total_trades"],
            "winning_trades": trade_stats["winning_trades"],
            "losing_trades": trade_stats["losing_trades"],
            "total_pnl": trade_stats["total_pnl"]
        }

    def _calculate_hold_times(self, session: TradingSession, trades: List) -> Dict[str, float]:
        """
        计算持仓时间占比

        Args:
            session: 交易会话
            trades: 交易记录列表

        Returns:
            {
                "long_pct": 做多时间占比,
                "short_pct": 做空时间占比,
                "flat_pct": 空仓时间占比
            }
        """
        # 计算会话总时长
        session_start = session.created_at
        session_end = session.ended_at if session.ended_at else datetime.now(timezone.utc)

        # 确保时区一致
        if session_start.tzinfo is None:
            session_start = session_start.replace(tzinfo=timezone.utc)
        if session_end.tzinfo is None:
            session_end = session_end.replace(tzinfo=timezone.utc)

        total_duration = (session_end - session_start).total_seconds()

        if total_duration <= 0:
            return {
                "long_pct": 0.0,
                "short_pct": 0.0,
                "flat_pct": 100.0
            }

        # 统计各状态的持续时间
        long_duration = 0.0
        short_duration = 0.0

        for trade in trades:
            if not trade.entry_time or not trade.exit_time:
                continue

            # 确保时区一致
            entry_time = trade.entry_time
            exit_time = trade.exit_time

            if entry_time.tzinfo is None:
                entry_time = entry_time.replace(tzinfo=timezone.utc)
            if exit_time.tzinfo is None:
                exit_time = exit_time.replace(tzinfo=timezone.utc)

            # 计算该交易的持续时间
            duration = (exit_time - entry_time).total_seconds()

            if trade.side == 'long':
                long_duration += duration
            elif trade.side == 'short':
                short_duration += duration

        # 计算百分比
        long_pct = (long_duration / total_duration * 100) if total_duration > 0 else 0
        short_pct = (short_duration / total_duration * 100) if total_duration > 0 else 0
        flat_pct = 100 - long_pct - short_pct

        # 确保百分比不为负数（可能因为重叠持仓）
        flat_pct = max(0, flat_pct)

        return {
            "long_pct": round(long_pct, 1),
            "short_pct": round(short_pct, 1),
            "flat_pct": round(flat_pct, 1)
        }

