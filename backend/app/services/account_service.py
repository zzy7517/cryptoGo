"""
通用账户信息服务
与具体交易所无关，通过依赖注入使用任何交易所
使用工厂模式根据配置创建交易所实例
创建时间: 2025-11-01
"""
from typing import Dict, Any, List
from app.exchanges.base import AbstractExchange
from app.exchanges.factory import create_default_exchange
from app.utils.logging import get_logger

logger = get_logger(__name__)


class AccountService:
    """
    通用账户信息服务
    
    通过依赖注入接受任何交易所实现，不绑定特定交易所
    """

    def __init__(self, exchange: AbstractExchange):
        """
        初始化账户服务
        
        Args:
            exchange: 交易所实例（实现 AbstractExchange 接口）
        """
        self.exchange = exchange
        logger.info(f"账户服务初始化完成，使用交易所: {exchange.__class__.__name__}")

    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息
        
        Returns:
            账户信息字典，包含余额、权限等
        """
        try:
            return self.exchange.get_account_info()
        except Exception as e:
            logger.error(f"获取账户信息失败: {str(e)}")
            raise

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取持仓信息
        
        Returns:
            持仓列表，只返回有持仓的记录
        """
        try:
            return self.exchange.get_positions()
        except Exception as e:
            logger.error(f"获取持仓信息失败: {str(e)}")
            raise

    def get_account_summary(self) -> Dict[str, Any]:
        """
        获取账户摘要信息（账户信息 + 持仓信息）
        
        Returns:
            包含账户和持仓的完整信息
        """
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


# ==================== 工厂函数 ====================

def create_account_service() -> AccountService:
    """
    创建账户服务（从配置读取交易所类型）
    
    使用工厂模式根据配置自动创建对应的交易所实例
    
    Returns:
        配置好的 AccountService 实例
    """
    # 通过工厂创建交易所实例（自动从配置读取）
    exchange = create_default_exchange()
    
    # 返回服务实例
    return AccountService(exchange)


# ==================== 单例模式 ====================

_account_service_instance = None


def get_account_service() -> AccountService:
    """
    获取账户服务单例
    
    自动根据配置（settings.EXCHANGE）使用对应的交易所
    
    Returns:
        AccountService 实例
    """
    global _account_service_instance
    if _account_service_instance is None:
        _account_service_instance = create_account_service()
    return _account_service_instance


# ==================== 向后兼容 ====================

# 为了向后兼容，保留旧的命名
create_binance_account_service = create_account_service
BinanceAccountService = AccountService
get_binance_account_service = get_account_service


__all__ = [
    'AccountService',
    'create_account_service',
    'get_account_service',
    # 向后兼容
    'create_binance_account_service',
    'BinanceAccountService',
    'get_binance_account_service'
]

