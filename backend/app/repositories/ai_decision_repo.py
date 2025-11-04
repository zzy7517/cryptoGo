"""
AI 决策 Repository
管理 AI 交易决策的数据访问层，记录和查询基于会话的 AI 决策
修改时间: 2025-10-29 (添加会话支持)
"""
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ..models.ai_decision import AIDecision
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AIDecisionRepository:
    """AI 决策数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[AIDecision]:
        """根据 ID 获取 AI 决策"""
        return self.db.query(AIDecision).filter(AIDecision.id == id).first()
    
    def save_decision(
        self,
        session_id: int,
        symbols: List[str],
        decision_type: str,
        confidence: float,
        prompt_data: Dict[str, Any],
        ai_response: str,
        reasoning: Optional[str] = None,
        suggested_actions: Optional[List[Dict]] = None,
        executed: bool = False,
        account_balance: Optional[float] = None,
        unrealized_pnl: Optional[float] = None,
        total_asset: Optional[float] = None
    ) -> AIDecision:
        try:
            # 序列化 JSON 字段（SQLite 兼容）
            symbols_json = json.dumps(symbols) if symbols else None
            prompt_data_json = json.dumps(prompt_data) if prompt_data else None
            suggested_actions_json = json.dumps(suggested_actions or [])

            decision = AIDecision(
                session_id=session_id,
                symbols=symbols_json,
                decision_type=decision_type,
                confidence=confidence,
                prompt_data=prompt_data_json,
                ai_response=ai_response,
                reasoning=reasoning,
                suggested_actions=suggested_actions_json,
                executed=executed,
                account_balance=account_balance,
                unrealized_pnl=unrealized_pnl,
                total_asset=total_asset
            )
            self.db.add(decision)
            self.db.commit()
            self.db.refresh(decision)
            
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
        return self.db.query(AIDecision)\
            .filter(AIDecision.session_id == session_id)\
            .order_by(desc(AIDecision.created_at))\
            .limit(limit)\
            .all()

