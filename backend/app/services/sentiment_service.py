"""
Sentiment Service - 情绪数据获取服务
提供市场情绪数据（Fear & Greed Index）
创建时间: 2025-11-12
"""
import aiohttp
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SentimentService:
    """市场情绪服务（单例模式，带缓存）"""
    
    # Fear & Greed Index API
    FEAR_GREED_API = "https://api.alternative.me/fng/"
    
    # 缓存
    _cache: Optional[Dict[str, Any]] = None
    _cache_time: Optional[datetime] = None
    _cache_duration = 3600  # 1小时缓存
    
    @classmethod
    async def get_fear_greed_index(cls) -> Dict[str, Any]:
        """
        获取恐惧贪婪指数（带缓存）
        
        Returns:
            恐惧贪婪指数数据
        """
        # 检查缓存
        now = datetime.now()
        if cls._cache and cls._cache_time:
            if (now - cls._cache_time).seconds < cls._cache_duration:
                logger.debug("📊 使用缓存的情绪数据")
                return cls._cache
        
        # 获取新数据
        try:
            logger.info("📊 获取 Fear & Greed Index...")
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    cls.FEAR_GREED_API,
                    params={"limit": 1},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        fg_list = data.get("data", [])
                        
                        if fg_list:
                            fg_data = fg_list[0]
                            result = {
                                "value": int(fg_data["value"]),
                                "classification": fg_data["value_classification"],
                                "timestamp": fg_data["timestamp"],
                                "available": True
                            }
                            
                            # 更新缓存
                            cls._cache = result
                            cls._cache_time = now
                            
                            logger.info(f"✅ Fear & Greed Index: {result['value']} ({result['classification']})")
                            return result
                    
                    logger.warning(f"⚠️ Fear & Greed API 返回状态码: {response.status}")
                    
        except asyncio.TimeoutError:
            logger.warning("⚠️ Fear & Greed API 请求超时")
        except Exception as e:
            logger.warning(f"⚠️ 获取 Fear & Greed Index 失败: {e}")
        
        # 失败时返回中性值
        return {
            "value": 50,
            "classification": "Neutral",
            "timestamp": int(now.timestamp()),
            "available": False,
            "error": "Failed to fetch data"
        }
    
    @classmethod
    def interpret_fear_greed(cls, value: int) -> str:
        """
        解释恐惧贪婪指数
        
        Args:
            value: 指数值 0-100
            
        Returns:
            解释文本
        """
        if value <= 20:
            return "极度恐慌 - 市场可能存在超卖机会，但需谨慎抄底"
        elif value <= 40:
            return "恐慌 - 市场情绪偏向谨慎，投资者较为保守"
        elif value <= 60:
            return "中性 - 市场情绪相对平衡，处于观望状态"
        elif value <= 80:
            return "贪婪 - 市场情绪偏向乐观，注意风险控制"
        else:
            return "极度贪婪 - 市场过度乐观，高度警惕回调风险"
    
    @classmethod
    def get_trading_suggestion(cls, value: int) -> str:
        """
        基于恐惧贪婪指数给出交易建议
        
        Args:
            value: 指数值 0-100
            
        Returns:
            交易建议
        """
        if value <= 20:
            return "可考虑逢低布局，但需设置严格止损"
        elif value <= 40:
            return "适合小仓位试探，关注超跌反弹机会"
        elif value <= 60:
            return "保持正常交易策略"
        elif value <= 80:
            return "注意风险控制，考虑适当减仓或止盈"
        else:
            return "高度警惕回调，建议采取保守策略"


# 便捷函数
async def get_market_sentiment() -> Dict[str, Any]:
    """
    获取市场情绪数据（便捷函数）
    
    Returns:
        包含情绪数据和建议的字典
    """
    fg_data = await SentimentService.get_fear_greed_index()
    
    value = fg_data["value"]
    
    return {
        "fear_greed_value": value,
        "fear_greed_label": fg_data["classification"],
        "interpretation": SentimentService.interpret_fear_greed(value),
        "suggestion": SentimentService.get_trading_suggestion(value),
        "available": fg_data["available"]
    }

