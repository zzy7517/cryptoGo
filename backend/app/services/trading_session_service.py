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
from app.repositories.account_snapshot_repo import AccountSnapshotRepository
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
        self.snapshot_repo = AccountSnapshotRepository(db)
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
                f"已存在活跃会话 (ID: {active_session.id})，请先结束当前会话",
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
        
        # 创建初始快照
        if initial_capital:
            self.snapshot_repo.create_snapshot(
                session_id=session.id,
                total_value=Decimal(str(initial_capital)),
                available_cash=Decimal(str(initial_capital)),
                total_pnl=Decimal(0),
                total_return_pct=Decimal(0)
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
        
        # 获取最新快照
        latest_snapshot = self.snapshot_repo.get_latest(session_id)
        final_capital = float(latest_snapshot.total_value) if latest_snapshot else session.initial_capital
        
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
        
        # 获取快照
        snapshots = self.snapshot_repo.get_by_session(session_id, limit=10)
        
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
                "win_rate": float(session.win_rate) if session.win_rate else None,
                "config": session.config,
                "notes": session.notes
            },
            "statistics": {
                "active_positions_count": len(active_positions),
                "total_positions_count": len(positions),
                "total_trades_count": len(trades),
                "total_decisions_count": len(decisions)
            },
            "recent_snapshots": [
                {
                    "timestamp": s.created_at.isoformat(),
                    "total_value": float(s.total_value),
                    "total_pnl": float(s.total_pnl) if s.total_pnl else 0
                }
                for s in snapshots
            ]
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
                "total_trades": s.total_trades,
                "win_rate": float(s.win_rate) if s.win_rate else None
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
        
        # AI 决策统计
        decisions = self.decision_repo.get_by_session(session_id, limit=10000)
        avg_confidence = (
            sum([float(d.confidence) for d in decisions if d.confidence]) / len(decisions)
        ) if decisions else 0
        
        return {
            "total_trades": trade_stats["total_trades"],
            "winning_trades": trade_stats["winning_trades"],
            "losing_trades": trade_stats["losing_trades"],
            "win_rate": trade_stats["win_rate"],
            "total_pnl": trade_stats["total_pnl"],
            "biggest_win": trade_stats["biggest_win"],
            "biggest_loss": trade_stats["biggest_loss"],
            "avg_leverage": trade_stats["avg_leverage"],
            "avg_confidence": Decimal(str(avg_confidence))
        }
    
    def create_snapshot(
        self,
        session_id: int,
        total_value: float,
        available_cash: float,
        positions_summary: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        创建账户快照
        
        Args:
            session_id: 会话 ID
            total_value: 总价值
            available_cash: 可用现金
            positions_summary: 持仓汇总
        """
        session = self.session_repo.get_by_id(session_id)
        if not session:
            raise BusinessException(
                f"会话 {session_id} 不存在",
                error_code="SESSION_NOT_FOUND"
            )
        
        # 计算盈亏
        if session.initial_capital:
            total_pnl = Decimal(str(total_value)) - Decimal(str(session.initial_capital))
            total_return_pct = (total_pnl / Decimal(str(session.initial_capital))) * 100
        else:
            total_pnl = Decimal(0)
            total_return_pct = Decimal(0)
        
        self.snapshot_repo.create_snapshot(
            session_id=session_id,
            total_value=Decimal(str(total_value)),
            available_cash=Decimal(str(available_cash)),
            total_pnl=total_pnl,
            total_return_pct=total_return_pct,
            positions_summary=positions_summary
        )

