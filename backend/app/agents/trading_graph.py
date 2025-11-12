"""
Trading Graph - LangGraph工作流定义
定义交易agent的执行流程
创建时间: 2025-11-07
"""
from langgraph.graph import StateGraph, END
from functools import lru_cache

from .state import TradingState
from .trading_decision_agent import trading_decision_node
from .risk_analysis_agent import risk_analysis_node
from .execution_agent import execution_node
from ..utils.logging import get_logger

logger = get_logger(__name__)


def create_trading_graph():
    """
    创建交易工作流图
    
    工作流：
    1. TradingDecision: 收集市场数据 + AI决策
    2. RiskAnalysis: 风险分析和审核
    3. Execution: 执行交易
    
    Returns:
        编译后的工作流图
    """
    logger.info("🏗️ 创建交易工作流图...")
    
    # 创建状态图
    graph = StateGraph(TradingState)
    
    # 添加节点
    graph.add_node("decision", trading_decision_node)
    graph.add_node("risk_analysis", risk_analysis_node)
    graph.add_node("execution", execution_node)
    
    # 定义工作流
    # 入口 -> 决策 -> 风险分析 -> 执行 -> 结束
    graph.set_entry_point("decision")
    graph.add_edge("decision", "risk_analysis")
    graph.add_edge("risk_analysis", "execution")
    graph.add_edge("execution", END)
    
    # 编译图
    compiled_graph = graph.compile()
    
    logger.info("✅ 交易工作流图创建成功")
    logger.info("📊 工作流: START -> Decision -> RiskAnalysis -> Execution -> END")
    
    return compiled_graph


@lru_cache(maxsize=1)
def get_trading_graph():
    """
    获取交易工作流图单例
    
    Returns:
        编译后的工作流图
    """
    return create_trading_graph()

