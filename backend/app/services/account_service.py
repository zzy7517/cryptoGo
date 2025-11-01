"""
通用账户信息服务
与具体交易所无关，通过依赖注入使用任何交易所
创建时间: 2025-11-01
修改时间: 2025-11-02 - 重构依赖关系，移除循环依赖
"""
from typing import Dict, Any, List, Optional
from ..exchanges.base import AbstractExchange
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AccountService:
    """
    通用账户服务

    可以通过两种方式使用：
    1. 传入交易所实例：AccountService(exchange)
    2. 使用单例模式：AccountService.get_instance() - 自动从工厂获取交易所
    """

    # 单例实例
    _instance: Optional['AccountService'] = None

    def __init__(self, exchange: AbstractExchange):
        """
        初始化账户服务

        Args:
            exchange: 交易所实例（实现 AbstractExchange 接口）
        """
        self.exchange = exchange
        logger.info(f"账户服务初始化完成，使用交易所: {exchange.__class__.__name__}")

    @classmethod
    def get_instance(cls) -> 'AccountService':
        """
        获取账户服务单例

        自动从 ExchangeFactory 获取交易所实例

        Returns:
            AccountService 实例
        """
        if cls._instance is None:
            from ..exchanges.factory import get_trader
            exchange = get_trader()
            cls._instance = cls(exchange)
            logger.info("账户服务单例创建成功")
        return cls._instance

    @classmethod
    def reset_instance(cls):
        """重置单例实例，主要用于测试"""
        cls._instance = None
        logger.info("账户服务单例已重置")

    def get_account_info(self) -> Dict[str, Any]:
        try:
            return self.exchange.get_account_info()
        except Exception as e:
            logger.error(f"获取账户信息失败: {str(e)}")
            raise

    def get_positions(self) -> List[Dict[str, Any]]:
        try:
            return self.exchange.get_positions()
        except Exception as e:
            logger.error(f"获取持仓信息失败: {str(e)}")
            raise

    # 获取账户摘要信息（账户信息 + 持仓信息）
    def get_account_summary(self) -> Dict[str, Any]:
        try:
            account_info = self.get_account_info()
            positions = self.get_positions()

            return {
                'account': account_info,
                'positions': positions,
                'positionsCount': len(positions)
            }

        except Exception as e:
            logger.error(f"获取账户摘要失败: {str(e)}")
            raise


__all__ = [
    'AccountService',
]

