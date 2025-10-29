"""
交易记录模型
定义交易记录的数据结构，记录每笔交易的详细信息
创建时间: 2025-10-27
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Integer, DateTime, Interval, Index, CheckConstraint, ForeignKey
from sqlalchemy.sql import func

from app.core.database import Base


class Trade(Base):
    """交易记录"""
    
    __tablename__ = "trades"
    
    # 主键
    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联会话
    session_id = Column(BigInteger, ForeignKey('trading_sessions.id', ondelete='CASCADE'), comment="所属交易会话ID")
    
    # 交易信息
    symbol = Column(String(20), nullable=False, comment="交易对符号")
    side = Column(String(10), nullable=False, comment="方向: buy, sell, long, short")
    order_type = Column(String(20), comment="订单类型: market, limit, stop, stop_limit")
    
    # 数量和价格
    quantity = Column(Numeric(20, 8), nullable=False, comment="交易数量")
    price = Column(Numeric(20, 4), nullable=False, comment="成交价格")
    total_value = Column(Numeric(20, 4), nullable=False, comment="总价值")
    leverage = Column(Integer, default=1, comment="使用的杠杆倍数")
    
    # 名义价值（用于杠杆交易）
    notional_entry = Column(Numeric(20, 4), comment="名义入场价值")
    notional_exit = Column(Numeric(20, 4), comment="名义出场价值")
    
    # 时间信息
    entry_time = Column(DateTime(timezone=True), comment="开仓时间")
    exit_time = Column(DateTime(timezone=True), comment="平仓时间")
    holding_duration = Column(Interval, comment="持仓时长（仅已平仓交易）")
    
    # 费用
    fee = Column(Numeric(20, 8), comment="手续费")
    fee_currency = Column(String(10), comment="手续费币种")
    
    # 盈亏（仅平仓时）
    pnl = Column(Numeric(20, 4), comment="盈亏金额")
    pnl_pct = Column(Numeric(10, 4), comment="盈亏百分比")
    
    # 关联
    position_id = Column(BigInteger, comment="关联的持仓ID")
    ai_decision_id = Column(BigInteger, comment="关联的AI决策ID")
    exchange_order_id = Column(String(100), comment="交易所订单ID")
    
    # 约束和索引
    __table_args__ = (
        CheckConstraint("side IN ('buy', 'sell', 'long', 'short')", name='check_trade_side'),
        CheckConstraint("order_type IN ('market', 'limit', 'stop', 'stop_limit')", name='check_trade_order_type'),
        Index('idx_trade_session', 'session_id'),
        Index('idx_trade_symbol_created', 'symbol', 'created_at'),
        Index('idx_trade_position_id', 'position_id'),
        Index('idx_trade_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Trade {self.side.upper()} {self.quantity} {self.symbol} @ {self.price}>"

