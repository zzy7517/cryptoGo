"""
AI Response Parser - 解析AI交易决策响应
根据系统提示词中定义的格式解析AI响应

响应格式:
1. 思维链分析（纯文本）
2. JSON决策数组

创建时间: 2025-10-31
"""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from decimal import Decimal

from ..utils.logging import get_logger

logger = get_logger(__name__)


# ==================== 数据结构 ====================

@dataclass
class Decision:
    """
    AI 决策数据结构

    对应系统提示词中的JSON格式:
    {
        "symbol": "BTCUSDT",
        "action": "open_short",
        "leverage": 5,
        "position_size_usd": 5000,
        "stop_loss": 97000,
        "take_profit": 91000,
        "confidence": 85,
        "risk_usd": 300,
        "reasoning": "下跌趋势+MACD死叉"
    }
    """
    symbol: str
    action: str  # open_long, open_short, close_long, close_short, hold, wait
    reasoning: str = ""

    # 开仓时必填字段
    leverage: int = 1
    position_size_usd: float = 0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    confidence: int = 50
    risk_usd: Optional[float] = None

    # 兼容旧版本的百分比字段（如果有）
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（排除None值）"""
        result = {}
        for k, v in asdict(self).items():
            if v is not None:
                result[k] = v
        return result

    def validate(self) -> Tuple[bool, Optional[str]]:
        """
        验证决策数据的有效性

        Returns:
            (is_valid, error_message)
        """
        # 基础字段验证
        if not self.symbol:
            return False, "symbol 不能为空"

        if not self.action:
            return False, "action 不能为空"

        valid_actions = ["open_long", "open_short", "close_long", "close_short", "hold", "wait"]
        if self.action not in valid_actions:
            return False, f"action 必须是以下之一: {valid_actions}"

        # 开仓操作的必填字段验证
        if self.action in ["open_long", "open_short"]:
            if self.leverage <= 0:
                return False, f"开仓时 leverage 必须 > 0，当前值: {self.leverage}"

            if self.position_size_usd <= 0:
                return False, f"开仓时 position_size_usd 必须 > 0，当前值: {self.position_size_usd}"

            # 止损止盈价格验证（如果提供了）
            if self.stop_loss is not None and self.stop_loss <= 0:
                return False, f"stop_loss 必须 > 0，当前值: {self.stop_loss}"

            if self.take_profit is not None and self.take_profit <= 0:
                return False, f"take_profit 必须 > 0，当前值: {self.take_profit}"

            # 信心度验证
            if not (0 <= self.confidence <= 100):
                return False, f"confidence 必须在 0-100 之间，当前值: {self.confidence}"

        return True, None


@dataclass
class ParsedResponse:
    """解析后的AI响应"""
    thinking: str = ""  # 思维链分析
    decisions: List[Decision] = field(default_factory=list)  # 决策列表
    raw_json: str = ""  # 原始JSON字符串
    parsing_errors: List[str] = field(default_factory=list)  # 解析错误列表

    @property
    def is_valid(self) -> bool:
        """是否成功解析"""
        return len(self.decisions) > 0 and len(self.parsing_errors) == 0

    @property
    def summary(self) -> str:
        """生成摘要"""
        if not self.decisions:
            return "无有效决策"

        action_counts = {}
        for d in self.decisions:
            action_counts[d.action] = action_counts.get(d.action, 0) + 1

        summary_parts = [f"{action}: {count}" for action, count in action_counts.items()]
        return f"共 {len(self.decisions)} 个决策 ({', '.join(summary_parts)})"


# ==================== 解析器 ====================

class ResponseParser:
    """AI响应解析器"""

    @staticmethod
    def parse(response: str) -> ParsedResponse:
        """
        解析AI响应

        Args:
            response: AI完整响应文本

        Returns:
            ParsedResponse对象
        """
        logger.info("🔍 开始解析 AI 响应")

        result = ParsedResponse()

        try:
            # 1. 提取思维链和JSON部分
            thinking, json_str = ResponseParser._extract_parts(response)
            result.thinking = thinking
            result.raw_json = json_str

            if not json_str:
                error_msg = "未找到 JSON 决策数组"
                logger.warning(f"⚠️ {error_msg}")
                result.parsing_errors.append(error_msg)
                return result

            logger.info(f"✅ 成功提取 JSON 字符串，长度: {len(json_str)}")

            # 2. 解析JSON
            decisions_data = ResponseParser._parse_json(json_str)

            if decisions_data is None:
                error_msg = "JSON 解析失败"
                logger.error(f"❌ {error_msg}")
                result.parsing_errors.append(error_msg)
                return result

            # 3. 验证JSON是否为数组
            if not isinstance(decisions_data, list):
                error_msg = f"JSON 必须是数组格式，实际类型: {type(decisions_data).__name__}"
                logger.error(f"❌ {error_msg}")
                result.parsing_errors.append(error_msg)
                return result

            logger.info(f"✅ JSON 解析成功，决策数量: {len(decisions_data)}")

            # 4. 转换为Decision对象
            for i, data in enumerate(decisions_data):
                try:
                    decision = ResponseParser._parse_decision(data)

                    # 验证决策
                    is_valid, error = decision.validate()
                    if not is_valid:
                        error_msg = f"决策 [{i}] 验证失败: {error}"
                        logger.warning(f"⚠️ {error_msg}")
                        result.parsing_errors.append(error_msg)
                        continue

                    result.decisions.append(decision)
                    logger.debug(f"✅ 决策 [{i}] 解析成功: {decision.symbol} {decision.action}")

                except Exception as e:
                    error_msg = f"决策 [{i}] 解析失败: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    result.parsing_errors.append(error_msg)

            # 5. 总结
            if result.decisions:
                logger.info(f"✅ 成功解析 {len(result.decisions)} 个有效决策")
            else:
                logger.warning("⚠️ 没有解析到有效决策")

            if result.parsing_errors:
                logger.warning(f"⚠️ 解析过程中出现 {len(result.parsing_errors)} 个错误")

            return result

        except Exception as e:
            error_msg = f"解析 AI 响应时发生异常: {str(e)}"
            logger.exception(error_msg)
            result.parsing_errors.append(error_msg)
            return result

    @staticmethod
    def _extract_parts(response: str) -> Tuple[str, str]:
        """
        提取思维链和JSON部分

        Args:
            response: 完整响应

        Returns:
            (thinking, json_str)
        """
        # 方法1: 查找markdown代码块中的JSON
        json_code_block_pattern = r'```json\s*([\s\S]*?)\s*```'
        match = re.search(json_code_block_pattern, response)

        if match:
            json_str = match.group(1).strip()
            thinking = response[:match.start()].strip()
            logger.debug("✅ 从 markdown 代码块中提取 JSON")
            return thinking, json_str

        # 方法2: 查找普通代码块
        code_block_pattern = r'```\s*([\s\S]*?)\s*```'
        match = re.search(code_block_pattern, response)

        if match:
            potential_json = match.group(1).strip()
            # 验证是否是JSON数组
            if potential_json.startswith('[') and potential_json.endswith(']'):
                thinking = response[:match.start()].strip()
                logger.debug("✅ 从代码块中提取 JSON")
                return thinking, potential_json

        # 方法3: 直接查找JSON数组（最宽松）
        json_start = response.find('[')
        json_end = response.rfind(']')

        if json_start != -1 and json_end != -1 and json_end > json_start:
            json_str = response[json_start:json_end + 1]
            thinking = response[:json_start].strip()
            logger.debug("✅ 从响应中直接提取 JSON 数组")
            return thinking, json_str

        # 未找到JSON
        logger.warning("⚠️ 未找到 JSON 数组")
        return response.strip(), ""

    @staticmethod
    def _parse_json(json_str: str) -> Optional[Any]:
        """
        解析JSON字符串

        Args:
            json_str: JSON字符串

        Returns:
            解析后的对象，失败返回None
        """
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON 解析失败: {e}")
            logger.debug(f"JSON 字符串: {json_str[:200]}...")

            # 尝试修复常见JSON错误
            try:
                # 移除尾部逗号
                fixed_json = re.sub(r',\s*([}\]])', r'\1', json_str)
                return json.loads(fixed_json)
            except json.JSONDecodeError:
                logger.error("❌ JSON 修复失败")
                return None

    @staticmethod
    def _parse_decision(data: Dict[str, Any]) -> Decision:
        """
        从字典解析Decision对象

        Args:
            data: 决策字典

        Returns:
            Decision对象
        """
        # 提取基础字段
        symbol = data.get('symbol', '')
        action = data.get('action', 'wait')
        reasoning = data.get('reasoning', '')

        # 提取开仓字段
        leverage = int(data.get('leverage', 1))
        position_size_usd = float(data.get('position_size_usd', 0))
        confidence = int(data.get('confidence', 50))

        # 提取止损止盈（支持价格和百分比两种格式）
        stop_loss = None
        take_profit = None
        stop_loss_pct = None
        take_profit_pct = None
        risk_usd = None

        # 优先使用价格格式
        if 'stop_loss' in data:
            stop_loss = float(data['stop_loss'])
        elif 'stop_loss_pct' in data:
            stop_loss_pct = float(data['stop_loss_pct'])

        if 'take_profit' in data:
            take_profit = float(data['take_profit'])
        elif 'take_profit_pct' in data:
            take_profit_pct = float(data['take_profit_pct'])

        if 'risk_usd' in data:
            risk_usd = float(data['risk_usd'])

        return Decision(
            symbol=symbol,
            action=action,
            reasoning=reasoning,
            leverage=leverage,
            position_size_usd=position_size_usd,
            stop_loss=stop_loss,
            take_profit=take_profit,
            confidence=confidence,
            risk_usd=risk_usd,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct
        )


# ==================== 便捷函数 ====================

def parse_ai_response(response: str) -> Tuple[ParsedResponse, List[Decision]]:
    """
    解析AI响应的便捷函数

    Args:
        response: AI完整响应

    Returns:
        (ParsedResponse对象, Decision列表)
    """
    parsed = ResponseParser.parse(response)
    return parsed, parsed.decisions


def extract_thinking_and_decisions(response: str) -> Tuple[str, List[Decision]]:
    """
    提取思维链和决策列表

    Args:
        response: AI完整响应

    Returns:
        (thinking, decisions)
    """
    parsed = ResponseParser.parse(response)
    return parsed.thinking, parsed.decisions
