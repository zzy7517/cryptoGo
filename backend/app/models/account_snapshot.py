"""
账户快照模型
定义账户快照的数据结构，定期记录账户状态和绩效指标
创建时间: 2025-10-27
"""
from sqlalchemy import Column, BigInteger, Numeric, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.utils.database import Base


class AccountSnapshot(Base):
    """账户快照 - 定期记录账户状态"""
    
    __tablename__ = "account_snapshots"
    
    # 主键
    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联会话
    session_id = Column(BigInteger, ForeignKey('trading_sessions.id', ondelete='CASCADE'), comment="所属交易会话ID")
    
    # 账户信息
    total_value = Column(Numeric(20, 4), nullable=False, comment="账户总价值")
    available_cash = Column(Numeric(20, 4), nullable=False, comment="可用现金")
    total_pnl = Column(Numeric(20, 4), comment="总盈亏")
    total_return_pct = Column(Numeric(10, 4), comment="总收益率 (%)")
    
    # 风险指标
    sharpe_ratio = Column(Numeric(10, 6), comment="夏普比率")
    max_drawdown = Column(Numeric(10, 4), comment="最大回撤 (%)")
    
    # 持仓汇总
    positions_summary = Column(JSONB, comment="当前所有持仓的快照（JSON格式）")
    
    # 关联
    ai_decision_id = Column(BigInteger, comment="关联的AI决策ID")
    
    # 索引
    __table_args__ = (
        Index('idx_snapshot_session', 'session_id'),
        Index('idx_snapshot_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AccountSnapshot value={self.total_value} return={self.total_return_pct}%>"

