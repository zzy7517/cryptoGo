"""
抽象交易类
定义交易接口，所有交易所实现都需要继承这个类
创建时间: 2025-10-31
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from decimal import Decimal
from enum import Enum

from app.utils.logging import get_logger

logger = get_logger(__name__)


class OrderSide(str, Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """订单类型"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"


class PositionSide(str, Enum):
    """持仓方向（合约）"""
    LONG = "long"
    SHORT = "short"
    BOTH = "both"  # 双向持仓模式


class OrderResult:
    """订单结果"""
    
    def __init__(
        self,
        success: bool,
        order_id: Optional[str] = None,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        order_type: Optional[str] = None,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        avg_price: Optional[float] = None,
        status: Optional[str] = None,
        filled_quantity: Optional[float] = None,
        fee: Optional[float] = None,
        fee_currency: Optional[str] = None,
        timestamp: Optional[int] = None,
        error: Optional[str] = None,
        raw_data: Optional[Dict] = None
    ):
        self.success = success
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.avg_price = avg_price
        self.status = status
        self.filled_quantity = filled_quantity
        self.fee = fee
        self.fee_currency = fee_currency
        self.timestamp = timestamp
        self.error = error
        self.raw_data = raw_data
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side,
            "order_type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "avg_price": self.avg_price,
            "status": self.status,
            "filled_quantity": self.filled_quantity,
            "fee": self.fee,
            "fee_currency": self.fee_currency,
            "timestamp": self.timestamp,
            "error": self.error
        }


