"""
Trading Decision Agent - 交易决策Agent
整合市场数据收集和AI决策逻辑
创建时间: 2025-11-07
"""
import asyncio
from typing import Dict, Any
from datetime import datetime

from .state import TradingState
from ..utils.constants import TradingAction
from ..llm import get_llm
from ..llm.prompt_builder import build_user_prompt
from ..llm.response_parser import ResponseParser
from ..services.trading_agent_service import build_system_prompt, Decision
from ..utils.logging import get_logger

logger = get_logger(__name__)


async def trading_decision_node(state: TradingState) -> TradingState:
    """
    交易决策节点
    
    功能：
    1. 收集市场数据（复用现有的 build_user_prompt）
    2. 调用AI进行决策分析
    3. 解析AI响应，提取决策列表
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("=" * 80)
    logger.info("🤖 TradingDecisionAgent: 开始决策分析")
    logger.info("=" * 80)
    
    try:
        # 1. 构建系统提示词
        logger.info("📝 构建系统提示词...")
        system_prompt = await build_system_prompt(
            risk_params=state["risk_params"],
            session_id=state["session_id"]
        )
        
        # 2. 构建用户提示词（自动收集市场数据）
        logger.info("📊 收集市场数据并构建用户提示词...")
        user_prompt = await build_user_prompt(
            session_id=state["session_id"],
            symbols=state["symbols"],
            call_count=state["call_count"],
            start_time=state["start_time"]
        )
        
        logger.info(f"✅ 用户提示词已生成，长度: {len(user_prompt)} 字符")
        
        # 3. 调用AI
        logger.info("🤖 调用AI进行决策...")
        ai_engine = get_llm()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 使用 asyncio.to_thread 避免阻塞事件循环
        response = await asyncio.to_thread(ai_engine.chat, messages, temperature=0.3)
        
        logger.info("✅ AI 调用成功")
        logger.info("=" * 80)
        logger.info("💭 AI 分析结果:")
        logger.info("=" * 80)
        logger.info(response)
        logger.info("=" * 80)
        
        # 4. 解析AI响应
        logger.info("🔍 解析AI响应...")
        parsed = ResponseParser.parse(response)
        
        if parsed.parsing_errors:
            logger.warning(f"⚠️ 解析过程中出现错误:")
            for error in parsed.parsing_errors:
                logger.warning(f"  - {error}")
        
        # 转换为字典格式
        decisions = []
        for parsed_decision in parsed.decisions:
            decision_dict = {
                "symbol": parsed_decision.symbol,
                "action": parsed_decision.action,
                "reasoning": parsed_decision.reasoning,
                "leverage": parsed_decision.leverage,
                "position_size_usd": parsed_decision.position_size_usd,
                "stop_loss_pct": parsed_decision.stop_loss_pct,
                "take_profit_pct": parsed_decision.take_profit_pct,
                "stop_loss_price": parsed_decision.stop_loss,
                "take_profit_price": parsed_decision.take_profit,
                "confidence": parsed_decision.confidence,
                "risk_usd": parsed_decision.risk_usd
            }
            decisions.append(decision_dict)
        
        logger.info(f"✅ 成功解析 {len(decisions)} 个有效决策")
        
        # 打印决策列表
        logger.info(f"📋 决策列表 ({len(decisions)} 个):")
        for i, d in enumerate(decisions, 1):
            logger.info(f"  [{i}] {d['symbol']} - {d['action']}")
            logger.info(f"      理由: {d['reasoning']}")
            if d['action'] in TradingAction.OPEN_ACTIONS:
                logger.info(f"      杠杆: {d['leverage']}x, 仓位: ${d['position_size_usd']:.2f}")
                logger.info(f"      止损: {d.get('stop_loss_pct')}%, 止盈: {d.get('take_profit_pct')}%")
                logger.info(f"      信心度: {d['confidence']}%")
        
        # 5. 更新状态
        state["system_prompt"] = system_prompt
        state["user_prompt"] = user_prompt
        state["ai_response"] = response
        state["ai_decisions"] = decisions
        
        # 更新调试信息
        if "debug_info" not in state:
            state["debug_info"] = {}
        state["debug_info"]["decision_completed_at"] = datetime.now().isoformat()
        state["debug_info"]["decisions_count"] = len(decisions)
        
        logger.info("✅ TradingDecisionAgent: 决策完成")
        
        return state
        
    except Exception as e:
        logger.exception(f"❌ TradingDecisionAgent 执行失败: {e}")
        
        # 记录错误
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"DecisionAgent: {str(e)}")
        
        # 确保有空的决策列表
        if "ai_decisions" not in state:
            state["ai_decisions"] = []
        
        raise

