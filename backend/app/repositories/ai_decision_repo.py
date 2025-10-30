"""
AI 决策 Repository
管理 AI 交易决策的数据访问层，记录和查询基于会话的 AI 决策
修改时间: 2025-10-29 (添加会话支持)
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.ai_decision import AIDecision
from app.repositories.base import BaseRepository
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AIDecisionRepository(BaseRepository[AIDecision]):
    """AI 决策数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(AIDecision, db)
    
    def save_decision(
        self,
        session_id: int,
        symbols: List[str],
        decision_type: str,
        confidence: float,
        prompt_data: Dict[str, Any],
        ai_response: str,
        reasoning: Optional[str] = None,
        suggested_actions: Optional[List[Dict]] = None
    ) -> AIDecision:
        """
        保存 AI 决策
        
        Args:
            session_id: 所属会话 ID
            symbols: 分析的币种列表
            decision_type: 决策类型 (buy, sell, hold, rebalance)
            confidence: 置信度 0-1
            prompt_data: 完整的 prompt 数据
            ai_response: AI 的原始回复
            reasoning: AI 的推理过程
            suggested_actions: 建议的具体操作
            
        Returns:
            创建的 AIDecision 实例
        """
        try:
            decision = self.create(
                session_id=session_id,
                symbols=symbols,
                decision_type=decision_type,
                confidence=confidence,
                prompt_data=prompt_data,
                ai_response=ai_response,
                reasoning=reasoning,
                suggested_actions=suggested_actions or []
            )
            
            logger.info(
                "AI 决策已保存",
                decision_id=decision.id,
                session_id=session_id,
                decision_type=decision_type,
                symbols=symbols,
                confidence=confidence
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"保存 AI 决策失败: {str(e)}")
            raise
    
    def get_by_session(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[AIDecision]:
        """
        获取指定会话的所有决策
        
        Args:
            session_id: 会话 ID
            limit: 返回数量
            
        Returns:
            决策列表
        """
        return self.db.query(AIDecision)\
            .filter(AIDecision.session_id == session_id)\
            .order_by(desc(AIDecision.created_at))\
            .limit(limit)\
            .all()

