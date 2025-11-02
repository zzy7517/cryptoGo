"""
抽象交易所基类
定义所有交易所的通用接口，包括账户管理、交易执行、持仓查询等
创建时间: 2025-11-01
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum

from ..utils.logging import get_logger

logger = get_logger(__name__)


class OrderSide(str, Enum):
    """订单方向"""
    BUY = "buy"
    SELL = "sell"


class PositionSide(str, Enum):
    """持仓方向（合约）- 仅支持双向持仓"""
    LONG = "long"
    SHORT = "short"


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


class AbstractExchange(ABC):
    """
    抽象交易所基类
    
    定义所有交易所都需要实现的接口，包括：
    - 账户信息管理
    - 持仓查询
    - 订单执行
    - 杠杆设置
    - 止损/止盈
    """
    
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        """
        初始化交易所
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        logger.info(
            f"初始化交易所: {self.__class__.__name__}",
            testnet=testnet
        )
    
    # ==================== 初始化 ====================
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化交易所连接
        
        Returns:
            是否初始化成功
        """
        pass
    
    # ==================== 账户相关 ====================
    
    @abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息字典，包含余额、权限等
        """
        pass
    
    @abstractmethod
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            持仓列表
        """
        pass
    
    @abstractmethod
    def get_position(
        self,
        symbol: str,
        position_side: Optional[PositionSide] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个持仓信息
        
        Args:
            symbol: 交易对
            position_side: 持仓方向（None表示获取所有）
            
        Returns:
            持仓信息字典
        """
        pass
    
    # ==================== 交易相关 ====================
    
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
            symbol: 交易对
            side: 订单方向（buy/sell）
            quantity: 数量
            position_side: 持仓方向（long/short），合约专用
            reduce_only: 是否只减仓
            
        Returns:
            订单结果
        """
        pass
    

    # ==================== 杠杆和止损止盈 ====================
    
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
    
    # ==================== 便捷方法 ====================
    
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
            stop_loss_price: 止损价格（仅供AI参考，不创建委托单）
            take_profit_price: 止盈价格（仅供AI参考，不创建委托单）
            
        Returns:
            订单结果
            
        注意：
            stop_loss_price 和 take_profit_price 仅作为AI决策的参考值，
            不会在交易所创建委托单。真正的止损止盈由AI在每个周期自主决定。
        """
        try:
            # 设置杠杆
            if leverage:
                self.set_leverage(symbol, leverage)
            
            # 开多仓（买入）- 仅使用市价单
            result = self.create_market_order(
                symbol=symbol,
                side=OrderSide.BUY,
                quantity=quantity,
                position_side=PositionSide.LONG
            )
            
            if not result.success:
                return result
            
            # AI盯盘模式：不创建止损止盈委托单
            # AI会在每个决策周期基于最新数据自主决定是否平仓
            logger.info(
                f"✅ 开多仓成功 (AI盯盘模式)",
                symbol=symbol,
                quantity=quantity,
                leverage=leverage,
                stop_loss_reference=stop_loss_price,
                take_profit_reference=take_profit_price
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
            stop_loss_price: 止损价格（仅供AI参考，不创建委托单）
            take_profit_price: 止盈价格（仅供AI参考，不创建委托单）
            
        Returns:
            订单结果
            
        注意：
            stop_loss_price 和 take_profit_price 仅作为AI决策的参考值，
            不会在交易所创建委托单。真正的止损止盈由AI在每个周期自主决定。
        """
        try:
            # 设置杠杆
            if leverage:
                self.set_leverage(symbol, leverage)
            
            # 开空仓（卖出）- 仅使用市价单
            result = self.create_market_order(
                symbol=symbol,
                side=OrderSide.SELL,
                quantity=quantity,
                position_side=PositionSide.SHORT
            )
            
            if not result.success:
                return result
            
            # AI盯盘模式：不创建止损止盈委托单
            # AI会在每个决策周期基于最新数据自主决定是否平仓
            logger.info(
                f"✅ 开空仓成功 (AI盯盘模式)",
                symbol=symbol,
                quantity=quantity,
                leverage=leverage,
                stop_loss_reference=stop_loss_price,
                take_profit_reference=take_profit_price
            )
            
            return result
            
        except Exception as e:
            logger.error(f"开空仓失败: {e}", symbol=symbol)
            return OrderResult(success=False, error=str(e))
    
    # ==================== 市场数据相关 ====================
    
    @abstractmethod
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情数据
        
        Args:
            symbol: 交易对
            
        Returns:
            行情数据字典
        """
        pass
    
    @abstractmethod
    def get_klines(
        self,
        symbol: str,
        interval: str = '1h',
        limit: int = 100,
        since: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取K线数据
        
        Args:
            symbol: 交易对
            interval: 时间周期
            limit: 返回数据条数
            since: 起始时间戳（毫秒）
            
        Returns:
            K线数据列表
        """
        pass
    
    @abstractmethod
    def get_order_book(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对
            limit: 深度级别
            
        Returns:
            订单簿数据
        """
        pass
    
    @abstractmethod
    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        获取资金费率（合约市场）
        
        Args:
            symbol: 交易对
            
        Returns:
            资金费率数据
        """
        pass
    
    @abstractmethod
    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        获取持仓量（合约市场）
        
        Args:
            symbol: 交易对
            
        Returns:
            持仓量数据
        """
        pass

