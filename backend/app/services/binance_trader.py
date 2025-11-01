"""
币安交易类实现
使用 CCXT 库实现币安合约交易
创建时间: 2025-10-31
"""
import ccxt
from typing import Dict, Any, Optional, List
from decimal import Decimal
from datetime import datetime

from app.services.abstract_trader import (
    AbstractTrader,
    OrderSide,
    OrderType,
    PositionSide,
    OrderResult
)
from app.utils.logging import get_logger
from app.utils.exceptions import (
    DataFetchException,
    RateLimitException,
    ConfigurationException
)

logger = get_logger(__name__)


class BinanceTrader(AbstractTrader):
    """
    币安交易实现类
    
    使用 CCXT 实现币安合约交易功能，包括：
    - 开仓/平仓
    - 杠杆设置
    - 止损/止盈
    - 持仓查询
    """
    
    def __init__(self, api_key: str, api_secret: str):
        """
        初始化币安交易器
        
        Args:
            api_key: 币安API密钥
            api_secret: 币安API密钥
        """
        super().__init__(api_key, api_secret)
        self.exchange: Optional[ccxt.binance] = None
        self.initialize()
    
    def initialize(self) -> bool:
        """
        初始化币安交易所连接
        
        Returns:
            是否初始化成功
        """
        try:
            from app.utils.config import settings
            
            # 配置币安交易所
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # 合约交易
                    'adjustForTimeDifference': True,  # 自动调整时间差
                },
                'timeout': 10000,  # 10秒超时
            }
            
            # 添加代理配置
            if settings.HTTP_PROXY or settings.HTTPS_PROXY:
                config['proxies'] = {}
                if settings.HTTP_PROXY:
                    config['proxies']['http'] = settings.HTTP_PROXY
                if settings.HTTPS_PROXY:
                    config['proxies']['https'] = settings.HTTPS_PROXY
                logger.debug(f"使用代理: {config['proxies']}")

            self.exchange = ccxt.binance(config)

            # 测试连接
            self.exchange.load_markets()
            
            logger.info(
                "币安交易器初始化成功",
                markets_count=len(self.exchange.markets)
            )
            
            return True
            
        except Exception as e:
            error_msg = f"初始化币安交易器失败: {str(e)}"
            logger.exception(error_msg)
            raise ConfigurationException(error_msg) from e
    
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
            position_side: 持仓方向（long/short）
            reduce_only: 是否只减仓
            
        Returns:
            订单结果
        """
        try:
            # 构建订单参数
            params = {}
            
            # 币安合约需要设置持仓方向
            if position_side:
                params['positionSide'] = position_side.value.upper()
            
            # 只减仓标志
            if reduce_only:
                params['reduceOnly'] = True
            
            logger.info(
                f"创建市价单: {symbol} {side.value} {quantity}",
                position_side=position_side.value if position_side else None,
                reduce_only=reduce_only
            )
            
            # 创建市价单
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side=side.value,
                amount=quantity,
                params=params
            )
            
            # 解析订单结果
            result = self._parse_order_result(order)
            
            logger.info(
                f"市价单创建成功: {order.get('id')}",
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                avg_price=result.avg_price
            )
            
            return result
            
        except ccxt.InsufficientFunds as e:
            error_msg = f"余额不足: {str(e)}"
            logger.error(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
            
        except ccxt.InvalidOrder as e:
            error_msg = f"无效订单: {str(e)}"
            logger.error(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
            
        except ccxt.RateLimitExceeded as e:
            error_msg = f"API请求频率超限: {str(e)}"
            logger.warning(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
            
        except Exception as e:
            error_msg = f"创建市价单失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
    
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
        try:
            # 构建订单参数
            params = {}
            
            # 币安合约需要设置持仓方向
            if position_side:
                params['positionSide'] = position_side.value.upper()
            
            # 只减仓标志
            if reduce_only:
                params['reduceOnly'] = True
            
            logger.info(
                f"创建限价单: {symbol} {side.value} {quantity} @ {price}",
                position_side=position_side.value if position_side else None,
                reduce_only=reduce_only
            )
            
            # 创建限价单
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side.value,
                amount=quantity,
                price=price,
                params=params
            )
            
            # 解析订单结果
            result = self._parse_order_result(order)
            
            logger.info(
                f"限价单创建成功: {order.get('id')}",
                symbol=symbol,
                side=side.value,
                quantity=quantity,
                price=price
            )
            
            return result
            
        except ccxt.InsufficientFunds as e:
            error_msg = f"余额不足: {str(e)}"
            logger.error(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
            
        except ccxt.InvalidOrder as e:
            error_msg = f"无效订单: {str(e)}"
            logger.error(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
            
        except Exception as e:
            error_msg = f"创建限价单失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
    
    def set_leverage(
        self,
        symbol: str,
        leverage: int
    ) -> bool:
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数
            
        Returns:
            是否设置成功
        """
        try:
            self.exchange.set_leverage(leverage, symbol)
            logger.info(f"设置杠杆成功: {symbol} {leverage}x")
            return True
            
        except Exception as e:
            logger.error(f"设置杠杆失败: {e}", symbol=symbol, leverage=leverage)
            return False
    
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
        try:
            # 如果没有指定数量，获取当前持仓数量
            if quantity is None:
                position = self.get_position(symbol, position_side)
                if not position:
                    return OrderResult(success=False, error="未找到持仓")
                quantity = abs(float(position.get('contracts', 0)))
            
            # 确定订单方向（平仓方向与持仓方向相反）
            side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY
            
            # 创建止损市价单
            params = {
                'positionSide': position_side.value.upper(),
                'stopPrice': stop_price,
                'reduceOnly': True
            }
            
            logger.info(
                f"设置止损单: {symbol} {position_side.value} @ {stop_price}",
                quantity=quantity
            )
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='STOP_MARKET',
                side=side.value,
                amount=quantity,
                params=params
            )
            
            result = self._parse_order_result(order)
            logger.info(f"止损单设置成功: {order.get('id')}")
            
            return result
            
        except Exception as e:
            error_msg = f"设置止损失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
    
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
        try:
            # 如果没有指定数量，获取当前持仓数量
            if quantity is None:
                position = self.get_position(symbol, position_side)
                if not position:
                    return OrderResult(success=False, error="未找到持仓")
                quantity = abs(float(position.get('contracts', 0)))
            
            # 确定订单方向（平仓方向与持仓方向相反）
            side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY
            
            # 创建止盈市价单
            params = {
                'positionSide': position_side.value.upper(),
                'stopPrice': take_profit_price,
                'reduceOnly': True
            }
            
            logger.info(
                f"设置止盈单: {symbol} {position_side.value} @ {take_profit_price}",
                quantity=quantity
            )
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='TAKE_PROFIT_MARKET',
                side=side.value,
                amount=quantity,
                params=params
            )
            
            result = self._parse_order_result(order)
            logger.info(f"止盈单设置成功: {order.get('id')}")
            
            return result
            
        except Exception as e:
            error_msg = f"设置止盈失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
    
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
        try:
            # 获取当前持仓
            position = self.get_position(symbol, position_side)
            if not position:
                return OrderResult(success=False, error="未找到持仓")
            
            # 如果没有指定数量，使用全部持仓数量
            if quantity is None:
                quantity = abs(float(position.get('contracts', 0)))
            
            if quantity <= 0:
                return OrderResult(success=False, error="持仓数量为0")
            
            # 确定平仓方向（与持仓方向相反）
            side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY
            
            logger.info(
                f"平仓: {symbol} {position_side.value} {quantity}"
            )
            
            # 创建平仓市价单
            result = self.create_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                position_side=position_side,
                reduce_only=True
            )
            
            if result.success:
                logger.info(f"平仓成功: {symbol} {position_side.value}")
            
            return result
            
        except Exception as e:
            error_msg = f"平仓失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol)
            return OrderResult(success=False, error=error_msg)
    
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
        try:
            positions = self.exchange.fetch_positions([symbol])
            
            for pos in positions:
                # 检查是否有持仓
                contracts = float(pos.get('contracts', 0))
                if contracts == 0:
                    continue
                
                # 如果指定了持仓方向，则过滤
                if position_side:
                    pos_side = pos.get('side', '').lower()
                    if pos_side != position_side.value:
                        continue
                
                # 返回持仓信息
                return {
                    'symbol': pos.get('symbol'),
                    'side': pos.get('side'),
                    'contracts': contracts,
                    'contractSize': pos.get('contractSize'),
                    'unrealizedPnl': pos.get('unrealizedPnl'),
                    'percentage': pos.get('percentage'),
                    'notional': pos.get('notional'),
                    'leverage': pos.get('leverage'),
                    'entryPrice': pos.get('entryPrice'),
                    'markPrice': pos.get('markPrice'),
                    'liquidationPrice': pos.get('liquidationPrice'),
                    'marginMode': pos.get('marginMode'),
                    'marginType': pos.get('marginType'),
                    'collateral': pos.get('collateral'),
                    'timestamp': pos.get('timestamp'),
                    'raw': pos
                }
            
            return None
            
        except Exception as e:
            logger.error(f"获取持仓失败: {e}", symbol=symbol)
            return None
    
    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        获取所有持仓
        
        Returns:
            持仓列表
        """
        try:
            positions = self.exchange.fetch_positions()
            
            result = []
            for pos in positions:
                # 只返回有持仓的
                contracts = float(pos.get('contracts', 0))
                if contracts == 0:
                    continue
                
                result.append({
                    'symbol': pos.get('symbol'),
                    'side': pos.get('side'),
                    'contracts': contracts,
                    'contractSize': pos.get('contractSize'),
                    'unrealizedPnl': pos.get('unrealizedPnl'),
                    'percentage': pos.get('percentage'),
                    'notional': pos.get('notional'),
                    'leverage': pos.get('leverage'),
                    'entryPrice': pos.get('entryPrice'),
                    'markPrice': pos.get('markPrice'),
                    'liquidationPrice': pos.get('liquidationPrice'),
                    'marginMode': pos.get('marginMode'),
                    'marginType': pos.get('marginType'),
                    'collateral': pos.get('collateral'),
                    'timestamp': pos.get('timestamp')
                })
            
            logger.info(f"获取所有持仓成功，共 {len(result)} 个")
            return result
            
        except Exception as e:
            logger.error(f"获取所有持仓失败: {e}")
            return []
    
    def get_balance(self, currency: str = 'USDT') -> Dict[str, Any]:
        """
        获取账户余额
        
        Args:
            currency: 币种
            
        Returns:
            余额信息
        """
        try:
            balance = self.exchange.fetch_balance()
            
            if currency in balance:
                currency_balance = balance[currency]
                result = {
                    'currency': currency,
                    'free': float(currency_balance.get('free', 0)),
                    'used': float(currency_balance.get('used', 0)),
                    'total': float(currency_balance.get('total', 0))
                }
                
                logger.debug(
                    f"账户余额: {currency}",
                    free=result['free'],
                    total=result['total']
                )
                
                return result
            
            return {
                'currency': currency,
                'free': 0.0,
                'used': 0.0,
                'total': 0.0
            }
            
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}", currency=currency)
            return {
                'currency': currency,
                'free': 0.0,
                'used': 0.0,
                'total': 0.0,
                'error': str(e)
            }
    
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
        try:
            self.exchange.cancel_order(order_id, symbol)
            logger.info(f"取消订单成功: {order_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消订单失败: {e}", symbol=symbol, order_id=order_id)
            return False
    
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
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            
            return {
                'id': order.get('id'),
                'symbol': order.get('symbol'),
                'type': order.get('type'),
                'side': order.get('side'),
                'price': order.get('price'),
                'average': order.get('average'),
                'amount': order.get('amount'),
                'filled': order.get('filled'),
                'remaining': order.get('remaining'),
                'status': order.get('status'),
                'timestamp': order.get('timestamp'),
                'raw': order
            }
            
        except Exception as e:
            logger.error(f"查询订单状态失败: {e}", symbol=symbol, order_id=order_id)
            return None
    
    def _parse_order_result(self, order: Dict[str, Any]) -> OrderResult:
        """
        解析订单结果
        
        Args:
            order: CCXT返回的订单对象
            
        Returns:
            OrderResult对象
        """
        try:
            # 提取费用信息
            fee = None
            fee_currency = None
            if 'fee' in order and order['fee']:
                fee = float(order['fee'].get('cost', 0))
                fee_currency = order['fee'].get('currency')
            
            return OrderResult(
                success=True,
                order_id=str(order.get('id')),
                symbol=order.get('symbol'),
                side=order.get('side'),
                order_type=order.get('type'),
                quantity=float(order.get('amount', 0)),
                price=float(order.get('price', 0)) if order.get('price') else None,
                avg_price=float(order.get('average', 0)) if order.get('average') else None,
                status=order.get('status'),
                filled_quantity=float(order.get('filled', 0)),
                fee=fee,
                fee_currency=fee_currency,
                timestamp=int(order.get('timestamp', 0)),
                raw_data=order
            )
            
        except Exception as e:
            logger.error(f"解析订单结果失败: {e}")
            return OrderResult(
                success=False,
                error=f"解析订单结果失败: {str(e)}",
                raw_data=order
            )


# 便捷函数：从配置创建 BinanceTrader
def create_binance_trader_from_config() -> BinanceTrader:
    """
    从配置文件创建 BinanceTrader 实例
    
    Returns:
        BinanceTrader实例
    """
    from app.utils.config import settings
    
    if not settings.BINANCE_API_KEY or not settings.BINANCE_SECRET:
        raise ConfigurationException("未配置币安API密钥")
    
    return BinanceTrader(
        api_key=settings.BINANCE_API_KEY,
        api_secret=settings.BINANCE_SECRET
    )
