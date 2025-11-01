"""
数据采集服务 - 交易所连接和数据获取
通过 CCXT 库连接交易所，获取市场数据、K 线、资金费率等信息
创建时间: 2025-10-27
"""
import ccxt
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
from functools import lru_cache

from app.utils.config import settings
from app.utils.logging import get_logger
from app.utils.exceptions import (
    UnsupportedFeatureException, 
    DataFetchException,
    RateLimitException,
    ConfigurationException
)

logger = get_logger(__name__)


class ExchangeConnector:
    """交易所连接器"""
    
    def __init__(self):
        """初始化交易所连接"""
        self.exchange_id = settings.EXCHANGE
        self.exchange = None
        self._initialize_exchange()
    
    def _initialize_exchange(self):
        """初始化交易所实例"""
        try:
            exchange_class = getattr(ccxt, self.exchange_id)
            
            # 配置交易所参数
            config = {
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # 合约交易
                },
                'timeout': 10000,  # 10秒超时
            }

            # 如果提供了 API 密钥，则添加认证信息
            if settings.BINANCE_API_KEY and settings.BINANCE_SECRET:
                config['apiKey'] = settings.BINANCE_API_KEY
                config['secret'] = settings.BINANCE_SECRET
                logger.debug("已配置交易所 API 认证")
            else:
                logger.warning("未配置交易所 API 密钥，仅可使用公开接口")
            
            # 添加代理配置
            if settings.HTTP_PROXY or settings.HTTPS_PROXY:
                config['proxies'] = {}
                if settings.HTTP_PROXY:
                    config['proxies']['http'] = settings.HTTP_PROXY
                if settings.HTTPS_PROXY:
                    config['proxies']['https'] = settings.HTTPS_PROXY
                logger.debug(f"使用代理: {config['proxies']}")

            self.exchange = exchange_class(config)

            logger.info(
                "成功初始化交易所",
                exchange=self.exchange_id,
                rate_limit=config['enableRateLimit']
            )
            
        except AttributeError:
            error_msg = f"不支持的交易所: {self.exchange_id}"
            logger.error(error_msg)
            raise ConfigurationException(error_msg, error_code="INVALID_EXCHANGE")
        except Exception as e:
            error_msg = f"初始化交易所失败: {str(e)}"
            logger.exception(error_msg)
            raise ConfigurationException(error_msg) from e
    
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
            symbol: 交易对，如 'BTC/USDT'
            interval: 时间周期 (1m, 5m, 15m, 1h, 4h, 1d)
            limit: 返回数据条数
            since: 起始时间戳（毫秒）
        
        Returns:
            K线数据列表
        """
        try:
            # 获取原始OHLCV数据
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=interval,
                limit=limit,
                since=since
            )
            
            # 转换为标准格式
            klines = []
            for candle in ohlcv:
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
                count=len(klines),
                time_range=f"{klines[0]['timestamp']} - {klines[-1]['timestamp']}" if klines else "empty"
            )
            return klines
            
        except ccxt.RateLimitExceeded as e:
            error_msg = f"API 请求频率超限: {str(e)}"
            logger.warning(error_msg, symbol=symbol, interval=interval)
            raise RateLimitException(error_msg) from e
        except ccxt.NetworkError as e:
            error_msg = f"网络错误"
            # 记录完整的异常信息和堆栈
            logger.exception(error_msg, symbol=symbol, interval=interval, exception_type=type(e).__name__)
            # 尝试获取更详细的错误信息
            if hasattr(e, 'response') and e.response:
                logger.error(f"API 响应详情", response=str(e.response)[:500])  # 限制长度避免日志过大
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol, "interval": interval}) from e
        except ccxt.BaseError as e:
            # CCXT 基础错误，可能包含 API 错误响应
            error_msg = f"交易所 API 错误"
            logger.exception(error_msg, symbol=symbol, interval=interval, exception_type=type(e).__name__)
            if hasattr(e, 'response') and e.response:
                logger.error(f"API 响应详情", response=str(e.response)[:500])  # 限制长度避免日志过大
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol, "interval": interval}) from e
        except Exception as e:
            error_msg = f"获取K线数据失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol, interval=interval, exception_type=type(e).__name__)
            raise DataFetchException(error_msg, details={"symbol": symbol, "interval": interval}) from e
    
    def get_order_book(self, symbol: str, limit: int = 5) -> Dict[str, Any]:
        """
        获取订单簿数据（更可靠的方式获取bid/ask）
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
            limit: 深度级别
        
        Returns:
            订单簿数据
        """
        try:
            orderbook = self.exchange.fetch_order_book(symbol, limit=limit)
            
            # 提取最佳买卖价
            best_bid = orderbook['bids'][0][0] if orderbook.get('bids') and len(orderbook['bids']) > 0 else None
            best_ask = orderbook['asks'][0][0] if orderbook.get('asks') and len(orderbook['asks']) > 0 else None
            
            result = {
                'symbol': symbol,
                'bid': float(best_bid) if best_bid else None,
                'ask': float(best_ask) if best_ask else None,
                'bids': [[float(price), float(amount)] for price, amount in orderbook.get('bids', [])[:limit]],
                'asks': [[float(price), float(amount)] for price, amount in orderbook.get('asks', [])[:limit]],
                'timestamp': int(orderbook.get('timestamp', datetime.now().timestamp() * 1000))
            }
            
            logger.debug("成功获取订单簿", symbol=symbol, bid=result['bid'], ask=result['ask'])
            return result
            
        except ccxt.NetworkError as e:
            error_msg = f"获取订单簿网络错误"
            logger.debug(error_msg, symbol=symbol, error=str(e))
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
        except ccxt.BaseError as e:
            # 可能是测试网限制或API错误，不抛出异常，返回None让调用者处理
            logger.debug(f"订单簿API错误（可能是测试网限制）: {str(e)[:100]}", symbol=symbol)
            return {'symbol': symbol, 'bid': None, 'ask': None, 'bids': [], 'asks': [], 'timestamp': int(datetime.now().timestamp() * 1000)}
        except Exception as e:
            error_msg = f"获取订单簿失败"
            logger.debug(error_msg, symbol=symbol, error=str(e)[:100])
            return {'symbol': symbol, 'bid': None, 'ask': None, 'bids': [], 'asks': [], 'timestamp': int(datetime.now().timestamp() * 1000)}
    
    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        获取实时行情数据（增强版 - 结合ticker和订单簿）
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
        
        Returns:
            行情数据字典
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            # 计算涨跌幅
            change = None
            percentage = None
            if ticker.get('last') and ticker.get('open'):
                change = ticker['last'] - ticker['open']
                percentage = (change / ticker['open']) * 100
            
            # 如果ticker没有bid/ask，从订单簿获取
            bid = float(ticker['bid']) if ticker.get('bid') else None
            ask = float(ticker['ask']) if ticker.get('ask') else None
            
            # 如果ticker中缺少bid/ask，尝试从订单簿获取
            if bid is None or ask is None:
                try:
                    orderbook = self.get_order_book(symbol, limit=1)
                    if bid is None and orderbook.get('bid'):
                        bid = orderbook['bid']
                    if ask is None and orderbook.get('ask'):
                        ask = orderbook['ask']
                    logger.debug(f"从订单簿补充了bid/ask数据: bid={bid}, ask={ask}")
                except Exception as e:
                    logger.warning(f"获取订单簿补充bid/ask失败: {e}")
            
            result = {
                'symbol': symbol,
                'last': float(ticker['last']) if ticker.get('last') else 0.0,
                'bid': bid,
                'ask': ask,
                'high': float(ticker['high']) if ticker.get('high') else None,
                'low': float(ticker['low']) if ticker.get('low') else None,
                'volume': float(ticker['baseVolume']) if ticker.get('baseVolume') else None,
                'change': change,
                'percentage': round(percentage, 2) if percentage else None,
                'timestamp': int(ticker['timestamp']) if ticker.get('timestamp') else int(datetime.now().timestamp() * 1000)
            }
            
            logger.debug("成功获取实时行情", symbol=symbol, price=result['last'], bid=result.get('bid'), ask=result.get('ask'))
            return result
            
        except ccxt.RateLimitExceeded as e:
            error_msg = f"API 请求频率超限: {str(e)}"
            logger.warning(error_msg, symbol=symbol)
            raise RateLimitException(error_msg) from e
        except ccxt.NetworkError as e:
            error_msg = f"网络错误"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            if hasattr(e, 'response') and e.response:
                logger.error(f"API 响应详情", response=str(e.response)[:500])
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
        except ccxt.BaseError as e:
            error_msg = f"交易所 API 错误"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            if hasattr(e, 'response') and e.response:
                logger.error(f"API 响应详情", response=str(e.response)[:500])
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
        except Exception as e:
            error_msg = f"获取实时行情失败: {str(e)}"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            raise DataFetchException(error_msg, details={"symbol": symbol}) from e
    
    def get_symbols(self, quote: str = 'USDT', active_only: bool = True) -> List[Dict[str, Any]]:
        """
        获取交易对列表
        
        Args:
            quote: 计价货币，如 'USDT'
            active_only: 是否只返回活跃的交易对
        
        Returns:
            交易对列表
        """
        try:
            markets = self.exchange.load_markets()
            
            symbols = []
            for market_id, market in markets.items():
                # 过滤条件
                if active_only and not market.get('active', True):
                    continue
                
                if quote and market.get('quote') != quote:
                    continue
                
                symbols.append({
                    'symbol': market['symbol'],
                    'base': market['base'],
                    'quote': market['quote'],
                    'active': market.get('active', True)
                })
            
            logger.info("成功获取交易对列表", quote=quote, count=len(symbols))
            return symbols
            
        except Exception as e:
            error_msg = f"获取交易对列表失败: {str(e)}"
            logger.exception(error_msg, quote=quote)
            raise DataFetchException(error_msg, details={"quote": quote}) from e
    
    def get_funding_rate(self, symbol: str) -> Dict[str, Any]:
        """
        获取资金费率（合约市场）
        
        Args:
            symbol: 交易对，如 'BTC/USDT:USDT'
        
        Returns:
            资金费率数据
        """
        # 检查交易所是否支持资金费率
        if not hasattr(self.exchange, 'fetch_funding_rate'):
            error_msg = f"{self.exchange_id} 不支持资金费率查询"
            logger.warning(error_msg, exchange=self.exchange_id, symbol=symbol)
            raise UnsupportedFeatureException(
                error_msg,
                error_code="UNSUPPORTED_FUNDING_RATE",
                details={"exchange": self.exchange_id, "feature": "funding_rate"}
            )
        
        try:
            # 获取资金费率
            funding_rate = self.exchange.fetch_funding_rate(symbol)
            
            result = {
                'symbol': symbol,
                'funding_rate': float(funding_rate.get('fundingRate', 0)) if funding_rate.get('fundingRate') else None,
                'next_funding_time': int(funding_rate.get('fundingTimestamp', 0)) if funding_rate.get('fundingTimestamp') else None,
                'timestamp': int(funding_rate.get('timestamp', datetime.now().timestamp() * 1000))
            }
            
            logger.debug(
                "成功获取资金费率",
                symbol=symbol,
                funding_rate=result['funding_rate'],
                next_funding=result['next_funding_time']
            )
            return result
            
        except UnsupportedFeatureException:
            raise
        except ccxt.NetworkError as e:
            error_msg = f"获取资金费率网络错误"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            if hasattr(e, 'response') and e.response:
                logger.error(f"API 响应详情", response=str(e.response)[:500])
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
        except ccxt.BaseError as e:
            error_msg = f"获取资金费率 API 错误"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            if hasattr(e, 'response') and e.response:
                logger.error(f"API 响应详情", response=str(e.response)[:500])
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
        except Exception as e:
            error_msg = f"获取资金费率失败"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
    
    def get_open_interest(self, symbol: str) -> Dict[str, Any]:
        """
        获取持仓量（合约市场）
        
        Args:
            symbol: 交易对，如 'BTC/USDT:USDT'
        
        Returns:
            持仓量数据
        """
        # 检查交易所是否支持持仓量查询
        if not hasattr(self.exchange, 'fetch_open_interest'):
            error_msg = f"{self.exchange_id} 不支持持仓量查询"
            logger.warning(error_msg, exchange=self.exchange_id, symbol=symbol)
            raise UnsupportedFeatureException(
                error_msg,
                error_code="UNSUPPORTED_OPEN_INTEREST",
                details={"exchange": self.exchange_id, "feature": "open_interest"}
            )
        
        try:
            # 获取持仓量
            open_interest = self.exchange.fetch_open_interest(symbol)
            
            # CCXT 返回的字段是 openInterestAmount，不是 openInterest
            oi_value = open_interest.get('openInterestAmount') or open_interest.get('openInterest')
            
            result = {
                'symbol': symbol,
                'open_interest': float(oi_value) if oi_value is not None else None,
                'timestamp': int(open_interest.get('timestamp', datetime.now().timestamp() * 1000))
            }
            
            logger.debug(
                "成功获取持仓量",
                symbol=symbol,
                open_interest=result['open_interest']
            )
            return result
            
        except UnsupportedFeatureException:
            raise
        except ccxt.NetworkError as e:
            error_msg = f"获取持仓量网络错误"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            if hasattr(e, 'response') and e.response:
                logger.error(f"API 响应详情", response=str(e.response)[:500])
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
        except ccxt.BaseError as e:
            error_msg = f"获取持仓量 API 错误"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            if hasattr(e, 'response') and e.response:
                logger.error(f"API 响应详情", response=str(e.response)[:500])
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e
        except Exception as e:
            error_msg = f"获取持仓量失败"
            logger.exception(error_msg, symbol=symbol, exception_type=type(e).__name__)
            raise DataFetchException(f"{error_msg}: {str(e)}", details={"symbol": symbol}) from e


@lru_cache(maxsize=1)
def get_exchange_connector() -> ExchangeConnector:
    """
    获取交易所连接器单例
    
    使用 lru_cache 确保只创建一个实例，线程安全
    """
    return ExchangeConnector()

