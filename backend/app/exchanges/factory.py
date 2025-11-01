"""
交易所工厂
根据配置创建对应的交易所实例
使用工厂模式，支持动态创建不同交易所
创建时间: 2025-11-01
"""
from typing import Dict, Any, Optional
from app.exchanges.base import AbstractExchange
from app.exchanges.binance import BinanceExchange
from app.utils.logging import get_logger
from app.utils.config import settings

logger = get_logger(__name__)


class ExchangeFactory:
    """
    交易所工厂类
    
    根据配置创建对应的交易所实例
    使用工厂模式，使得交易所可以根据配置动态切换
    """
    
    # 注册的交易所类型
    _exchanges = {
        'binance': BinanceExchange,
        # 未来可以添加更多交易所
        # 'okx': OKXExchange,
        # 'bybit': BybitExchange,
    }
    
    @classmethod
    def register_exchange(cls, name: str, exchange_class: type):
        """
        注册新的交易所类型
        
        Args:
            name: 交易所名称
            exchange_class: 交易所类
        """
        cls._exchanges[name] = exchange_class
        logger.info(f"注册交易所: {name}")
    
    @classmethod
    def create_exchange(
        cls,
        exchange_name: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        testnet: Optional[bool] = None,
        proxies: Optional[Dict[str, str]] = None
    ) -> AbstractExchange:
        """
        创建交易所实例
        
        Args:
            exchange_name: 交易所名称（如果为空则从配置读取）
            api_key: API 密钥（如果为空则从配置读取）
            api_secret: API 密钥（如果为空则从配置读取）
            testnet: 是否使用测试网（如果为空则从配置读取）
            proxies: 代理配置（如果为空则从配置读取）
            
        Returns:
            交易所实例
            
        Raises:
            ValueError: 如果交易所类型不支持
        """
        # 从配置读取默认值
        if exchange_name is None:
            exchange_name = settings.EXCHANGE.lower()
        
        if api_key is None:
            api_key = settings.BINANCE_API_KEY  # TODO: 根据交易所类型读取不同的配置
        
        if api_secret is None:
            api_secret = settings.BINANCE_SECRET
        
        if testnet is None:
            testnet = settings.BINANCE_TESTNET
        
        # 配置代理
        if proxies is None and (settings.HTTP_PROXY or settings.HTTPS_PROXY):
            proxies = {}
            if settings.HTTP_PROXY:
                proxies['http://'] = settings.HTTP_PROXY
            if settings.HTTPS_PROXY:
                proxies['https://'] = settings.HTTPS_PROXY
        
        # 检查交易所是否支持
        if exchange_name not in cls._exchanges:
            supported = ', '.join(cls._exchanges.keys())
            raise ValueError(
                f"不支持的交易所: {exchange_name}。"
                f"支持的交易所: {supported}"
            )
        
        # 创建交易所实例
        exchange_class = cls._exchanges[exchange_name]
        
        logger.info(
            f"创建交易所实例: {exchange_name}",
            testnet=testnet,
            has_proxy=proxies is not None
        )
        
        # 根据交易所类型创建实例
        if exchange_name == 'binance':
            return exchange_class(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet,
                proxies=proxies
            )
        # 未来添加其他交易所
        # elif exchange_name == 'okx':
        #     return exchange_class(api_key, api_secret, ...)
        else:
            # 默认使用标准构造函数
            return exchange_class(
                api_key=api_key,
                api_secret=api_secret,
                testnet=testnet
            )
    
    @classmethod
    def get_supported_exchanges(cls) -> list:
        """
        获取支持的交易所列表
        
        Returns:
            交易所名称列表
        """
        return list(cls._exchanges.keys())


# ==================== 便捷函数 ====================

def create_default_exchange() -> AbstractExchange:
    """
    创建默认交易所实例（从配置读取）
    
    Returns:
        交易所实例
    """
    return ExchangeFactory.create_exchange()


__all__ = ['ExchangeFactory', 'create_default_exchange']

