"""
AI 引擎服务 - DeepSeek 集成
基于 DeepSeek API 的市场分析和交易决策引擎
修改时间: 2025-10-29 (添加会话支持)
"""
from openai import OpenAI
from typing import Dict, Any, Optional, List
from functools import lru_cache
from sqlalchemy.orm import Session
from decimal import Decimal

from ..utils.config import settings
from ..utils.logging import get_logger
from ..utils.exceptions import ConfigurationException
from ..repositories.ai_decision_repo import AIDecisionRepository

logger = get_logger(__name__)


class LLMService:
    def __init__(self):
        if not settings.DEEPSEEK_API_KEY:
            error_msg = "未配置 DEEPSEEK_API_KEY，请在 .env 文件中设置"
            logger.error(error_msg)
            raise ConfigurationException(error_msg, error_code="MISSING_API_KEY")
        
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_BASE_URL
        )
        self.model = settings.DEEPSEEK_MODEL
        
        logger.info(
            "成功初始化 AI 引擎",
            model=self.model,
            base_url=settings.DEEPSEEK_BASE_URL
        )
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        try:
            logger.debug(
                "调用 DeepSeek API",
                messages_count=len(messages),
                temperature=temperature
            )
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            content = response.choices[0].message.content

            logger.info(
                "DeepSeek API 调用成功",
            )
            
            return content
            
        except Exception as e:
            error_msg = f"DeepSeek API 调用失败: {str(e)}"
            logger.exception(error_msg)
            raise Exception(error_msg) from e

@lru_cache(maxsize=1)
def get_llm() -> LLMService:
    """
    获取 AI 引擎单例
    
    使用 lru_cache 确保只创建一个实例，线程安全
    """
    return LLMService()

