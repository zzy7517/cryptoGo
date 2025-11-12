"""
LLM Providers - 各种 LLM 提供商实现
"""
from ..client import LLMFactory
from .deepseek import DeepSeekLLM

# 自动注册所有提供商
LLMFactory.register_provider("deepseek", DeepSeekLLM)

__all__ = [
    'DeepSeekLLM',
]

