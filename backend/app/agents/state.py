"""
LangGraph 状态定义
定义整个交易agent工作流的状态结构
创建时间: 2025-11-07
"""
from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime


class TradingState(TypedDict, total=False):
    """
    交易Agent工作流的状态
    
    状态在各个agent节点之间传递，每个agent读取需要的字段并更新相应的输出字段
    """
    # ========== 输入参数 ==========
    session_id: int  # 交易会话ID
    symbols: List[str]  # 交易对列表，如 ['BTC/USDT:USDT', 'ETH/USDT:USDT']
    risk_params: Dict[str, Any]  # 风险参数配置
    call_count: int  # 决策周期计数
    start_time: datetime  # 会话开始时间
    
    # ========== 主要决策流程输出 ==========
    # 市场数据和提示词
    market_data: Optional[Dict[str, Any]]  # 市场数据（可选，用于后续扩展）
    user_prompt: str  # 完整的用户提示词（用于保存到数据库）
    system_prompt: str  # 系统提示词
    
    # AI决策
    ai_decisions: List[Dict[str, Any]]  # AI决策列表
    ai_response: str  # AI完整响应文本
    
    # 执行结果
    execution_results: List[Dict[str, Any]]  # 执行结果列表
    
    # ========== 风险分析 ==========
    risk_analysis: Optional[Dict[str, Any]]  # 风险分析结果
    
    # ========== 可选的增强功能（预留）==========
    sentiment_data: Optional[Dict[str, Any]]  # 市场情绪数据（未来扩展）
    historical_insights: Optional[Dict[str, Any]]  # 历史交易分析（未来扩展）
    
    # ========== 错误处理和调试 ==========
    errors: List[str]  # 错误信息列表
    debug_info: Dict[str, Any]  # 调试信息，记录各节点执行情况
