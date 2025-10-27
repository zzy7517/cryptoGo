"""
数据采集服务 - 交易所连接和数据获取
"""
import ccxt
from typing import List, Dict, Optional, Any
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


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
                    'defaultType': 'spot',  # 现货交易
                }
            }
            
            # 如果提供了 API 密钥，则添加认证信息
            if settings.BINANCE_API_KEY and settings.BINANCE_SECRET:
                config['apiKey'] = settings.BINANCE_API_KEY
                config['secret'] = settings.BINANCE_SECRET
            
            # 如果使用测试网
            if settings.BINANCE_TESTNET and self.exchange_id == 'binance':
                config['options']['defaultType'] = 'future'
                config['urls'] = {
                    'api': {
                        'public': 'https://testnet.binancefuture.com/fapi/v1',
                        'private': 'https://testnet.binancefuture.com/fapi/v1',
                    }
                }
            
            self.exchange = exchange_class(config)
            logger.info(f"成功初始化交易所: {self.exchange_id}")
            
        except Exception as e:
            logger.error(f"初始化交易所失败: {str(e)}")
            raise
    
    def get_klines(
        self, 
        symbol: str = None, 
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
        if symbol is None:
            symbol = settings.DEFAULT_SYMBOL
        
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
                    'timestamp': int(candle[0]),  # 时间戳
                    'open': float(candle[1]),      # 开盘价
                    'high': float(candle[2]),      # 最高价
                    'low': float(candle[3]),       # 最低价
                    'close': float(candle[4]),     # 收盘价
                    'volume': float(candle[5])     # 成交量
                })
            
            logger.info(f"成功获取 {symbol} {interval} K线数据，共 {len(klines)} 条")
            return klines
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {str(e)}")
            raise
    
    def get_ticker(self, symbol: str = None) -> Dict[str, Any]:
        """
        获取实时行情数据
        
        Args:
            symbol: 交易对，如 'BTC/USDT'
        
        Returns:
            行情数据字典
        """
        if symbol is None:
            symbol = settings.DEFAULT_SYMBOL
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            # 计算涨跌幅
            change = None
            percentage = None
            if ticker.get('last') and ticker.get('open'):
                change = ticker['last'] - ticker['open']
                percentage = (change / ticker['open']) * 100
            
            result = {
                'symbol': symbol,
                'last': float(ticker['last']) if ticker.get('last') else 0.0,
                'bid': float(ticker['bid']) if ticker.get('bid') else None,
                'ask': float(ticker['ask']) if ticker.get('ask') else None,
                'high': float(ticker['high']) if ticker.get('high') else None,
                'low': float(ticker['low']) if ticker.get('low') else None,
                'volume': float(ticker['baseVolume']) if ticker.get('baseVolume') else None,
                'change': change,
                'percentage': round(percentage, 2) if percentage else None,
                'timestamp': int(ticker['timestamp']) if ticker.get('timestamp') else int(datetime.now().timestamp() * 1000)
            }
            
            logger.info(f"成功获取 {symbol} 实时行情")
            return result
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {str(e)}")
            raise
    
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
            
            logger.info(f"成功获取交易对列表，共 {len(symbols)} 个")
            return symbols
            
        except Exception as e:
            logger.error(f"获取交易对列表失败: {str(e)}")
            raise
    
    def get_market_stats(self, symbol: str = None) -> Dict[str, Any]:
        """
        获取市场统计数据（24h数据）
        
        Args:
            symbol: 交易对
        
        Returns:
            市场统计数据
        """
        if symbol is None:
            symbol = settings.DEFAULT_SYMBOL
        
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            
            # 计算涨跌
            change_24h = None
            change_percentage_24h = None
            if ticker.get('last') and ticker.get('open'):
                change_24h = ticker['last'] - ticker['open']
                change_percentage_24h = (change_24h / ticker['open']) * 100
            
            stats = {
                'symbol': symbol,
                'price': float(ticker['last']) if ticker.get('last') else 0.0,
                'high_24h': float(ticker['high']) if ticker.get('high') else 0.0,
                'low_24h': float(ticker['low']) if ticker.get('low') else 0.0,
                'volume_24h': float(ticker['baseVolume']) if ticker.get('baseVolume') else 0.0,
                'change_24h': change_24h if change_24h else 0.0,
                'change_percentage_24h': round(change_percentage_24h, 2) if change_percentage_24h else 0.0,
                'timestamp': int(ticker['timestamp']) if ticker.get('timestamp') else int(datetime.now().timestamp() * 1000)
            }
            
            logger.info(f"成功获取 {symbol} 市场统计数据")
            return stats
            
        except Exception as e:
            logger.error(f"获取市场统计数据失败: {str(e)}")
            raise


# 全局交易所连接器实例
_exchange_connector: Optional[ExchangeConnector] = None


def get_exchange_connector() -> ExchangeConnector:
    """获取交易所连接器单例"""
    global _exchange_connector
    if _exchange_connector is None:
        _exchange_connector = ExchangeConnector()
    return _exchange_connector

