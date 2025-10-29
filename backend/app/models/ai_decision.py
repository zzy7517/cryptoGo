"""
AI 决策模型
定义 AI 决策记录的数据结构，保存 AI 分析和决策结果
创建时间: 2025-10-27
"""
from sqlalchemy import Column, BigInteger, String, Numeric, Boolean, Text, DateTime, Index, CheckConstraint, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.sql import func

from app.core.database import Base


class AIDecision(Base):
    """AI 决策记录"""
    
    __tablename__ = "ai_decisions"
    
    # 主键
    id = Column(BigInteger, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # 关联会话
    session_id = Column(BigInteger, ForeignKey('trading_sessions.id', ondelete='CASCADE'), comment="所属交易会话ID")
    
    # 决策信息
    symbols = Column(ARRAY(String), comment="分析的币种列表")
    decision_type = Column(String(20), comment="决策类型: buy, sell, hold, rebalance, close")
    confidence = Column(Numeric(5, 4), comment="置信度 (0-1)")
    
    # AI 输入/输出
    prompt_data = Column(JSONB, comment="给AI的完整prompt数据（JSON格式）")
    ai_response = Column(Text, comment="AI的原始回复")
    reasoning = Column(Text, comment="AI的推理过程")
    
    # 建议的交易参数
    suggested_actions = Column(JSONB, comment="建议的具体操作（JSON格式）")
    
    # 执行情况
    executed = Column(Boolean, default=False, comment="是否已执行")
    execution_result = Column(JSONB, comment="执行结果（JSON格式）")
    
    # 约束和索引
    __table_args__ = (
        CheckConstraint("decision_type IN ('buy', 'sell', 'hold', 'rebalance', 'close')", name='check_decision_type'),
        Index('idx_decision_session', 'session_id'),
        Index('idx_decision_created_at', 'created_at'),
        Index('idx_decision_executed', 'executed'),
    )
    
    def __repr__(self):
        return f"<AIDecision {self.decision_type} symbols={self.symbols} confidence={self.confidence}>"

