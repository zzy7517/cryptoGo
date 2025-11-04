"""
交易会话 Repository
管理交易会话的数据访问层，处理会话的 CRUD 操作和状态管理
创建时间: 2025-10-27
更新时间: 2025-11-04 - 添加 JSON 序列化支持（SQLite 兼容）
"""
import json
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal

from ..models.trading_session import TradingSession


class TradingSessionRepository:
    """交易会话数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[TradingSession]:
        return self.db.query(TradingSession).filter(TradingSession.id == id).first()
    
    def update(self, id: int, **kwargs) -> Optional[TradingSession]:
        session = self.get_by_id(id)
        if not session:
            return None
        
        for key, value in kwargs.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def get_active_session(self) -> Optional[TradingSession]:
        return self.db.query(TradingSession).filter(
            TradingSession.status == 'running'
        ).order_by(desc(TradingSession.created_at)).first()
    
    def get_latest_sessions(self, limit: int = 10) -> List[TradingSession]:
        return self.db.query(TradingSession).order_by(
            desc(TradingSession.created_at)
        ).limit(limit).all()
    
    def get_by_status(self, status: str) -> List[TradingSession]:
        return self.db.query(TradingSession).filter(
            TradingSession.status == status
        ).order_by(desc(TradingSession.created_at)).all()
    
    def create_session(
        self,
        session_name: Optional[str] = None,
        initial_capital: Optional[float] = None,
        config: Optional[dict] = None
    ) -> TradingSession:
        initial_cap = Decimal(str(initial_capital)) if initial_capital else None

        # 将 config 字典序列化为 JSON 字符串（SQLite 兼容）
        config_json = json.dumps(config) if config else None

        session = TradingSession(
            session_name=session_name,
            initial_capital=initial_cap,
            current_capital=initial_cap,  # 初始时 current_capital = initial_capital
            config=config_json,
            status='running'
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    def end_session(
        self,
        session_id: int,
        status: str = 'completed',
        final_capital: Optional[float] = None,
        total_pnl: Optional[float] = None
    ) -> Optional[TradingSession]:
        session = self.get_by_id(session_id)
        if not session:
            return None
        
        update_data = {
            'status': status,
            'ended_at': datetime.now()
        }
        
        if final_capital is not None:
            update_data['final_capital'] = Decimal(str(final_capital))
            
        if total_pnl is not None:
            update_data['total_pnl'] = Decimal(str(total_pnl))
            
        if final_capital and session.initial_capital:
            # 将所有值转换为 float 进行计算，然后转回 Decimal
            final_cap_float = float(final_capital) if isinstance(final_capital, Decimal) else final_capital
            initial_cap_float = float(session.initial_capital)
            update_data['total_return_pct'] = Decimal(str(
                (final_cap_float - initial_cap_float) / initial_cap_float * 100
            ))
        
        return self.update(session_id, **update_data)
    
    def update_statistics(
        self,
        session_id: int,
        **stats
    ) -> Optional[TradingSession]:
        return self.update(session_id, **stats)

