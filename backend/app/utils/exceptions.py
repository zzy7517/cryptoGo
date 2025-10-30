"""
自定义异常类
定义应用中使用的各类自定义异常，提供结构化的错误处理
创建时间: 2025-10-27
"""
from typing import Optional, Dict, Any


class CryptoGoException(Exception):
    """
    应用基础异常类
    
    所有自定义异常的基类
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，便于 API 响应"""
        return {
            "error_type": self.error_code,
            "message": self.message,
            "details": self.details
        }


class ExchangeException(CryptoGoException):
    """交易所相关异常"""
    pass


class UnsupportedFeatureException(ExchangeException):
    """
    交易所不支持的功能
    
    当请求的功能在当前交易所不可用时抛出
    """
    pass


class DataFetchException(ExchangeException):
    """
    数据获取失败
    
    当从交易所获取数据失败时抛出（网络错误、API 错误等）
    """
    pass


class RateLimitException(ExchangeException):
    """
    API 请求频率限制
    
    当触发交易所 API 频率限制时抛出
    """
    pass


class ValidationException(CryptoGoException):
    """
    数据验证异常
    
    当输入参数或数据验证失败时抛出
    """
    pass


class ConfigurationException(CryptoGoException):
    """
    配置异常
    
    当配置错误或缺少必要配置时抛出
    """
    pass


class BusinessException(CryptoGoException):
    """
    业务逻辑异常
    
    当业务逻辑验证失败时抛出（如会话状态错误、操作冲突等）
    """
    pass

