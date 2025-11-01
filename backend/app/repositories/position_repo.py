"""
持仓 Repository
管理持仓数据的访问层，支持基于会话的持仓管理和盈亏计算
修改时间: 2025-10-29 (添加会话支持)
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from decimal import Decimal

from ..models.position import Position
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PositionRepository:
    """持仓数据访问层"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, id: int) -> Optional[Position]:
        """根据 ID 获取持仓"""
        return self.db.query(Position).filter(Position.id == id).first()
    
    def update(self, id: int, **kwargs) -> Optional[Position]:
        """更新持仓"""
        position = self.get_by_id(id)
        if not position:
            return None
        
        for key, value in kwargs.items():
            if hasattr(position, key):
                setattr(position, key, value)
        
        self.db.commit()
        self.db.refresh(position)
        return position
    
    def create_position(
        self,
        session_id: int,
        symbol: str,
        side: str,
        quantity: Decimal,
        entry_price: Decimal,
        leverage: int = 1,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None,
        ai_decision_id: Optional[int] = None,
        entry_order_id: Optional[int] = None
    ) -> Position:
        """
        创建持仓
        
        Args:
            session_id: 所属会话 ID
            symbol: 交易对
            side: 持仓方向 (long, short)
            quantity: 数量
            entry_price: 入场价格
            leverage: 杠杆
            stop_loss: 止损价
            take_profit: 止盈价
            ai_decision_id: 关联的 AI 决策 ID
            entry_order_id: 入场订单 ID
            
        Returns:
            创建的 Position 实例
        """
        try:
            position = Position(
                session_id=session_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price,
                current_price=entry_price,
                leverage=leverage,
                stop_loss=stop_loss,
                take_profit=take_profit,
                ai_decision_id=ai_decision_id,
                entry_order_id=entry_order_id,
                status="active"
            )
            self.db.add(position)
            self.db.commit()
            self.db.refresh(position)
            
            logger.info(
                "持仓已创建",
                position_id=position.id,
                session_id=session_id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price
            )
            
            return position
            
        except Exception as e:
            logger.error(f"创建持仓失败: {str(e)}")
            raise
    
    def get_active_positions(self, session_id: int) -> List[Position]:
        """
        获取指定会话的所有活跃持仓
        
        Args:
            session_id: 会话 ID
        
        Returns:
            活跃持仓列表
        """
        return self.db.query(Position)\
            .filter(
                Position.session_id == session_id,
                Position.status == "active"
            )\
            .all()
    
    def close_position(
        self,
        position_id: int,
        exit_price: Decimal,
        exit_order_id: Optional[int] = None
    ) -> Optional[Position]:
        """
        平仓

        Args:
            position_id: 持仓 ID
            exit_price: 出场价格
            exit_order_id: 出场订单 ID

        Returns:
            更新后的持仓或 None
        """
        position = self.get_by_id(position_id)
        if not position:
            return None

        # 计算已实现盈亏
        # 做多: (出场价 - 入场价) * 数量 * 杠杆
        # 做空: (入场价 - 出场价) * 数量 * 杠杆
        if position.side == 'long':
            realized_pnl = (exit_price - position.entry_price) * position.quantity * position.leverage
        else:  # short
            realized_pnl = (position.entry_price - exit_price) * position.quantity * position.leverage

        updated = self.update(
            position_id,
            status="closed",
            current_price=exit_price,
            realized_pnl=realized_pnl,
            unrealized_pnl=Decimal(0),
            exit_order_id=exit_order_id
        )

        if updated:
            logger.info(
                "持仓已平仓",
                position_id=position_id,
                symbol=position.symbol,
                side=position.side,
                realized_pnl=realized_pnl
            )

        return updated
    
    def get_total_pnl(
        self,
        session_id: int,
        symbol: Optional[str] = None
    ) -> Decimal:
        query = self.db.query(Position).filter(Position.session_id == session_id)
        
        if symbol:
            query = query.filter(Position.symbol == symbol)
        
        positions = query.all()
        
        total_pnl = Decimal(0)
        for pos in positions:
            # 已实现盈亏
            if pos.realized_pnl:
                total_pnl += pos.realized_pnl
            # 未实现盈亏（仅活跃持仓）
            if pos.status == "active" and pos.unrealized_pnl:
                total_pnl += pos.unrealized_pnl
        
        return total_pnl
    
    def get_by_session(
        self,
        session_id: int,
        limit: int = 100
    ) -> List[Position]:
        """
        获取指定会话的所有持仓
        
        Args:
            session_id: 会话 ID
            limit: 返回数量
            
        Returns:
            持仓列表
        """
        return self.db.query(Position)\
            .filter(Position.session_id == session_id)\
            .order_by(desc(Position.created_at))\
            .limit(limit)\
            .all()

    def update_stop_loss_take_profit(
        self,
        position_id: int,
        stop_loss: Optional[Decimal] = None,
        take_profit: Optional[Decimal] = None
    ) -> Optional[Position]:
        """
        更新持仓的止损止盈
        
        Args:
            position_id: 持仓 ID
            stop_loss: 止损价格
            take_profit: 止盈价格
            
        Returns:
            更新后的持仓或 None
        """
        position = self.get_by_id(position_id)
        if not position:
            return None
        
        update_data = {}
        if stop_loss is not None:
            update_data['stop_loss'] = stop_loss
        if take_profit is not None:
            update_data['take_profit'] = take_profit
        
        if not update_data:
            return position
        
        updated = self.update(position_id, **update_data)
        
        if updated:
            logger.info(
                "持仓止损止盈已更新",
                position_id=position_id,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
        
        return updated

