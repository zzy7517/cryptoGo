"""
交易会话模型
定义交易会话的数据结构，记录每次交易运行实例的完整信息
创建时间: 2025-10-27
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Integer, Boolean, Text, DateTime, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.utils.database import Base


class TradingSession(Base):
    """交易会话 - 记录每次运行实例"""
    
    __tablename__ = "trading_sessions"
    
    # 主键
    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ended_at = Column(DateTime(timezone=True), comment="会话结束时间")
    
    # 基本信息
    session_name = Column(String(100), comment="会话名称（可选）")
    status = Column(String(20), default="running", comment="会话状态")
    
    # 初始状态
    initial_capital = Column(Numeric(20, 4), comment="初始资金")
    
    # 最终统计
    final_capital = Column(Numeric(20, 4), comment="最终资金")
    total_pnl = Column(Numeric(20, 4), comment="总盈亏")
    total_return_pct = Column(Numeric(10, 4), comment="总收益率 (%)")
    
    # 交易统计
    total_trades = Column(Integer, default=0, comment="总交易次数")
    winning_trades = Column(Integer, default=0, comment="盈利交易次数")
    losing_trades = Column(Integer, default=0, comment="亏损交易次数")
    
    # 配置信息
    config = Column(JSONB, comment="运行配置（JSON格式）")
    
    # 备注
    notes = Column(Text, comment="备注信息")
    
    # 约束
    __table_args__ = (
        CheckConstraint("status IN ('running', 'stopped', 'crashed', 'completed')", name='check_session_status'),
        Index('idx_session_status', 'status'),
        Index('idx_session_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<TradingSession {self.id} {self.session_name or ''} status={self.status}>"

