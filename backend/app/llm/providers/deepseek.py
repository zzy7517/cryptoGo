"""
DeepSeek LLM Provider - DeepSeek 大语言模型实现
创建时间: 2025-11-12
"""
from openai import OpenAI
from typing import Dict, List, Optional

from ..client import LLMBase
from ...utils.config import settings
from ...utils.logging import get_logger
from ...utils.exceptions import ConfigurationException

logger = get_logger(__name__)


class DeepSeekLLM(LLMBase):
    """DeepSeek LLM 实现"""
    
    def __init__(self):
        """初始化 DeepSeek 客户端"""
        super().__init__()
        
        api_key = self._get_api_key()
        base_url = self._get_base_url()
        self.model = self._get_model()
        
        if not api_key:
            error_msg = "未配置 DEEPSEEK_API_KEY，请在 .env 文件中设置"
            logger.error(error_msg)
            raise ConfigurationException(error_msg, error_code="MISSING_API_KEY")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        logger.info(
            "deepseek llm initialized",
            model=self.model,
            base_url=base_url
        )
    
    def _get_api_key(self) -> Optional[str]:
        """获取 DeepSeek API Key"""
        return settings.DEEPSEEK_API_KEY
    
    def _get_base_url(self) -> str:
        """获取 DeepSeek API Base URL"""
        return settings.DEEPSEEK_BASE_URL
    
    def _get_model(self) -> str:
        """获取 DeepSeek 模型名称"""
        return settings.DEEPSEEK_MODEL
    
    def chat(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.1,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        调用 DeepSeek API 进行对话
        
        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成token数
            
        Returns:
            LLM 返回的文本内容
        """
        try:
            logger.debug(
                "调用 deepseek llm",
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
            return content
            
        except Exception as e:
            error_msg = f"deepseek llm call failed: {str(e)}"
            logger.exception(error_msg)
            raise Exception(error_msg) from e
    
    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        return self.model

