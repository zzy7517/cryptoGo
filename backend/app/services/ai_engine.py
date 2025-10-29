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

from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import ConfigurationException
from app.repositories.ai_decision_repo import AIDecisionRepository

logger = get_logger(__name__)


class AIEngine:
    """AI 引擎 - 基于 DeepSeek"""
    
    def __init__(self):
        """初始化 DeepSeek 客户端"""
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
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        调用 DeepSeek Chat API
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数 (0-2)，越高越随机
            max_tokens: 最大生成 token 数
            
        Returns:
            AI 回复内容
        """
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
                input_tokens=response.usage.prompt_tokens,
                output_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens
            )
            
            return content
            
        except Exception as e:
            error_msg = f"DeepSeek API 调用失败: {str(e)}"
            logger.exception(error_msg)
            raise Exception(error_msg) from e
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试 DeepSeek API 连接
        
        Returns:
            测试结果
        """
        try:
            response = self.chat(
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "Hello, please reply with 'OK' to confirm the connection."}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            logger.info("DeepSeek 连接测试成功", response=response)
            
            return {
                "status": "success",
                "model": self.model,
                "response": response,
                "message": "DeepSeek API 连接正常"
            }
            
        except Exception as e:
            logger.error("DeepSeek 连接测试失败", error=str(e))
            return {
                "status": "failed",
                "model": self.model,
                "error": str(e),
                "message": "DeepSeek API 连接失败"
            }
    
    def analyze_market(
        self,
        market_data: Dict[str, Any],
        context: Optional[str] = None,
        save_to_db: bool = False,
        db: Optional[Session] = None,
        session_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        分析市场数据
        
        Args:
            market_data: 市场数据字典
            context: 额外的上下文信息
            save_to_db: 是否保存到数据库
            db: 数据库会话（如果 save_to_db=True 则必须提供）
            session_id: 交易会话 ID（如果 save_to_db=True 则必须提供）
            
        Returns:
            {
                "analysis": "AI 分析结果",
                "decision_id": "数据库决策 ID（如果保存）",
                "prompt_data": "完整的 prompt 数据"
            }
        """
        # 构建系统提示词
        system_prompt = """你是一位专业的加密货币交易分析师。
你的任务是分析市场数据，给出专业的交易建议。

请基于提供的市场数据，给出：
1. 市场趋势判断
2. 关键指标解读
3. 交易建议（做多/做空/观望）
4. 风险提示

请保持客观、理性，避免过度乐观或悲观。"""

        # 构建用户消息
        user_message = f"""请分析以下市场数据：

{self._format_market_data(market_data)}

{f'额外信息：{context}' if context else ''}

请给出你的分析和建议。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        
        try:
            # 调用 AI
            response = self.chat(messages, temperature=0.3)
            logger.info("市场分析完成")
            
            # 准备返回结果
            result = {
                "analysis": response,
                "prompt_data": market_data
            }
            
            # 保存到数据库（如果需要）
            if save_to_db:
                if not db:
                    logger.warning("需要保存到数据库但未提供 db 会话")
                elif not session_id:
                    logger.warning("需要保存到数据库但未提供 session_id")
                else:
                    decision_id = self._save_decision_to_db(
                        db=db,
                        session_id=session_id,
                        market_data=market_data,
                        ai_response=response,
                        context=context
                    )
                    result["decision_id"] = decision_id
            
            return result
            
        except Exception as e:
            logger.error(f"市场分析失败: {str(e)}")
            raise
    
    def _save_decision_to_db(
        self,
        db: Session,
        session_id: int,
        market_data: Dict[str, Any],
        ai_response: str,
        context: Optional[str] = None
    ) -> Optional[int]:
        """
        保存决策到数据库
        
        Args:
            db: 数据库会话
            session_id: 交易会话 ID
            market_data: 市场数据
            ai_response: AI 回复
            context: 上下文
            
        Returns:
            决策 ID
        """
        try:
            repo = AIDecisionRepository(db)
            
            # 提取币种列表
            symbols = []
            if 'ticker' in market_data and 'symbol' in market_data['ticker']:
                # 单个币种
                symbol = market_data['ticker']['symbol'].split('/')[0]
                symbols = [symbol]
            
            # 简单的决策类型判断（后续可以让 AI 返回结构化数据）
            decision_type = "hold"  # 默认观望
            if "建议买入" in ai_response or "做多" in ai_response:
                decision_type = "buy"
            elif "建议卖出" in ai_response or "做空" in ai_response:
                decision_type = "sell"
            
            # 置信度默认值（后续可以让 AI 返回）
            confidence = Decimal("0.5")
            
            decision = repo.save_decision(
                session_id=session_id,
                symbols=symbols,
                decision_type=decision_type,
                confidence=confidence,
                prompt_data=market_data,
                ai_response=ai_response,
                reasoning=context
            )
            
            logger.info(f"决策已保存到数据库，ID: {decision.id}, Session: {session_id}")
            return decision.id
            
        except Exception as e:
            logger.error(f"保存决策到数据库失败: {str(e)}")
            return None
    
    def _format_market_data(self, market_data: Dict[str, Any]) -> str:
        """
        格式化市场数据为文本
        
        Args:
            market_data: 市场数据字典
            
        Returns:
            格式化的文本
        """
        formatted = []
        
        # 基础价格信息
        if 'ticker' in market_data:
            ticker = market_data['ticker']
            formatted.append(f"当前价格: ${ticker.get('last', 'N/A')}")
            formatted.append(f"24h涨跌: {ticker.get('percentage', 'N/A')}%")
            formatted.append(f"24h最高: ${ticker.get('high', 'N/A')}")
            formatted.append(f"24h最低: ${ticker.get('low', 'N/A')}")
            formatted.append(f"24h成交量: {ticker.get('volume', 'N/A')}")
        
        # 技术指标
        if 'indicators' in market_data:
            indicators = market_data['indicators']
            formatted.append("\n技术指标:")
            formatted.append(f"- EMA(20): ${indicators.get('ema20', 'N/A')}")
            formatted.append(f"- EMA(50): ${indicators.get('ema50', 'N/A')}")
            formatted.append(f"- MACD: {indicators.get('macd', 'N/A')}")
            formatted.append(f"- 信号线: {indicators.get('signal', 'N/A')}")
            formatted.append(f"- RSI(14): {indicators.get('rsi14', 'N/A')}")
            formatted.append(f"- ATR(14): {indicators.get('atr14', 'N/A')}")
        
        # 合约数据
        if 'funding_rate' in market_data:
            fr = market_data['funding_rate']
            formatted.append(f"\n资金费率: {fr.get('funding_rate', 'N/A')}")
        
        if 'open_interest' in market_data:
            oi = market_data['open_interest']
            formatted.append(f"持仓量: {oi.get('open_interest', 'N/A')}")
        
        return "\n".join(formatted)


@lru_cache(maxsize=1)
def get_ai_engine() -> AIEngine:
    """
    获取 AI 引擎单例
    
    使用 lru_cache 确保只创建一个实例，线程安全
    """
    return AIEngine()

