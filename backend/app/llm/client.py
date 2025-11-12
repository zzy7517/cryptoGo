"""
LLM Client - 大语言模型客户端核心
包含基类定义和工厂实现
创建时间: 2025-11-12
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from functools import lru_cache

from ..utils.config import settings
from ..utils.logging import get_logger
from ..utils.exceptions import ConfigurationException

logger = get_logger(__name__)


class LLMBase(ABC):
    """LLM 抽象基类，定义所有 LLM 提供商需要实现的接口"""
    
    def __init__(self):
        """初始化 LLM 客户端"""
        self.client = None
        self.model = None
    
    @abstractmethod
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        调用 LLM 进行对话
        
        Args:
            messages: 消息列表，格式为 [{"role": "user/system/assistant", "content": "..."}]
            temperature: 温度参数，控制随机性
            max_tokens: 最大生成token数
            
        Returns:
            LLM 返回的文本内容
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        pass


class LLMFactory:
    """LLM 工厂类，根据配置创建对应的 LLM 实例"""
    
    _providers = {}
    
    @classmethod
    def register_provider(cls, name: str, provider_class):
        """
        注册 LLM 提供商
        
        Args:
            name: 提供商名称
            provider_class: 提供商类
        """
        cls._providers[name.lower()] = provider_class
        logger.debug(f"注册 LLM 提供商: {name}")
    
    @classmethod
    def create_llm(cls, provider: str = None) -> LLMBase:
        """
        创建 LLM 实例
        
        Args:
            provider: LLM 提供商名称，如果不指定则使用配置中的默认值
            
        Returns:
            LLM 实例
            
        Raises:
            ConfigurationException: 当提供商不支持时
        """
        if provider is None:
            provider = settings.LLM_PROVIDER
        
        provider = provider.lower()
        
        if provider not in cls._providers:
            error_msg = f"不支持的 LLM 提供商: {provider}，支持的提供商: {list(cls._providers.keys())}"
            logger.error(error_msg)
            raise ConfigurationException(error_msg, error_code="UNSUPPORTED_PROVIDER")
        
        llm_class = cls._providers[provider]
        logger.info(f"创建 {provider} LLM 实例")
        
        return llm_class()


@lru_cache(maxsize=1)
def get_llm() -> LLMBase:
    """
    获取 LLM 服务单例
    
    Returns:
        LLM 实例
    """
    return LLMFactory.create_llm()

