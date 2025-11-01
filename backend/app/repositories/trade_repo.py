"""
交易记录 Repository
管理交易记录的数据访问层，支持基于会话的交易记录管理
创建时间: 2025-10-29
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal
from datetime import datetime

from ..models.trade import Trade
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TradeRepository:
    """交易记录数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[Trade]:
        """根据 ID 获取交易记录"""
        return self.db.query(Trade).filter(Trade.id == id).first()
    
    def create_trade(
        self,
        session_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        price: Decimal,
        total_value: Decimal,
        order_type: str = "market",
        leverage: int = 1,
        fee: Optional[Decimal] = None,
        fee_currency: Optional[str] = None,
        position_id: Optional[int] = None,
        ai_decision_id: Optional[int] = None,
        exchange_order_id: Optional[str] = None
    ) -> Trade:
        """
        创建交易记录
        
        Args:
            session_id: 所属会话 ID
            symbol: 交易对
            side: 方向 (buy, sell, long, short)
            quantity: 数量
            price: 价格
            total_value: 总价值
            order_type: 订单类型
            leverage: 杠杆
            fee: 手续费
            fee_currency: 手续费币种
            position_id: 关联持仓 ID
            ai_decision_id: 关联 AI 决策 ID
            exchange_order_id: 交易所订单 ID
            
        Returns:
            创建的 Trade 实例
        """
        try:
            trade = Trade(
                session_id=session_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                total_value=total_value,
                order_type=order_type,
                leverage=leverage,
                fee=fee,
                fee_currency=fee_currency,
                position_id=position_id,
                ai_decision_id=ai_decision_id,
                exchange_order_id=exchange_order_id,
                entry_time=datetime.now()
            )
            self.db.add(trade)
            self.db.commit()
            self.db.refresh(trade)
            
            logger.info(
                "交易记录已创建",
                trade_id=trade.id,
                session_id=session_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price
            )
            
            return trade
            
        except Exception as e:
            logger.error(f"创建交易记录失败: {str(e)}")
            raise
    
    def get_by_session(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[Trade]:
        return self.db.query(Trade)\
            .filter(Trade.session_id == session_id)\
            .order_by(desc(Trade.created_at))\
            .limit(limit)\
            .all()
    
    def get_by_symbol(
        self,
        session_id: int,
        symbol: str,
        limit: int = 100
    ) -> List[Trade]:
        return self.db.query(Trade)\
            .filter(
                Trade.session_id == session_id,
                Trade.symbol == symbol
            )\
            .order_by(desc(Trade.created_at))\
            .limit(limit)\
            .all()
    
    def get_trades_by_session(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[Trade]:
        return self.get_by_session(session_id, limit)
    
    def get_session_statistics(self, session_id: int) -> dict:
        trades = self.get_by_session(session_id, limit=10000)
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl and t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl and t.pnl < 0])
        
        total_pnl = sum([t.pnl for t in trades if t.pnl]) or Decimal(0)
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "total_pnl": total_pnl
        }

