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
    
    def create_closed_trade(
        self,
        session_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        entry_price: Decimal,
        exit_price: Decimal,
        entry_time: datetime,
        exit_time: datetime,
        leverage: int = 1,
        entry_fee: Optional[Decimal] = None,
        exit_fee: Optional[Decimal] = None,
        fee_currency: Optional[str] = None,
        ai_decision_id: Optional[int] = None,
        entry_order_id: Optional[str] = None,
        exit_order_id: Optional[str] = None
    ) -> Trade:
        """
        创建已完成的交易记录（仅在平仓时调用）

        Args:
            session_id: 所属会话 ID
            symbol: 交易对
            side: 方向 (long, short)
            quantity: 数量
            entry_price: 开仓价格
            exit_price: 平仓价格
            entry_time: 开仓时间
            exit_time: 平仓时间
            leverage: 杠杆
            entry_fee: 开仓手续费
            exit_fee: 平仓手续费
            fee_currency: 手续费币种
            ai_decision_id: 关联 AI 决策 ID
            entry_order_id: 开仓订单ID
            exit_order_id: 平仓订单ID

        Returns:
            创建的 Trade 实例
        """
        try:
            # 计算持仓时长
            holding_duration = exit_time - entry_time

            # 计算总手续费
            total_fees = Decimal(0)
            if entry_fee:
                total_fees += entry_fee
            if exit_fee:
                total_fees += exit_fee

            # 计算名义价值
            notional_entry = quantity * entry_price
            notional_exit = quantity * exit_price

            # 计算净盈亏
            if side == 'long':
                # 做多：卖出价 - 买入价
                pnl = (exit_price - entry_price) * quantity - total_fees
            else:  # short
                # 做空：买入价 - 卖出价
                pnl = (entry_price - exit_price) * quantity - total_fees

            # 计算盈亏百分比
            pnl_pct = (pnl / notional_entry * 100) if notional_entry > 0 else Decimal(0)

            trade = Trade(
                session_id=session_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                exit_price=exit_price,
                price=entry_price,  # 向后兼容
                total_value=notional_entry,
                leverage=leverage,
                entry_time=entry_time,
                exit_time=exit_time,
                holding_duration=holding_duration,
                entry_fee=entry_fee,
                exit_fee=exit_fee,
                total_fees=total_fees,
                fee=total_fees,  # 向后兼容
                fee_currency=fee_currency,
                notional_entry=notional_entry,
                notional_exit=notional_exit,
                pnl=pnl,
                pnl_pct=pnl_pct,
                ai_decision_id=ai_decision_id,
                entry_order_id=entry_order_id,
                exit_order_id=exit_order_id,
                exchange_order_id=exit_order_id,  # 向后兼容
                order_type='market'
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
                quantity=float(quantity),
                entry_price=float(entry_price),
                exit_price=float(exit_price),
                pnl=float(pnl),
                holding_duration=str(holding_duration)
            )

            return trade

        except Exception as e:
            logger.error(f"创建交易记录失败: {str(e)}")
            self.db.rollback()
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