class AbstractTrader(ABC):
    """
    抽象交易类
    
    定义所有交易所都需要实现的接口，包括：
    - 开仓/平仓
    - 市价/限价单
    - 止损/止盈设置
    - 持仓查询
    - 账户信息查询
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        """
        初始化交易器
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.exchange = None
        
        logger.info(
            f"初始化交易器: {self.__class__.__name__}",
            testnet=testnet
        )
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化交易所连接
        
        Returns:
            是否初始化成功
        """
        pass
    
    @abstractmethod
    def create_market_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        position_side: Optional[PositionSide] = None,
        reduce_only: bool = False
    ) -> OrderResult:
        """
        创建市价单
        
        Args:
            symbol: 交易对，如 'BTC/USDT:USDT'
            side: 订单方向（buy/sell）
            quantity: 数量
            position_side: 持仓方向（long/short），合约专用
            reduce_only: 是否只减仓
            
        Returns:
            订单结果
        """
        pass
    
    @abstractmethod
    def create_limit_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
        position_side: Optional[PositionSide] = None,
        reduce_only: bool = False
    ) -> OrderResult:
        """
        创建限价单
        
        Args:
            symbol: 交易对
            side: 订单方向
            quantity: 数量
            price: 限价
            position_side: 持仓方向
            reduce_only: 是否只减仓
            
        Returns:
            订单结果
        """
        pass
    
    @abstractmethod
    def set_leverage(
        self,
        symbol: str,
        leverage: int
    ) -> bool:
        """
        设置杠杆倍数（合约专用）
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数
            
        Returns:
            是否设置成功
        """
        pass
    
    @abstractmethod
    def set_stop_loss(
        self,
        symbol: str,
        position_side: PositionSide,
        stop_price: float,
        quantity: Optional[float] = None
    ) -> OrderResult:
        """
        设置止损单
        
        Args:
            symbol: 交易对
            position_side: 持仓方向
            stop_price: 止损价格
            quantity: 数量（None表示全部）
            
        Returns:
            订单结果
        """
        pass
    
    @abstractmethod
    def set_take_profit(
        self,
        symbol: str,
        position_side: PositionSide,
        take_profit_price: float,
        quantity: Optional[float] = None
    ) -> OrderResult:
        """
        设置止盈单
        
        Args:
            symbol: 交易对
            position_side: 持仓方向
            take_profit_price: 止盈价格
            quantity: 数量（None表示全部）
            
        Returns:
            订单结果
        """
        pass
    
    @abstractmethod
    def close_position(
        self,
        symbol: str,
        position_side: PositionSide,
        quantity: Optional[float] = None
    ) -> OrderResult:
        """
        平仓
        
        Args:
            symbol: 交易对
            position_side: 持仓方向
            quantity: 平仓数量（None表示全部平仓）
            
        Returns:
            订单结果
        """
        pass
    
    @abstractmethod
    def get_position(
        self,
        symbol: str,
        position_side: Optional[PositionSide] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取持仓信息
        
        Args:
            symbol: 交易对
            position_side: 持仓方向（None表示获取所有）
            
        Returns:
            持仓信息字典
        """
        pass
    
    @abstractmethod
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        获取所有持仓
        
        Returns:
            持仓列表
        """
        pass
    
    @abstractmethod
    def get_balance(self, currency: str = 'USDT') -> Dict[str, Any]:
        """
        获取账户余额
        
        Args:
            currency: 币种
            
        Returns:
            余额信息
        """
        pass
    
    @abstractmethod
    def cancel_order(
        self,
        symbol: str,
        order_id: str
    ) -> bool:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            是否取消成功
        """
        pass
    
    @abstractmethod
    def get_order_status(
        self,
        symbol: str,
        order_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        查询订单状态
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            订单信息
        """
        pass
    
    def open_long(
        self,
        symbol: str,
        quantity: float,
        leverage: Optional[int] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> OrderResult:
        """
        开多仓的便捷方法
        
        Args:
            symbol: 交易对
            quantity: 数量
            leverage: 杠杆倍数
            stop_loss_price: 止损价格
            take_profit_price: 止盈价格
            
        Returns:
            订单结果
        """
        try:
            # 设置杠杆
            if leverage:
                self.set_leverage(symbol, leverage)
            
            # 开多仓（买入）
            result = self.create_market_order(
                symbol=symbol,
                side=OrderSide.BUY,
                quantity=quantity,
                position_side=PositionSide.LONG
            )
            
            if not result.success:
                return result
            
            # 设置止损
            if stop_loss_price:
                self.set_stop_loss(
                    symbol=symbol,
                    position_side=PositionSide.LONG,
                    stop_price=stop_loss_price,
                    quantity=quantity
                )
            
            # 设置止盈
            if take_profit_price:
                self.set_take_profit(
                    symbol=symbol,
                    position_side=PositionSide.LONG,
                    take_profit_price=take_profit_price,
                    quantity=quantity
                )
            
            return result
            
        except Exception as e:
            logger.error(f"开多仓失败: {e}", symbol=symbol)
            return OrderResult(success=False, error=str(e))
    
    def open_short(
        self,
        symbol: str,
        quantity: float,
        leverage: Optional[int] = None,
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None
    ) -> OrderResult:
        """
        开空仓的便捷方法
        
        Args:
            symbol: 交易对
            quantity: 数量
            leverage: 杠杆倍数
            stop_loss_price: 止损价格
            take_profit_price: 止盈价格
            
        Returns:
            订单结果
        """
        try:
            # 设置杠杆
            if leverage:
                self.set_leverage(symbol, leverage)
            
            # 开空仓（卖出）
            result = self.create_market_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=quantity,
                position_side=PositionSide.SHORT
            )
            
            if not result.success:
                return result
            
            # 设置止损
            if stop_loss_price:
                self.set_stop_loss(
                    symbol=symbol,
                    position_side=PositionSide.SHORT,
                    stop_price=stop_loss_price,
                    quantity=quantity
                )
            
            # 设置止盈
            if take_profit_price:
                self.set_take_profit(
                    symbol=symbol,
                    position_side=PositionSide.SHORT,
                    take_profit_price=take_profit_price,
                    quantity=quantity
                )
            
            return result
            
        except Exception as e:
            logger.error(f"开空仓失败: {e}", symbol=symbol)
            return OrderResult(success=False, error=str(e))
    
    def close_long(
        self,
        symbol: str,
        quantity: Optional[float] = None
    ) -> OrderResult:
        """
        平多仓的便捷方法
        
        Args:
            symbol: 交易对
            quantity: 平仓数量（None表示全部）
            
        Returns:
            订单结果
        """
        return self.close_position(
            symbol=symbol,
            position_side=PositionSide.LONG,
            quantity=quantity
        )
    
    def close_short(
        self,
        symbol: str,
        quantity: Optional[float] = None
    ) -> OrderResult:
        """
        平空仓的便捷方法
        
        Args:
            symbol: 交易对
            quantity: 平仓数量（None表示全部）
            
        Returns:
            订单结果
        """
        return self.close_position(
            symbol=symbol,
            position_side=PositionSide.SHORT,
            quantity=quantity
        )
