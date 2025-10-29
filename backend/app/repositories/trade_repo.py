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

from app.models.trade import Trade
from app.repositories.base import BaseRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class TradeRepository(BaseRepository[Trade]):
    """交易记录数据访问层"""
    
    def __init__(self, db: Session):
        super().__init__(Trade, db)
    
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
            trade = self.create(
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
        """
        获取指定会话的所有交易
        
        Args:
            session_id: 会话 ID
            limit: 返回数量
            
        Returns:
            交易记录列表
        """
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
        """
        获取指定会话和交易对的交易记录
        
        Args:
            session_id: 会话 ID
            symbol: 交易对
            limit: 返回数量
            
        Returns:
            交易记录列表
        """
        return self.db.query(Trade)\
            .filter(
                Trade.session_id == session_id,
                Trade.symbol == symbol
            )\
            .order_by(desc(Trade.created_at))\
            .limit(limit)\
            .all()
    
    def get_by_position(
        self,
        position_id: int
    ) -> List[Trade]:
        """
        获取指定持仓的所有交易
        
        Args:
            position_id: 持仓 ID
            
        Returns:
            交易记录列表
        """
        return self.db.query(Trade)\
            .filter(Trade.position_id == position_id)\
            .order_by(Trade.created_at)\
            .all()
    
    def close_trade(
        self,
        trade_id: int,
        exit_price: Decimal,
        exit_time: Optional[datetime] = None
    ) -> Optional[Trade]:
        """
        平仓交易（更新出场信息和盈亏）
        
        Args:
            trade_id: 交易 ID
            exit_price: 出场价格
            exit_time: 出场时间
            
        Returns:
            更新后的交易或 None
        """
        trade = self.get_by_id(trade_id)
        if not trade:
            return None
        
        # 计算盈亏
        if trade.side in ['buy', 'long']:
            pnl = (exit_price - trade.price) * trade.quantity * trade.leverage
        else:  # sell, short
            pnl = (trade.price - exit_price) * trade.quantity * trade.leverage
        
        # 减去手续费
        if trade.fee:
            pnl -= trade.fee
        
        # 计算盈亏百分比
        pnl_pct = (pnl / trade.total_value) * 100 if trade.total_value > 0 else 0
        
        # 计算持仓时长
        exit_time = exit_time or datetime.now()
        holding_duration = exit_time - trade.entry_time if trade.entry_time else None
        
        updated = self.update(
            trade_id,
            exit_time=exit_time,
            pnl=pnl,
            pnl_pct=pnl_pct,
            holding_duration=holding_duration
        )
        
        if updated:
            logger.info(
                "交易已平仓",
                trade_id=trade_id,
                pnl=pnl,
                pnl_pct=pnl_pct
            )
        
        return updated
    
    def get_session_statistics(self, session_id: int) -> dict:
        """
        获取会话的交易统计
        
        Args:
            session_id: 会话 ID
            
        Returns:
            统计数据字典
        """
        trades = self.get_by_session(session_id, limit=10000)
        
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t.pnl and t.pnl > 0])
        losing_trades = len([t for t in trades if t.pnl and t.pnl < 0])
        
        total_pnl = sum([t.pnl for t in trades if t.pnl]) or Decimal(0)
        
        biggest_win = max([t.pnl for t in trades if t.pnl], default=Decimal(0))
        biggest_loss = min([t.pnl for t in trades if t.pnl], default=Decimal(0))
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        avg_leverage = (
            sum([t.leverage for t in trades]) / total_trades
        ) if total_trades > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "biggest_win": biggest_win,
            "biggest_loss": biggest_loss,
            "avg_leverage": avg_leverage
        }

