"""
币安市场数据实现
通过 BinanceFuturesClient 获取市场数据、K线、资金费率等
创建时间: 2025-11-01
"""
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from datetime import datetime

from ...utils.logging import get_logger
from ...utils.exceptions import (
    DataFetchException,
    RateLimitException,
)

if TYPE_CHECKING:
    from .client import BinanceFuturesClient

logger = get_logger(__name__)


class BinanceMarketData:
    """币安期货市场数据获取器"""
    
    # K线时间周期映射
    TIMEFRAME_MAP = {
        '1m': '1m', '3m': '3m', '5m': '5m', '15m': '15m', '30m': '30m',
        '1h': '1h', '2h': '2h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
        '1d': '1d', '3d': '3d', '1w': '1w', '1M': '1M'
    }
    
    def __init__(self, client: 'BinanceFuturesClient'):
        """
        初始化币安市场数据获取器
        
        Args:
            client: BinanceFuturesClient 实例
        """
        self.client = client
        logger.info("成功初始化币安市场数据获取器")
    
    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        """
        标准化交易对格式
        BTC/USDT 或 BTC/USDT:USDT -> BTCUSDT
        """
        return symbol.replace('/', '').replace(':USDT', '').replace(':usdt', '')
    
    def get_klines(
        self, 
        symbol: str, 
        interval: str = '1h', 
        limit: int = 100,
        since: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        # 获取K线数据
        try:
            binance_symbol = self.normalize_symbol(symbol)
            
            # 验证时间周期
            if interval not in self.TIMEFRAME_MAP:
                raise ValueError(f"不支持的时间周期: {interval}")
            
            # 调用 client 的公开方法
            data = self.client.get_klines(
                symbol=binance_symbol,
                interval=self.TIMEFRAME_MAP[interval],
                start_time=since,
                limit=min(limit, 1500)
            )
            
            # 转换为标准格式
            klines = []
            for candle in data:
                klines.append({
                    'timestamp': int(candle[0]),
                    'open': float(candle[1]),
                    'high': float(candle[2]),
                    'low': float(candle[3]),
                    'close': float(candle[4]),
                    'volume': float(candle[5])
                })
            
            logger.debug(
                "成功获取K线数据",
                symbol=symbol,
                interval=interval,
                count=len(klines)
            )
            return klines
            
        except (RateLimitException, DataFetchException):
            raise
        except Exception as e:
            error_msg = f"获取K线数据失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol, interval=interval)
            raise DataFetchException(error_msg, details={"symbol": symbol, "interval": interval}) from e
    
    def get_order_book(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        # 获取订单簿数据
        try:
            binance_symbol = self.normalize_symbol(symbol)
            
            # 限制值必须是币安支持的值
            valid_limits = [5, 10, 20, 50, 100, 500, 1000]
            limit = min(valid_limits, key=lambda x: abs(x - limit))
            
            # 调用 client 的公开方法
            data = self.client.get_depth(symbol=binance_symbol, limit=limit)
            
            # 提取最佳买卖价
            best_bid = float(data['bids'][0][0]) if data.get('bids') and len(data['bids']) > 0 else None
            best_ask = float(data['asks'][0][0]) if data.get('asks') and len(data['asks']) > 0 else None
            
            result = {
                'symbol': symbol,
                'bid': best_bid,
                'ask': best_ask,
                'bids': [[float(price), float(qty)] for price, qty in data.get('bids', [])[:limit]],
                'asks': [[float(price), float(qty)] for price, qty in data.get('asks', [])[:limit]],
                'timestamp': int(data.get('T', datetime.now().timestamp() * 1000))
            }
            
            logger.debug("成功获取订单簿", symbol=symbol, bid=result['bid'], ask=result['ask'])
            return result
            
        except (RateLimitException, DataFetchException):
            logger.debug(f"获取订单簿失败（可能是测试网限制）", symbol=symbol)
            return {
                'symbol': symbol, 
                'bid': None, 
                'ask': None, 
                'bids': [], 
                'asks': [], 
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
        except Exception as e:
            logger.debug(f"获取订单簿失败: {e}", symbol=symbol)
            return {
                'symbol': symbol, 
                'bid': None, 
                'ask': None, 
                'bids': [], 
                'asks': [], 
                'timestamp': int(datetime.now().timestamp() * 1000)
            }
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        # 获取24小时价格变动统计
        try:
            binance_symbol = self.normalize_symbol(symbol)
            
            # 调用 client 的公开方法
            data = self.client.get_ticker_24hr(symbol=binance_symbol)
            
            # 解析数据
            last_price = float(data.get('lastPrice', 0))
            open_price = float(data.get('openPrice', 0))
            
            # 计算涨跌幅
            change = None
            percentage = None
            if last_price and open_price:
                change = last_price - open_price
                percentage = (change / open_price) * 100
            
            result = {
                'symbol': symbol,
                'last': last_price,
                'bid': float(data.get('bidPrice')) if data.get('bidPrice') else None,
                'ask': float(data.get('askPrice')) if data.get('askPrice') else None,
                'high': float(data.get('highPrice')) if data.get('highPrice') else None,
                'low': float(data.get('lowPrice')) if data.get('lowPrice') else None,
                'volume': float(data.get('volume')) if data.get('volume') else None,
                'change': change,
                'percentage': round(percentage, 2) if percentage else None,
                'timestamp': int(data.get('closeTime', datetime.now().timestamp() * 1000))
            }
            
            # 如果没有bid/ask，从订单簿补充
            if result['bid'] is None or result['ask'] is None:
                try:
                    orderbook = self.get_order_book(symbol, limit=1)
                    if result['bid'] is None and orderbook.get('bid'):
                        result['bid'] = orderbook['bid']
                    if result['ask'] is None and orderbook.get('ask'):
                        result['ask'] = orderbook['ask']
                except Exception as e:
                    logger.debug(f"获取订单簿补充bid/ask失败: {e}")
            
            logger.debug("成功获取实时行情", symbol=symbol, price=result['last'])
            return result
            
        except (RateLimitException, DataFetchException):
            raise
        except Exception as e:
            error_msg = f"获取实时行情失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol)
            raise DataFetchException(error_msg, details={"symbol": symbol}) from e
    
    def get_symbols(self, quote: str = 'USDT', active_only: bool = True) -> List[Dict[str, Any]]:
        # 获取交易对列表
        try:
            # 调用 client 的公开方法
            data = self.client.get_exchange_info()
            
            symbols = []
            for symbol_info in data.get('symbols', []):
                # 过滤条件
                if active_only and symbol_info.get('status') != 'TRADING':
                    continue
                
                if quote and symbol_info.get('quoteAsset') != quote:
                    continue
                
                symbols.append({
                    'symbol': f"{symbol_info['baseAsset']}/{symbol_info['quoteAsset']}",
                    'base': symbol_info['baseAsset'],
                    'quote': symbol_info['quoteAsset'],
                    'active': symbol_info.get('status') == 'TRADING'
                })
            
            logger.info("成功获取交易对列表", quote=quote, count=len(symbols))
            return symbols
            
        except (RateLimitException, DataFetchException):
            raise
        except Exception as e:
            error_msg = f"获取交易对列表失败: {str(e)}"
            logger.exception(error_msg, quote=quote)
            raise DataFetchException(error_msg, details={"quote": quote}) from e
    
    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        # 获取资金费率
        try:
            binance_symbol = self.normalize_symbol(symbol)
            
            # 调用 client 的公开方法
            data = self.client.get_premium_index(symbol=binance_symbol)
            
            result = {
                'symbol': symbol,
                'funding_rate': float(data.get('lastFundingRate', 0)) if data.get('lastFundingRate') else None,
                'next_funding_time': int(data.get('nextFundingTime', 0)) if data.get('nextFundingTime') else None,
                'timestamp': int(data.get('time', datetime.now().timestamp() * 1000))
            }
            
            logger.debug(
                "成功获取资金费率",
                symbol=symbol,
                funding_rate=result['funding_rate']
            )
            return result
            
        except (RateLimitException, DataFetchException):
            raise
        except Exception as e:
            error_msg = f"获取资金费率失败"
            logger.exception(error_msg, symbol=symbol)
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
    
    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        # 获取持仓量
        try:
            binance_symbol = self.normalize_symbol(symbol)
            
            # 调用 client 的公开方法
            data = self.client.get_open_interest(symbol=binance_symbol)
            
            result = {
                'symbol': symbol,
                'open_interest': float(data.get('openInterest', 0)) if data.get('openInterest') else None,
                'timestamp': int(data.get('time', datetime.now().timestamp() * 1000))
            }
            
            logger.debug(
                "成功获取持仓量",
                symbol=symbol,
                open_interest=result['open_interest']
            )
            return result
            
        except (RateLimitException, DataFetchException):
            raise
        except Exception as e:
            error_msg = f"获取持仓量失败"
            logger.exception(error_msg, symbol=symbol)
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e

