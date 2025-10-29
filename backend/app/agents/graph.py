"""
LangGraph Trading Graph
构建交易代理的状态图
创建时间: 2025-10-29
"""
from langgraph.graph import StateGraph, END
from app.agents.state import TradingState
from app.agents.nodes import (
    collect_market_data,
    analyze_market,
    execute_decision,
    update_positions,
    create_snapshot,
    check_continue
)
from app.core.logging import get_logger

logger = get_logger(__name__)


def create_trading_graph():
    """
    创建交易代理状态图
    
    流程:
    START → collect_data → analyze → execute → update → snapshot → (条件检查)
                                                                    ↓
                                                        continue ← ─┘ → stop (END)
    
    Returns:
        编译后的 LangGraph
    """
    # 创建状态图
    workflow = StateGraph(TradingState)
    
    # 添加节点
    workflow.add_node("collect_data", collect_market_data)
    workflow.add_node("analyze", analyze_market)
    workflow.add_node("execute", execute_decision)
    workflow.add_node("update", update_positions)
    workflow.add_node("snapshot", create_snapshot)
    
    # 添加边（定义节点之间的流转）
    workflow.set_entry_point("collect_data")
    workflow.add_edge("collect_data", "analyze")
    workflow.add_edge("analyze", "execute")
    workflow.add_edge("execute", "update")
    workflow.add_edge("update", "snapshot")
    
    # 添加条件边（根据状态决定是继续还是结束）
    workflow.add_conditional_edges(
        "snapshot",
        check_continue,
        {
            "continue": "collect_data",  # 循环回到数据收集
            "stop": END                   # 结束流程
        }
    )
    
    # 编译图
    graph = workflow.compile()
    
    logger.info("交易代理状态图已创建")
    
    return graph

