"""
数据采集服务 - 交易所市场数据获取的统一接口
使用工厂模式创建交易所实例，通过统一接口获取市场数据
创建时间: 2025-10-27
修改时间: 2025-11-01 - 重构为工厂模式，统一架构
"""
from functools import lru_cache

from ..exchanges.factory import ExchangeFactory
from ..exchanges.base import AbstractExchange


@lru_cache(maxsize=1)
def get_exchange() -> AbstractExchange:
    """
    获取交易所实例
    
    使用工厂模式创建交易所实例，支持：
    - 账户管理
    - 持仓查询
    - 订单执行
    - 市场数据获取
    
    Returns:
        交易所实例
    """
    return ExchangeFactory.create_exchange()

