"""
币安 USDS-M 期货 API 客户端
直接调用币安 API，支持 testnet/mainnet
创建时间: 2025-11-01
"""
import time
import hmac
import hashlib
from urllib.parse import urlencode
from typing import Dict, Any, List, Optional
import httpx
from ...utils.logging import get_logger

logger = get_logger(__name__)


class BinanceFuturesClient:
    """币安 USDS-M 期货 API 客户端"""
    
    # API 端点
    MAINNET_BASE_URL = "https://fapi.binance.com"
    TESTNET_BASE_URL = "https://demo-fapi.binance.com"  # Demo Trading
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False,
        proxies: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = self.TESTNET_BASE_URL if testnet else self.MAINNET_BASE_URL
        self.timeout = timeout
        
        # 创建 HTTP 客户端
        # httpx 使用 proxy 或 mounts 参数，不是 proxies
        client_kwargs = {
            'timeout': timeout,
            'headers': {
                'X-MBX-APIKEY': self.api_key
            }
        }
        
        # 添加代理配置（httpx 格式）
        if proxies:
            # httpx 需要使用 proxy 参数或 mounts
            # 简单情况：使用统一代理
            if 'https://' in proxies:
                client_kwargs['proxy'] = proxies['https://']
            elif 'http://' in proxies:
                client_kwargs['proxy'] = proxies['http://']
        
        self.client = httpx.Client(**client_kwargs)
        
        logger.info(
            f"币安期货客户端初始化成功",
            base_url=self.base_url,
            testnet=testnet,
            has_proxy=proxies is not None
        )
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        query_string = urlencode(params)
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _request(
        self,
        method: str,
        endpoint: str,
        signed: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        
        # 如果需要签名
        if signed:
            params = kwargs.get('params', {})
            params['timestamp'] = int(time.time() * 1000)
            # 添加 recvWindow 参数，允许 60 秒的时间窗口容忍度
            params['recvWindow'] = 60000
            params['signature'] = self._generate_signature(params)
            kwargs['params'] = params
        
        try:
            response = self.client.request(method, url, **kwargs)
            response.raise_for_status()
            
            # 币安 API 返回 JSON
            data = response.json()
            
            # 检查是否有错误
            if isinstance(data, dict) and 'code' in data and data['code'] != 200:
                error_msg = data.get('msg', 'Unknown error')
                logger.error(
                    f"API 错误: {error_msg}",
                    code=data.get('code'),
                    endpoint=endpoint
                )
                raise Exception(f"Binance API Error: {error_msg}")
            
            return data
            
        except httpx.HTTPStatusError as e:
            error_msg = e.response.text
            try:
                error_data = e.response.json()
                error_msg = error_data.get('msg', error_msg)
                logger.error(
                    f"HTTP 错误: {e.response.status_code} - {error_msg}",
                    endpoint=endpoint,
                    code=error_data.get('code'),
                    response=e.response.text
                )
            except:
                logger.error(
                    f"HTTP 错误: {e.response.status_code}",
                    endpoint=endpoint,
                    response=error_msg
                )
            raise
        except Exception as e:
            logger.error(f"请求失败: {str(e)}", endpoint=endpoint)
            raise
    
    # ==================== 账户相关 API ====================
    
    def get_account_info(self) -> Dict[str, Any]:
        return self._request('GET', '/fapi/v2/account', signed=True)
    
    # 获取账户余额 
    def get_account_balance(self) -> List[Dict[str, Any]]:
        return self._request('GET', '/fapi/v2/balance', signed=True)
    
    # 获取持仓信息
    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        GET /fapi/v3/positionRisk

        注意：只返回有持仓或有挂单的交易对

        Args:
            symbol: 交易对（可选），不传则返回所有

        Returns:
            持仓信息列表，包含以下字段：
            - symbol: 交易对
            - positionSide: 持仓方向（BOTH/LONG/SHORT）
            - positionAmt: 持仓数量
            - entryPrice: 开仓均价
            - breakEvenPrice: 盈亏平衡价
            - markPrice: 标记价格
            - unRealizedProfit: 未实现盈亏
            - liquidationPrice: 强平价格
            - isolatedMargin: 逐仓保证金
            - notional: 名义价值
            - marginAsset: 保证金资产
            - isolatedWallet: 逐仓钱包余额
            - initialMargin: 当前所需起始保证金
            - maintMargin: 维持保证金
            - positionInitialMargin: 持仓所需起始保证金
            - openOrderInitialMargin: 挂单所需起始保证金
            - adl: 自动减仓等级
            - updateTime: 更新时间
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/fapi/v3/positionRisk', signed=True, params=params)
    
    # 获取账户交易历史
    def get_account_trades(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        from_id: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        params = {
            'symbol': symbol,
            'limit': limit
        }
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        if from_id:
            params['fromId'] = from_id
        
        return self._request('GET', '/fapi/v1/userTrades', signed=True, params=params)
    
    # 获取收入历史
    def get_income_history(
        self,
        symbol: Optional[str] = None,
        income_type: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        params = {'limit': limit}
        if symbol:
            params['symbol'] = symbol
        if income_type:
            params['incomeType'] = income_type
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self._request('GET', '/fapi/v1/income', signed=True, params=params)
    
    # ==================== 交易相关 API ====================
    
    def create_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        position_side: str = "BOTH",
        time_in_force: Optional[str] = None,
        reduce_only: bool = False,
        stop_price: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        创建订单
        POST /fapi/v1/order
        
        Args:
            symbol: 交易对，如 BTCUSDT
            side: BUY 或 SELL
            order_type: 订单类型，如 LIMIT, MARKET, STOP, STOP_MARKET, TAKE_PROFIT, TAKE_PROFIT_MARKET
            quantity: 数量
            price: 价格（限价单必填）
            position_side: 持仓方向，LONG 或 SHORT（双向持仓模式）
            time_in_force: 有效方式，GTC, IOC, FOK（限价单必填）
            reduce_only: 只减仓
            stop_price: 触发价格（止损/止盈单必填）
            **kwargs: 其他参数
            
        Returns:
            订单信息
        """
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'positionSide': position_side,
        }
        
        if quantity:
            # 格式化数量为字符串，保留足够的小数位（最多8位）
            # 去除尾部的0，避免被Binance拒绝
            params['quantity'] = f"{quantity:.8f}".rstrip('0').rstrip('.')
        if price:
            # 格式化价格为字符串，保留足够的小数位（最多8位）
            params['price'] = f"{price:.8f}".rstrip('0').rstrip('.')
        if time_in_force:
            params['timeInForce'] = time_in_force
        if reduce_only:
            params['reduceOnly'] = 'true'
        if stop_price:
            # 格式化止损价格为字符串，保留足够的小数位（最多8位）
            params['stopPrice'] = f"{stop_price:.8f}".rstrip('0').rstrip('.')
        
        # 添加其他参数
        params.update(kwargs)
        
        logger.info(
            f"创建订单: {symbol} {side} {order_type}",
            quantity=quantity,
            price=price
        )
        
        return self._request('POST', '/fapi/v1/order', signed=True, params=params)
    
    # 取消订单
    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return self._request('DELETE', '/fapi/v1/order', signed=True, params=params)
    
    # 取消所有订单
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        params = {'symbol': symbol}
        return self._request('DELETE', '/fapi/v1/allOpenOrders', signed=True, params=params)
    
    # 查询订单
    def get_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return self._request('GET', '/fapi/v1/order', signed=True, params=params)
    
    # 查询当前挂单
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', '/fapi/v1/openOrders', signed=True, params=params)
    
    # ==================== 杠杆和保证金相关 API ====================
    
    # 调整杠杆
    def change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._request('POST', '/fapi/v1/leverage', signed=True, params=params)
    
    # 变更保证金模式
    def change_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        return self._request('POST', '/fapi/v1/marginType', signed=True, params=params)
    
    # 获取杠杆分层标准
    def get_leverage_bracket(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', '/fapi/v1/leverageBracket', signed=True, params=params)
    
    # ==================== 市场数据 API（无需签名）====================
    
    # 获取交易规则和交易对信息
    def get_exchange_info(self) -> Dict[str, Any]:
        return self._request('GET', '/fapi/v1/exchangeInfo', signed=False)
    
    # 获取最新价格
    def get_ticker_price(self, symbol: Optional[str] = None) -> Any:
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', '/fapi/v1/ticker/price', signed=False, params=params)
    
    def get_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500
    ) -> List[List]:
        """
        获取K线数据
        GET /fapi/v1/klines
        
        Args:
            symbol: 交易对
            interval: 时间间隔，如 1m, 5m, 15m, 1h, 4h, 1d
            start_time: 起始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            limit: 返回数量，默认 500，最大 1500
            
        Returns:
            K线数据列表
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        if start_time:
            params['startTime'] = start_time
        if end_time:
            params['endTime'] = end_time
        
        return self._request('GET', '/fapi/v1/klines', signed=False, params=params)
    
    # 获取订单簿深度
    def get_depth(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        params = {
            'symbol': symbol,
            'limit': limit
        }
        return self._request('GET', '/fapi/v1/depth', signed=False, params=params)
    
    # 获取24小时价格变动统计
    def get_ticker_24hr(self, symbol: str) -> Dict[str, Any]:
        params = {'symbol': symbol}
        return self._request('GET', '/fapi/v1/ticker/24hr', signed=False, params=params)
    
    # 获取资金费率
    def get_premium_index(self, symbol: str) -> Dict[str, Any]:
        params = {'symbol': symbol}
        return self._request('GET', '/fapi/v1/premiumIndex', signed=False, params=params)
    
    # 获取持仓量
    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        params = {'symbol': symbol}
        return self._request('GET', '/fapi/v1/openInterest', signed=False, params=params)
    
    # 获取服务器时间
    def get_server_time(self) -> Dict[str, Any]:
        return self._request('GET', '/fapi/v1/time', signed=False)
    
    # 关闭 HTTP 客户端
    def close(self):
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

