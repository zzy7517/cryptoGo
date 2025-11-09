"""
Execution Agent - 交易执行Agent
执行AI决策的交易操作
创建时间: 2025-11-07
"""
import asyncio
from typing import Dict, Any
from datetime import datetime

from .state import TradingState
from ..services.trading_agent_service import execute_decision, Decision
from ..utils.logging import get_logger

logger = get_logger(__name__)


async def execution_node(state: TradingState) -> TradingState:
    """
    交易执行节点
    
    功能：
    执行AI决策的交易操作（开仓、平仓、持仓、观望）
    
    Args:
        state: 当前状态
        
    Returns:
        更新后的状态
    """
    logger.info("=" * 80)
    logger.info("🔧 ExecutionAgent: 开始执行交易")
    logger.info("=" * 80)
    
    try:
        decisions = state.get("ai_decisions", [])
        
        if not decisions:
            logger.info("⚠️ 没有需要执行的决策")
            state["execution_results"] = []
            return state
        
        execution_results = []
        margin_mode = state["risk_params"].get("margin_mode", "CROSSED")
        
        for i, decision_dict in enumerate(decisions, 1):
            logger.info(f"执行决策 [{i}/{len(decisions)}]: {decision_dict['symbol']} {decision_dict['action']}")
            
            # 转换为Decision对象
            decision = Decision(
                symbol=decision_dict["symbol"],
                action=decision_dict["action"],
                reasoning=decision_dict["reasoning"],
                leverage=decision_dict["leverage"],
                position_size_usd=decision_dict["position_size_usd"],
                stop_loss_pct=decision_dict.get("stop_loss_pct"),
                take_profit_pct=decision_dict.get("take_profit_pct"),
                stop_loss_price=decision_dict.get("stop_loss_price"),
                take_profit_price=decision_dict.get("take_profit_price"),
                confidence=decision_dict["confidence"],
                risk_usd=decision_dict.get("risk_usd")
            )
            
            # 执行决策
            result = await execute_decision(
                decision=decision,
                session_id=state["session_id"],
                margin_mode=margin_mode
            )
            
            execution_results.append({
                "decision": decision_dict,
                "result": result
            })
            
            # 短暂延迟，避免请求过快
            if result.get('success'):
                await asyncio.sleep(0.5)
        
        logger.info("✅ ExecutionAgent: 交易执行完成")
        
        # 更新状态
        state["execution_results"] = execution_results
        
        # 更新调试信息
        if "debug_info" not in state:
            state["debug_info"] = {}
        state["debug_info"]["execution_completed_at"] = datetime.now().isoformat()
        state["debug_info"]["executed_count"] = len(execution_results)
        
        # 统计执行结果
        success_count = sum(1 for er in execution_results if er["result"].get("success"))
        logger.info(f"📊 执行统计: 成功 {success_count}/{len(execution_results)}")
        
        return state
        
    except Exception as e:
        logger.exception(f"❌ ExecutionAgent 执行失败: {e}")
        
        # 记录错误
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"ExecutionAgent: {str(e)}")
        
        # 确保有空的执行结果列表
        if "execution_results" not in state:
            state["execution_results"] = []
        
        raise

