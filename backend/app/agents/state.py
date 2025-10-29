"""
LangGraph Trading Agent State
定义交易代理的状态结构
创建时间: 2025-10-29
"""
from typing import TypedDict, Optional, List, Dict, Any
from datetime import datetime


class TradingState(TypedDict):
    """
    交易代理状态
    
    LangGraph 会在节点之间传递这个状态对象，每个节点可以读取和更新状态
    """
    # ============ 会话信息 ============
    session_id: int
    """交易会话 ID"""
    
    loop_count: int
    """循环计数器"""
    
    decision_interval: int
    """决策间隔（秒）"""
    
    symbols: List[str]
    """交易对列表，如 ['BTC/USDT:USDT', 'ETH/USDT:USDT']"""
    
    # ============ 市场数据 ============
    market_data: Optional[Dict[str, Any]]
    """
    当前市场数据，包含：
    - ticker: 实时价格
    - klines: K线数据
    - indicators: 技术指标
    - funding_rate: 资金费率
    - open_interest: 持仓量
    """
    
    # ============ 账户信息 ============
    available_capital: float
    """可用资金"""
    
    total_value: float
    """账户总价值"""
    
    active_positions: List[Dict[str, Any]]
    """
    活跃持仓列表，每个持仓包含：
    - id: 持仓 ID
    - symbol: 交易对
    - side: 方向 (long/short)
    - quantity: 数量
    - entry_price: 入场价格
    - current_price: 当前价格
    - unrealized_pnl: 未实现盈亏
    """
    
    # ============ AI 决策 ============
    last_decision: Optional[Dict[str, Any]]
    """
    最近的 AI 决策，包含：
    - decision_type: 决策类型 (buy/sell/hold/close)
    - confidence: 置信度 (0-1)
    - reasoning: 推理过程
    - suggested_actions: 建议的操作
    """
    
    last_decision_id: Optional[int]
    """最近决策的数据库 ID"""
    
    # ============ 控制标志 ============
    should_continue: bool
    """是否继续循环（检查会话状态）"""
    
    error_count: int
    """连续错误计数"""
    
    last_error: Optional[str]
    """最近的错误信息"""
    
    current_node: str
    """当前执行的节点名称（用于监控）"""
    
    last_update_time: str
    """最后更新时间（ISO格式）"""
    
    # ============ 配置参数 ============
    risk_params: Dict[str, Any]
    """
    风险参数：
    - max_position_size: 最大仓位（占总资金百分比）
    - stop_loss_pct: 止损百分比
    - take_profit_pct: 止盈百分比
    - max_leverage: 最大杠杆
    - max_positions: 最大同时持仓数
    """


def create_initial_state(
    session_id: int,
    decision_interval: int = 60,
    symbols: Optional[List[str]] = None,
    initial_capital: float = 10000.0,
    risk_params: Optional[Dict[str, Any]] = None
) -> TradingState:
    """
    创建初始交易状态
    
    Args:
        session_id: 会话 ID
        decision_interval: 决策间隔（秒）
        symbols: 交易对列表
        initial_capital: 初始资金
        risk_params: 风险参数
        
    Returns:
        初始化的 TradingState
    """
    if symbols is None:
        symbols = ["BTC/USDT:USDT"]
    
    if risk_params is None:
        risk_params = {
            "max_position_size": 0.2,  # 单个仓位最多占20%资金
            "stop_loss_pct": 0.05,      # 5% 止损
            "take_profit_pct": 0.10,    # 10% 止盈
            "max_leverage": 3,          # 最大3倍杠杆
            "max_positions": 3          # 最多3个同时持仓
        }
    
    return TradingState(
        session_id=session_id,
        loop_count=0,
        decision_interval=decision_interval,
        symbols=symbols,
        market_data=None,
        available_capital=initial_capital,
        total_value=initial_capital,
        active_positions=[],
        last_decision=None,
        last_decision_id=None,
        should_continue=True,
        error_count=0,
        last_error=None,
        current_node="START",
        last_update_time=datetime.now().isoformat(),
        risk_params=risk_params
    )

