"""
持仓模型
定义持仓记录的数据结构，包含持仓详情、盈亏和风控信息
创建时间: 2025-10-27
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Integer, DateTime, Interval, Index, CheckConstraint, ForeignKey
from sqlalchemy.sql import func

from ..utils.database import Base


class Position(Base):
    """持仓记录"""
    
    __tablename__ = "positions"
    
    # 主键
    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # 关联会话
    session_id = Column(BigInteger, ForeignKey('trading_sessions.id', ondelete='CASCADE'), comment="所属交易会话ID")
    
    # 基本信息
    symbol = Column(String(20), nullable=False, comment="交易对符号") # 交易对，如 BTC/USDT:USDT
    side = Column(String(10), nullable=False, comment="持仓方向: long, short") # 做多，做空
    status = Column(String(20), default="active", comment="状态: active, closed") # 活跃，已平仓
    
    # 持仓详情
    quantity = Column(Numeric(20, 8), nullable=False, comment="持仓数量")
    entry_price = Column(Numeric(20, 4), nullable=False, comment="入场价格")
    current_price = Column(Numeric(20, 4), comment="当前价格")
    liquidation_price = Column(Numeric(20, 4), comment="强平价格")
    leverage = Column(Integer, default=1, comment="杠杆倍数")
    margin = Column(Numeric(20, 4), comment="保证金金额")
    
    # 时间信息
    entry_time = Column(DateTime(timezone=True), comment="开仓时间")
    exit_time = Column(DateTime(timezone=True), comment="平仓时间")
    holding_duration = Column(Interval, comment="持仓时长")
    
    # 盈亏
    unrealized_pnl = Column(Numeric(20, 4), comment="未实现盈亏")
    realized_pnl = Column(Numeric(20, 4), comment="已实现盈亏")
    
    # 风控
    stop_loss = Column(Numeric(20, 4), comment="止损价")
    take_profit = Column(Numeric(20, 4), comment="止盈价")
    
    # 关联信息
    entry_order_id = Column(BigInteger, comment="入场订单ID")
    exit_order_id = Column(BigInteger, comment="出场订单ID")
    ai_decision_id = Column(BigInteger, comment="关联的AI决策ID")
    
    # 约束和索引
    __table_args__ = (
        CheckConstraint("side IN ('long', 'short')", name='check_position_side'),
        CheckConstraint("status IN ('active', 'closed')", name='check_position_status'),
        Index('idx_position_session', 'session_id'),
        Index('idx_position_symbol_status', 'symbol', 'status'),
        Index('idx_position_created_at', 'created_at'),
        Index('idx_position_status', 'status'),
    )
    
    def __repr__(self):
        return f"<Position {self.side.upper()} {self.symbol} qty={self.quantity} @ {self.entry_price}>"

