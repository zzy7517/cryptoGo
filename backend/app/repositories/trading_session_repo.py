"""
交易会话 Repository
管理交易会话的数据访问层，处理会话的 CRUD 操作和状态管理
创建时间: 2025-10-27
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal

from app.models.trading_session import TradingSession
from app.repositories.base import BaseRepository


class TradingSessionRepository(BaseRepository[TradingSession]):
    """交易会话数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(TradingSession, db)
    
    def get_active_session(self) -> Optional[TradingSession]:
        """
        获取当前活跃的会话
        
        Returns:
            Optional[TradingSession]: 当前活跃的会话，如果没有则返回 None
        """
        return self.db.query(TradingSession).filter(
            TradingSession.status == 'running'
        ).order_by(desc(TradingSession.created_at)).first()
    
    def get_latest_sessions(self, limit: int = 10) -> List[TradingSession]:
        """
        获取最近的会话列表
        
        Args:
            limit: 返回的会话数量，默认 10
            
        Returns:
            List[TradingSession]: 会话列表
        """
        return self.db.query(TradingSession).order_by(
            desc(TradingSession.created_at)
        ).limit(limit).all()
    
    def get_by_status(self, status: str) -> List[TradingSession]:
        """
        根据状态获取会话列表
        
        Args:
            status: 会话状态 (running, stopped, crashed, completed)
            
        Returns:
            List[TradingSession]: 会话列表
        """
        return self.db.query(TradingSession).filter(
            TradingSession.status == status
        ).order_by(desc(TradingSession.created_at)).all()
    
    def create_session(
        self,
        session_name: Optional[str] = None,
        initial_capital: Optional[float] = None,
        config: Optional[dict] = None
    ) -> TradingSession:
        """
        创建新的交易会话
        
        Args:
            session_name: 会话名称（可选）
            initial_capital: 初始资金
            config: 配置信息
            
        Returns:
            TradingSession: 新创建的会话
        """
        initial_cap = Decimal(str(initial_capital)) if initial_capital else None
        return self.create(
            session_name=session_name,
            initial_capital=initial_cap,
            current_capital=initial_cap,  # 初始时 current_capital = initial_capital
            config=config,
            status='running'
        )
    
    def end_session(
        self,
        session_id: int,
        status: str = 'completed',
        final_capital: Optional[float] = None,
        total_pnl: Optional[float] = None
    ) -> Optional[TradingSession]:
        """
        结束交易会话
        
        Args:
            session_id: 会话 ID
            status: 最终状态 (stopped, crashed, completed)
            final_capital: 最终资金
            total_pnl: 总盈亏
            
        Returns:
            Optional[TradingSession]: 更新后的会话
        """
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
        """
        更新会话统计信息
        
        Args:
            session_id: 会话 ID
            **stats: 统计数据字段
            
        Returns:
            Optional[TradingSession]: 更新后的会话
        """
        return self.update(session_id, **stats)

