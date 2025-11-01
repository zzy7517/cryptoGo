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
from app.utils.logging import get_logger

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
        """
        初始化币安期货客户端
        
        Args:
            api_key: API 密钥
            api_secret: API 密钥
            testnet: 是否使用测试网
            proxies: 代理配置，如 {"http://": "http://127.0.0.1:7897", "https://": "http://127.0.0.1:7897"}
            timeout: 请求超时时间（秒）
        """
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
        """
        生成签名
        
        Args:
            params: 请求参数
            
        Returns:
            签名字符串
        """
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
        """
        发送 HTTP 请求
        
        Args:
            method: HTTP 方法 (GET, POST, PUT, DELETE)
            endpoint: API 端点
            signed: 是否需要签名
            **kwargs: 其他参数 (params, data, json)
            
        Returns:
            响应数据
            
        Raises:
            Exception: 请求失败时抛出异常
        """
        url = f"{self.base_url}{endpoint}"
        
        # 如果需要签名
        if signed:
            params = kwargs.get('params', {})
            params['timestamp'] = int(time.time() * 1000)
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
            logger.error(
                f"HTTP 错误: {e.response.status_code}",
                endpoint=endpoint,
                response=e.response.text
            )
            raise
        except Exception as e:
            logger.error(f"请求失败: {str(e)}", endpoint=endpoint)
            raise
    
    # ==================== 账户相关 API ====================
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息 (V2)
        GET /fapi/v2/account
        
        Returns:
            账户信息
        """
        return self._request('GET', '/fapi/v2/account', signed=True)
    
    def get_account_balance(self) -> List[Dict[str, Any]]:
        """
        获取账户余额 (V2)
        GET /fapi/v2/balance
        
        Returns:
            余额列表
        """
        return self._request('GET', '/fapi/v2/balance', signed=True)
    
    def get_position_risk(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取持仓信息 (V2)
        GET /fapi/v2/positionRisk
        
        Args:
            symbol: 交易对（可选，如 BTCUSDT）
            
        Returns:
            持仓列表
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        return self._request('GET', '/fapi/v2/positionRisk', signed=True, params=params)
    
    def get_account_trades(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        from_id: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        获取账户交易历史
        GET /fapi/v1/userTrades
        
        Args:
            symbol: 交易对
            start_time: 起始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            from_id: 从哪个 TradeId 开始返回
            limit: 返回数量，默认 500，最大 1000
            
        Returns:
            交易历史列表
        """
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
    
    def get_income_history(
        self,
        symbol: Optional[str] = None,
        income_type: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        获取收入历史
        GET /fapi/v1/income
        
        Args:
            symbol: 交易对（可选）
            income_type: 收入类型，如 TRANSFER, REALIZED_PNL, FUNDING_FEE 等
            start_time: 起始时间戳（毫秒）
            end_time: 结束时间戳（毫秒）
            limit: 返回数量，默认 100，最大 1000
            
        Returns:
            收入历史列表
        """
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
            position_side: 持仓方向，BOTH, LONG, SHORT（双向持仓模式下使用）
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
            params['quantity'] = quantity
        if price:
            params['price'] = price
        if time_in_force:
            params['timeInForce'] = time_in_force
        if reduce_only:
            params['reduceOnly'] = 'true'
        if stop_price:
            params['stopPrice'] = stop_price
        
        # 添加其他参数
        params.update(kwargs)
        
        logger.info(
            f"创建订单: {symbol} {side} {order_type}",
            quantity=quantity,
            price=price
        )
        
        return self._request('POST', '/fapi/v1/order', signed=True, params=params)
    
    def cancel_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        取消订单
        DELETE /fapi/v1/order
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            orig_client_order_id: 客户端订单ID
            
        Returns:
            取消结果
        """
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return self._request('DELETE', '/fapi/v1/order', signed=True, params=params)
    
    def cancel_all_orders(self, symbol: str) -> Dict[str, Any]:
        """
        取消所有订单
        DELETE /fapi/v1/allOpenOrders
        
        Args:
            symbol: 交易对
            
        Returns:
            取消结果
        """
        params = {'symbol': symbol}
        return self._request('DELETE', '/fapi/v1/allOpenOrders', signed=True, params=params)
    
    def get_order(
        self,
        symbol: str,
        order_id: Optional[int] = None,
        orig_client_order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        查询订单
        GET /fapi/v1/order
        
        Args:
            symbol: 交易对
            order_id: 订单ID
            orig_client_order_id: 客户端订单ID
            
        Returns:
            订单信息
        """
        params = {'symbol': symbol}
        if order_id:
            params['orderId'] = order_id
        if orig_client_order_id:
            params['origClientOrderId'] = orig_client_order_id
        
        return self._request('GET', '/fapi/v1/order', signed=True, params=params)
    
    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查询当前挂单
        GET /fapi/v1/openOrders
        
        Args:
            symbol: 交易对（可选，不传则返回所有）
            
        Returns:
            挂单列表
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', '/fapi/v1/openOrders', signed=True, params=params)
    
    # ==================== 杠杆和保证金相关 API ====================
    
    def change_leverage(self, symbol: str, leverage: int) -> Dict[str, Any]:
        """
        调整杠杆
        POST /fapi/v1/leverage
        
        Args:
            symbol: 交易对
            leverage: 杠杆倍数，1-125
            
        Returns:
            调整结果
        """
        params = {
            'symbol': symbol,
            'leverage': leverage
        }
        return self._request('POST', '/fapi/v1/leverage', signed=True, params=params)
    
    def change_margin_type(self, symbol: str, margin_type: str) -> Dict[str, Any]:
        """
        变更保证金模式
        POST /fapi/v1/marginType
        
        Args:
            symbol: 交易对
            margin_type: 保证金模式，ISOLATED（逐仓）或 CROSSED（全仓）
            
        Returns:
            变更结果
        """
        params = {
            'symbol': symbol,
            'marginType': margin_type
        }
        return self._request('POST', '/fapi/v1/marginType', signed=True, params=params)
    
    def get_leverage_bracket(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取杠杆分层标准
        GET /fapi/v1/leverageBracket
        
        Args:
            symbol: 交易对（可选）
            
        Returns:
            杠杆分层信息
        """
        params = {}
        if symbol:
            params['symbol'] = symbol
        
        return self._request('GET', '/fapi/v1/leverageBracket', signed=True, params=params)
    
    # ==================== 市场数据 API（无需签名）====================
    
    def get_exchange_info(self) -> Dict[str, Any]:
        """
        获取交易规则和交易对信息
        GET /fapi/v1/exchangeInfo
        
        Returns:
            交易所信息
        """
        return self._request('GET', '/fapi/v1/exchangeInfo', signed=False)
    
    def get_ticker_price(self, symbol: Optional[str] = None) -> Any:
        """
        获取最新价格
        GET /fapi/v1/ticker/price
        
        Args:
            symbol: 交易对（可选，不传则返回所有）
            
        Returns:
            价格信息（单个或列表）
        """
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
    
    def ping(self) -> Dict[str, Any]:
        """
        测试连接
        GET /fapi/v1/ping
        
        Returns:
            空对象 {}
        """
        return self._request('GET', '/fapi/v1/ping', signed=False)
    
    def get_server_time(self) -> Dict[str, Any]:
        """
        获取服务器时间
        GET /fapi/v1/time
        
        Returns:
            服务器时间
        """
        return self._request('GET', '/fapi/v1/time', signed=False)
    
    def close(self):
        """关闭 HTTP 客户端"""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

