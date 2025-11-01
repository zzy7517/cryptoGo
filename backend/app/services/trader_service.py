"""
交易服务
使用工厂模式根据配置创建交易所实例，用于执行交易
创建时间: 2025-11-01
"""
from app.exchanges.base import AbstractExchange
from app.exchanges.factory import create_default_exchange
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ==================== 单例模式 ====================

_trader_instance = None


def get_trader() -> AbstractExchange:
    """
    获取交易器单例
    
    自动根据配置（settings.EXCHANGE）创建对应的交易所实例
    
    Returns:
        交易所实例（AbstractExchange）
    """
    global _trader_instance
    if _trader_instance is None:
        _trader_instance = create_default_exchange()
        logger.info(f"交易器创建成功: {_trader_instance.__class__.__name__}")
    return _trader_instance


def reset_trader():
    """
    重置交易器单例
    
    主要用于测试或需要重新初始化交易器时
    """
    global _trader_instance
    _trader_instance = None
    logger.info("交易器已重置")


# ==================== 向后兼容 ====================

# 为了向后兼容，提供旧的函数名
create_binance_trader_from_config = get_trader


__all__ = [
    'get_trader',
    'reset_trader',
    # 向后兼容
    'create_binance_trader_from_config'
]

