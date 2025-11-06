"""
AI 决策模型
定义 AI 决策记录的数据结构，保存 AI 分析和决策结果
创建时间: 2025-10-27
更新时间: 2025-11-04 - 改用 SQLite，移除 PostgreSQL 特定类型
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.sql import func

from ..utils.database import Base


class AIDecision(Base):
    """AI 决策记录"""
    
    __tablename__ = "ai_decisions"
    
    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # 关联会话
    session_id = Column(Integer, ForeignKey('trading_sessions.id', ondelete='CASCADE'), comment="所属交易会话ID")
    
    # 决策信息
    symbols = Column(Text, comment="分析的币种列表（JSON数组格式）")
    decision_type = Column(String(20), comment="决策类型: buy, sell, hold, rebalance, close")
    confidence = Column(Numeric(5, 4), comment="置信度 (0-1)")

    # AI 输入/输出
    prompt_data = Column(Text, comment="给AI的完整prompt数据（JSON格式）")
    ai_response = Column(Text, comment="AI的原始回复")
    reasoning = Column(Text, comment="AI的推理过程")

    # 建议的交易参数
    suggested_actions = Column(Text, comment="建议的具体操作（JSON格式）")

    # 执行情况
    executed = Column(Boolean, default=False, comment="是否已执行")
    execution_result = Column(Text, comment="执行结果（JSON格式）")
    
    # 账户信息（用于资产变化追踪）
    account_balance = Column(Numeric(20, 4), comment="决策时的账户总余额")
    unrealized_pnl = Column(Numeric(20, 4), comment="决策时的浮动盈亏（未实现盈亏）")
    total_asset = Column(Numeric(20, 4), comment="决策时的总资产（余额 + 浮动盈亏）")
    
    # 约束和索引
    __table_args__ = (
        CheckConstraint("decision_type IN ('buy', 'sell', 'hold', 'rebalance', 'close')", name='check_decision_type'),
        Index('idx_decision_session', 'session_id'),
        Index('idx_decision_created_at', 'created_at'),
        Index('idx_decision_executed', 'executed'),
    )
    
    def __repr__(self):
        return f"<AIDecision {self.decision_type} symbols={self.symbols} confidence={self.confidence}>"

