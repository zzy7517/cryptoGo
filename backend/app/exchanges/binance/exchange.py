"""
币安交易所实现
整合账户管理、交易执行等所有功能
创建时间: 2025-11-01
"""
from typing import Dict, Any, Optional, List

from app.exchanges.base import (
    AbstractExchange,
    OrderSide,
    OrderType,
    PositionSide,
    OrderResult
)
from app.exchanges.binance.client import BinanceFuturesClient
from app.utils.logging import get_logger
from app.utils.exceptions import ConfigurationException

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
        self.initialize()
    
    def initialize(self) -> bool:
        """
        初始化币安交易所连接
        
        Returns:
            是否初始化成功
        """
        try:
            # 创建客户端
            self.client = BinanceFuturesClient(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=self.testnet,
                proxies=self.proxies,
                timeout=30
            )
            
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
    
    def test_connection(self) -> bool:
        """
        测试连接
        
        Returns:
            是否连接成功
        """
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            return False
    
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
                'canTrade': account_info.get('canTrade', False),
                'canDeposit': account_info.get('canDeposit', False),
                'canWithdraw': account_info.get('canWithdraw', False),
                'assets': main_assets,
                'updateTime': account_info.get('updateTime', 0)
            }
            
        except Exception as e:
            logger.error(f"获取账户信息失败: {str(e)}")
            raise
    
    def get_balance(self, currency: str = 'USDT') -> Dict[str, Any]:
        """
        获取账户余额
        
        Args:
            currency: 币种
            
        Returns:
            余额信息
        """
        try:
            balances = self.client.get_account_balance()
            
            for balance in balances:
                if balance.get('asset') == currency:
                    return {
                        'asset': balance.get('asset'),
                        'walletBalance': float(balance.get('walletBalance', 0)),
                        'unrealizedProfit': float(balance.get('unrealizedProfit', 0)),
                        'marginBalance': float(balance.get('marginBalance', 0)),
                        'availableBalance': float(balance.get('availableBalance', 0)),
                        'maxWithdrawAmount': float(balance.get('maxWithdrawAmount', 0))
                    }
            
            # 如果没找到该币种
            return {
                'asset': currency,
                'walletBalance': 0,
                'unrealizedProfit': 0,
                'marginBalance': 0,
                'availableBalance': 0,
                'maxWithdrawAmount': 0
            }
            
        except Exception as e:
            logger.error(f"获取余额失败: {str(e)}")
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
            order = self.client.create_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type='MARKET',
                quantity=quantity,
                position_side=position_side.value.upper() if position_side else 'BOTH',
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
            order = self.client.create_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type='LIMIT',
                quantity=quantity,
                price=price,
                position_side=position_side.value.upper() if position_side else 'BOTH',
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
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """
        取消订单
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            
        Returns:
            是否取消成功
        """
        try:
            self.client.cancel_order(symbol, order_id=int(order_id))
            logger.info(f"订单已取消", symbol=symbol, order_id=order_id)
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
            
            # 止损单方向与持仓方向相反
            side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY
            
            order = self.client.create_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type='STOP_MARKET',
                quantity=quantity,
                stop_price=stop_price,
                position_side=position_side.value.upper(),
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
            
            # 止盈单方向与持仓方向相反
            side = OrderSide.SELL if position_side == PositionSide.LONG else OrderSide.BUY
            
            order = self.client.create_order(
                symbol=symbol,
                side=side.value.upper(),
                order_type='TAKE_PROFIT_MARKET',
                quantity=quantity,
                stop_price=take_profit_price,
                position_side=position_side.value.upper(),
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
            
            return self.create_market_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                position_side=position_side,
                reduce_only=True
            )
            
        except Exception as e:
            logger.error(f"平仓失败: {e}", symbol=symbol, position_side=position_side)
            return OrderResult(success=False, error=str(e))
    
    def close(self):
        """关闭连接"""
        if self.client:
            self.client.close()

