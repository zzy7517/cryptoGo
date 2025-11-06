"""
币安交易所实现
整合账户管理、交易执行等所有功能
创建时间: 2025-11-01
"""
from typing import Dict, Any, Optional, List

from ..base import (
    AbstractExchange,
    OrderSide,
    PositionSide,
    OrderResult
)
from .client import BinanceFuturesClient
from .market_data import BinanceMarketData
from ...utils.logging import get_logger
from ...utils.exceptions import ConfigurationException

logger = get_logger(__name__)


class BinanceExchange(AbstractExchange):
    """
    币安交易所实现
    
    整合了账户信息、持仓查询、订单执行等所有功能
    使用 BinanceFuturesClient 进行底层 API 调用
    """
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        proxies: Optional[Dict[str, str]] = None
    ):
        """
        初始化币安交易所
        
        Args:
            api_key: API密钥
            api_secret: API密钥
            testnet: 是否使用测试网
            proxies: 代理配置
        """
        super().__init__(api_key, api_secret, testnet)
        self.proxies = proxies
        self.client: Optional[BinanceFuturesClient] = None
        self.market_data: Optional[BinanceMarketData] = None
        self._symbol_filters: Dict[str, Dict[str, Any]] = {}  # 缓存交易对过滤器
        self.initialize()
    
    def initialize(self) -> bool:
        """
        初始化币安交易所连接
        
        Returns:
            是否初始化成功
        """
        try:
            # 创建交易客户端
            self.client = BinanceFuturesClient(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet,
                proxies=self.proxies,
                timeout=30
            )
            
            # 创建市场数据获取器（使用同一个client）
            self.market_data = BinanceMarketData(client=self.client)
            
            # 注意：系统使用单向持仓模式（One-way Mode）
            logger.info("系统使用单向持仓模式（One-way Mode），positionSide=BOTH")
            
            # 测试连接
            server_time = self.client.get_server_time()
            logger.info(
                f"币安交易所初始化成功",
                testnet=self.testnet,
                server_time=server_time.get('serverTime')
            )
            
            return True
            
        except Exception as e:
            error_msg = f"初始化币安交易所失败: {str(e)}"
            logger.exception(error_msg)
            raise ConfigurationException(error_msg) from e
    
    def _get_symbol_filters(self, symbol: str) -> Dict[str, Any]:
        """
        获取交易对的过滤器（精度、最小/最大数量等）
        
        Args:
            symbol: 交易对（如 BTCUSDT）
            
        Returns:
            包含 LOT_SIZE 和 PRICE_FILTER 等过滤器的字典
        """
        # 标准化交易对格式
        symbol = symbol.replace('/', '').replace(':USDT', '').replace(':usdt', '')
        
        # 如果已缓存，直接返回
        if symbol in self._symbol_filters:
            return self._symbol_filters[symbol]
        
        try:
            # 获取交易所信息
            exchange_info = self.client.get_exchange_info()
            
            # 查找对应的交易对
            for symbol_info in exchange_info.get('symbols', []):
                if symbol_info['symbol'] == symbol:
                    filters = {}
                    for f in symbol_info.get('filters', []):
                        filters[f['filterType']] = f
                    
                    # 缓存结果
                    self._symbol_filters[symbol] = filters
                    return filters
            
            logger.warning(f"未找到交易对 {symbol} 的过滤器信息")
            return {}
            
        except Exception as e:
            logger.error(f"获取交易对过滤器失败: {e}", symbol=symbol)
            return {}
    
    def _format_quantity(self, symbol: str, quantity: float) -> float:
        """
        根据交易对的精度要求格式化数量
        
        Args:
            symbol: 交易对（如 BTCUSDT）
            quantity: 原始数量
            
        Returns:
            格式化后的数量
        """
        filters = self._get_symbol_filters(symbol)
        
        if not filters:
            # 如果没有过滤器信息，使用默认精度（3位小数）
            logger.warning(f"未获取到 {symbol} 的过滤器信息，使用默认精度")
            return round(quantity, 3)
        
        # 获取 LOT_SIZE 过滤器
        lot_size = filters.get('LOT_SIZE', {})
        if lot_size:
            step_size = float(lot_size.get('stepSize', 0.001))
            min_qty = float(lot_size.get('minQty', 0))
            max_qty = float(lot_size.get('maxQty', 1000000))
            
            # 计算步长的小数位数
            step_str = f"{step_size:.10f}".rstrip('0')
            if '.' in step_str:
                precision = len(step_str.split('.')[1])
            else:
                precision = 0
            
            # 按步长向下取整
            formatted_qty = (quantity // step_size) * step_size
            
            # 四舍五入到正确的小数位数
            formatted_qty = round(formatted_qty, precision)
            
            # 确保在最小最大范围内
            if formatted_qty < min_qty:
                formatted_qty = min_qty
            elif formatted_qty > max_qty:
                formatted_qty = max_qty
            
            logger.debug(
                f"数量格式化: {quantity:.10f} -> {formatted_qty:.10f}",
                symbol=symbol,
                step_size=step_size,
                precision=precision
            )
            
            return formatted_qty
        
        # 如果没有LOT_SIZE，返回默认精度
        return round(quantity, 3)
    
    
    # ==================== 账户相关 ====================
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息字典，包含余额、权限等
        """
        try:
            account_info = self.client.get_account_info()
            
            # 提取主要资产信息（USDT, BTC等）
            assets = account_info.get('assets', [])
            main_assets = {}
            
            for asset in assets:
                asset_name = asset.get('asset')
                wallet_balance = float(asset.get('walletBalance', 0))
                
                # 只保留有余额的资产
                if wallet_balance > 0:
                    main_assets[asset_name] = {
                        'walletBalance': wallet_balance,
                        'unrealizedProfit': float(asset.get('unrealizedProfit', 0)),
                        'marginBalance': float(asset.get('marginBalance', 0)),
                        'availableBalance': float(asset.get('availableBalance', 0)),
                        'maxWithdrawAmount': float(asset.get('maxWithdrawAmount', 0))
                    }
            
            return {
                'totalWalletBalance': float(account_info.get('totalWalletBalance', 0)),
                'availableBalance': float(account_info.get('availableBalance', 0)),
                'totalUnrealizedProfit': float(account_info.get('totalUnrealizedProfit', 0)),
                'totalMarginBalance': float(account_info.get('totalMarginBalance', 0)),
                'maxWithdrawAmount': float(account_info.get('maxWithdrawAmount', 0)),
                # 保证金相关
                'totalInitialMargin': float(account_info.get('totalInitialMargin', 0)),
                'totalMaintMargin': float(account_info.get('totalMaintMargin', 0)),
                'totalPositionInitialMargin': float(account_info.get('totalPositionInitialMargin', 0)),
                'totalOpenOrderInitialMargin': float(account_info.get('totalOpenOrderInitialMargin', 0)),
                'canTrade': account_info.get('canTrade', False),
                'canDeposit': account_info.get('canDeposit', False),
                'canWithdraw': account_info.get('canWithdraw', False),
                'assets': main_assets,
                'updateTime': account_info.get('updateTime', 0)
            }
            
        except Exception as e:
            logger.error(f"获取账户信息失败: {str(e)}")
            raise
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            持仓列表，只返回有持仓的记录
        """
        try:
            positions = self.client.get_position_risk(symbol)
            
            # 过滤出有持仓的记录
            active_positions = []
            for pos in positions:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    entry_price = float(pos.get('entryPrice', 0))
                    mark_price = float(pos.get('markPrice', 0))
                    unrealized_profit = float(pos.get('unRealizedProfit', 0))
                    
                    # 计算收益率
                    if entry_price != 0 and position_amt != 0:
                        notional = abs(position_amt * entry_price)
                        pnl_pct = (unrealized_profit / notional) * 100 if notional != 0 else 0
                    else:
                        pnl_pct = 0
                    
                    # 判断方向（做多/做空）
                    side = 'long' if position_amt > 0 else 'short'
                    
                    active_positions.append({
                        'symbol': pos.get('symbol'),
                        'side': side,
                        'positionSide': pos.get('positionSide'),
                        'quantity': abs(position_amt),
                        'entryPrice': entry_price,
                        'markPrice': mark_price,
                        'unrealizedProfit': unrealized_profit,
                        'unrealizedProfitPct': round(pnl_pct, 2),
                        'leverage': int(pos.get('leverage', 1)),
                        'marginType': pos.get('marginType'),
                        'liquidationPrice': float(pos.get('liquidationPrice', 0)),
                        'updateTime': pos.get('updateTime', 0)
                    })
            
            return active_positions
            
        except Exception as e:
            logger.error(f"获取持仓信息失败: {str(e)}")
            raise
    
    def get_position(
        self,
        symbol: str,
        position_side: Optional[PositionSide] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取单个持仓信息
        
        Args:
            symbol: 交易对
            position_side: 持仓方向
            
        Returns:
            持仓信息字典
        """
        try:
            positions = self.get_positions(symbol)
            
            if not positions:
                return None
            
            # 如果指定了持仓方向，筛选
            if position_side:
                for pos in positions:
                    if pos['side'] == position_side.value:
                        return pos
                return None
            
            # 否则返回第一个
            return positions[0]
            
        except Exception as e:
            logger.error(f"获取持仓信息失败: {str(e)}", symbol=symbol)
            raise
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取所有未成交订单
        
        Args:
            symbol: 交易对（可选），不传则返回所有
            
        Returns:
            未成交订单列表
        """
        try:
            orders = self.client.get_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"获取未成交订单失败: {str(e)}")
            raise
    
    # ==================== 交易相关 ====================
    
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
            symbol: 交易对（如 BTCUSDT）
            side: 订单方向
            quantity: 数量
            position_side: 持仓方向
            reduce_only: 是否只减仓
            
        Returns:
            订单结果
        """
        try:
            # 格式化数量以符合Binance精度要求
            formatted_quantity = self._format_quantity(symbol, quantity)

            # 单向持仓模式：始终使用 BOTH
            pos_side = 'BOTH'

            logger.info(
                f"创建市价单: {symbol}",
                original_qty=quantity,
                formatted_qty=formatted_quantity,
                side=side.value,
                position_side=pos_side
            )

            order = self.client.create_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type='MARKET',
                quantity=formatted_quantity,
                position_side=pos_side,
                reduce_only=reduce_only
            )
            
            return OrderResult(
                success=True,
                order_id=str(order.get('orderId')),
                symbol=order.get('symbol'),
                side=order.get('side'),
                order_type=order.get('type'),
                quantity=float(order.get('origQty', 0)),
                avg_price=float(order.get('avgPrice', 0)),
                status=order.get('status'),
                filled_quantity=float(order.get('executedQty', 0)),
                timestamp=order.get('updateTime'),
                raw_data=order
            )
            
        except Exception as e:
            logger.error(f"创建市价单失败: {e}", symbol=symbol, side=side, quantity=quantity)
            return OrderResult(success=False, error=str(e))
    
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
            # 格式化数量以符合Binance精度要求
            formatted_quantity = self._format_quantity(symbol, quantity)

            # 单向持仓模式：始终使用 BOTH
            pos_side = 'BOTH'

            order = self.client.create_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type='LIMIT',
                quantity=formatted_quantity,
                price=price,
                position_side=pos_side,
                time_in_force='GTC',
                reduce_only=reduce_only
            )
            
            return OrderResult(
                success=True,
                order_id=str(order.get('orderId')),
                symbol=order.get('symbol'),
                side=order.get('side'),
                order_type=order.get('type'),
                quantity=float(order.get('origQty', 0)),
                price=float(order.get('price', 0)),
                avg_price=float(order.get('avgPrice', 0)),
                status=order.get('status'),
                filled_quantity=float(order.get('executedQty', 0)),
                timestamp=order.get('updateTime'),
                raw_data=order
            )
            
        except Exception as e:
            logger.error(f"创建限价单失败: {e}", symbol=symbol, side=side, price=price)
            return OrderResult(success=False, error=str(e))
    
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
            order = self.client.get_order(symbol, order_id=int(order_id))
            return {
                'orderId': order.get('orderId'),
                'symbol': order.get('symbol'),
                'side': order.get('side'),
                'type': order.get('type'),
                'quantity': float(order.get('origQty', 0)),
                'price': float(order.get('price', 0)),
                'avgPrice': float(order.get('avgPrice', 0)),
                'status': order.get('status'),
                'filledQuantity': float(order.get('executedQty', 0)),
                'updateTime': order.get('updateTime')
            }
        except Exception as e:
            logger.error(f"查询订单状态失败: {e}", symbol=symbol, order_id=order_id)
            return None
    
    # ==================== 杠杆和止损止盈 ====================
    
    def set_leverage(self, symbol: str, leverage: int) -> bool:
        """
        设置杠杆倍数
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数
            
        Returns:
            是否设置成功
        """
        try:
            self.client.change_leverage(symbol, leverage)
            logger.info(f"杠杆已设置", symbol=symbol, leverage=leverage)
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
                quantity = position['quantity']
            
            # 格式化数量以符合Binance精度要求
            formatted_quantity = self._format_quantity(symbol, quantity)
            
            # 止损单方向与持仓方向相反
            side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY

            # 单向持仓模式：始终使用 BOTH
            pos_side = 'BOTH'

            order = self.client.create_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type='STOP_MARKET',
                quantity=formatted_quantity,
                stop_price=stop_price,
                position_side=pos_side,
                reduce_only=True
            )
            
            return OrderResult(
                success=True,
                order_id=str(order.get('orderId')),
                symbol=order.get('symbol'),
                side=order.get('side'),
                order_type=order.get('type'),
                quantity=float(order.get('origQty', 0)),
                price=stop_price,
                status=order.get('status'),
                raw_data=order
            )
            
        except Exception as e:
            logger.error(f"设置止损失败: {e}", symbol=symbol, stop_price=stop_price)
            return OrderResult(success=False, error=str(e))
    
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
                quantity = position['quantity']
            
            # 格式化数量以符合Binance精度要求
            formatted_quantity = self._format_quantity(symbol, quantity)
            
            # 止盈单方向与持仓方向相反
            side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY

            # 单向持仓模式：始终使用 BOTH
            pos_side = 'BOTH'

            order = self.client.create_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type='TAKE_PROFIT_MARKET',
                quantity=formatted_quantity,
                stop_price=take_profit_price,
                position_side=pos_side,
                reduce_only=True
            )
            
            return OrderResult(
                success=True,
                order_id=str(order.get('orderId')),
                symbol=order.get('symbol'),
                side=order.get('side'),
                order_type=order.get('type'),
                quantity=float(order.get('origQty', 0)),
                price=take_profit_price,
                status=order.get('status'),
                raw_data=order
            )
            
        except Exception as e:
            logger.error(f"设置止盈失败: {e}", symbol=symbol, take_profit_price=take_profit_price)
            return OrderResult(success=False, error=str(e))
    
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
            # 如果没有指定数量，获取当前持仓数量
            if quantity is None:
                position = self.get_position(symbol, position_side)
                if not position:
                    return OrderResult(success=False, error="未找到持仓")
                quantity = position['quantity']
            
            # 平仓方向与持仓方向相反
            side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY

            # 单向持仓模式下，直接使用 reduce_only=True 即可平仓
            return self.create_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                position_side=None,  # 单向持仓模式，函数内会自动设为 BOTH
                reduce_only=True
            )
            
        except Exception as e:
            logger.error(f"平仓失败: {e}", symbol=symbol, position_side=position_side)
            return OrderResult(success=False, error=str(e))
    
    # ==================== 市场数据相关 ====================
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情数据
        
        Args:
            symbol: 交易对
            
        Returns:
            行情数据字典
        """
        return self.market_data.get_ticker(symbol)
    
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
        return self.market_data.get_klines(symbol, interval, limit, since)
    
    def get_order_book(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        """
        获取订单簿数据
        
        Args:
            symbol: 交易对
            limit: 深度级别
            
        Returns:
            订单簿数据
        """
        return self.market_data.get_order_book(symbol, limit)
    
    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        获取资金费率（合约市场）
        
        Args:
            symbol: 交易对
            
        Returns:
            资金费率数据
        """
        return self.market_data.get_funding_rate(symbol)
    
    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        获取持仓量（合约市场）
        
        Args:
            symbol: 交易对
            
        Returns:
            持仓量数据
        """
        return self.market_data.get_open_interest(symbol)
    
    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()

