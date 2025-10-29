"""
账户快照 Repository
管理账户快照的数据访问层，定期记录账户状态和绩效指标
创建时间: 2025-10-29
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal

from app.models.account_snapshot import AccountSnapshot
from app.repositories.base import BaseRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class AccountSnapshotRepository(BaseRepository[AccountSnapshot]):
    """账户快照数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(AccountSnapshot, db)
    
    def create_snapshot(
        self,
        session_id: int,
        total_value: Decimal,
        available_cash: Decimal,
        total_pnl: Optional[Decimal] = None,
        total_return_pct: Optional[Decimal] = None,
        sharpe_ratio: Optional[Decimal] = None,
        max_drawdown: Optional[Decimal] = None,
        positions_summary: Optional[Dict[str, Any]] = None,
        ai_decision_id: Optional[int] = None
    ) -> AccountSnapshot:
        """
        创建账户快照
        
        Args:
            session_id: 所属会话 ID
            total_value: 账户总价值
            available_cash: 可用现金
            total_pnl: 总盈亏
            total_return_pct: 总收益率
            sharpe_ratio: 夏普比率
            max_drawdown: 最大回撤
            positions_summary: 持仓汇总
            ai_decision_id: 关联的 AI 决策 ID
            
        Returns:
            创建的 AccountSnapshot 实例
        """
        try:
            snapshot = self.create(
                session_id=session_id,
                total_value=total_value,
                available_cash=available_cash,
                total_pnl=total_pnl,
                total_return_pct=total_return_pct,
                sharpe_ratio=sharpe_ratio,
                max_drawdown=max_drawdown,
                positions_summary=positions_summary or {},
                ai_decision_id=ai_decision_id
            )
            
            logger.info(
                "账户快照已创建",
                snapshot_id=snapshot.id,
                session_id=session_id,
                total_value=total_value,
                total_pnl=total_pnl
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"创建账户快照失败: {str(e)}")
            raise
    
    def get_by_session(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[AccountSnapshot]:
        """
        获取指定会话的所有快照
        
        Args:
            session_id: 会话 ID
            limit: 返回数量
            
        Returns:
            快照列表
        """
        return self.db.query(AccountSnapshot)\
            .filter(AccountSnapshot.session_id == session_id)\
            .order_by(desc(AccountSnapshot.created_at))\
            .limit(limit)\
            .all()
    
    def get_latest(self, session_id: int) -> Optional[AccountSnapshot]:
        """
        获取指定会话的最新快照
        
        Args:
            session_id: 会话 ID
            
        Returns:
            最新快照或 None
        """
        return self.db.query(AccountSnapshot)\
            .filter(AccountSnapshot.session_id == session_id)\
            .order_by(desc(AccountSnapshot.created_at))\
            .first()
    
    def get_snapshots_for_chart(
        self,
        session_id: int,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        获取用于绘制图表的快照数据
        
        Args:
            session_id: 会话 ID
            limit: 返回数量
            
        Returns:
            简化的快照数据列表
        """
        snapshots = self.get_by_session(session_id, limit)
        
        return [
            {
                "timestamp": snapshot.created_at.isoformat(),
                "total_value": float(snapshot.total_value),
                "total_pnl": float(snapshot.total_pnl) if snapshot.total_pnl else 0,
                "total_return_pct": float(snapshot.total_return_pct) if snapshot.total_return_pct else 0,
                "max_drawdown": float(snapshot.max_drawdown) if snapshot.max_drawdown else 0
            }
            for snapshot in reversed(snapshots)  # 按时间正序
        ]
    
    def calculate_performance_metrics(
        self,
        session_id: int
    ) -> Dict[str, Any]:
        """
        计算会话的绩效指标
        
        Args:
            session_id: 会话 ID
            
        Returns:
            绩效指标字典
        """
        snapshots = self.get_by_session(session_id, limit=10000)
        
        if not snapshots:
            return {
                "max_drawdown": 0,
                "sharpe_ratio": 0,
                "total_return": 0,
                "volatility": 0
            }
        
        # 计算最大回撤
        returns = [float(s.total_return_pct or 0) for s in snapshots]
        max_return = 0
        max_drawdown = 0
        
        for ret in returns:
            max_return = max(max_return, ret)
            drawdown = max_return - ret
            max_drawdown = max(max_drawdown, drawdown)
        
        # 获取最新的夏普比率
        latest = snapshots[0]  # 已经按时间倒序
        sharpe_ratio = float(latest.sharpe_ratio) if latest.sharpe_ratio else 0
        
        # 总收益
        total_return = float(latest.total_return_pct) if latest.total_return_pct else 0
        
        # 波动率（简化计算）
        if len(returns) > 1:
            import statistics
            volatility = statistics.stdev(returns)
        else:
            volatility = 0
        
        return {
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio,
            "total_return": total_return,
            "volatility": volatility
        }
