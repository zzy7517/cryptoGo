"""
Agent Constants - Agent系统常量定义
定义交易决策、执行等相关的常量
创建时间: 2025-11-12
"""


class TradingAction:
    """交易操作类型常量"""
    
    # 开仓操作
    OPEN_LONG = "open_long"      # 开多仓
    OPEN_SHORT = "open_short"    # 开空仓
    
    # 平仓操作
    CLOSE_LONG = "close_long"    # 平多仓
    CLOSE_SHORT = "close_short"  # 平空仓
    
    # 持仓/观望
    HOLD = "hold"                # 持仓不动
    WAIT = "wait"                # 观望等待
    
    # 操作组
    OPEN_ACTIONS = [OPEN_LONG, OPEN_SHORT]
    CLOSE_ACTIONS = [CLOSE_LONG, CLOSE_SHORT]
    ALL_ACTIONS = [OPEN_LONG, OPEN_SHORT, CLOSE_LONG, CLOSE_SHORT, HOLD, WAIT]


class RiskLevel:
    """风险等级常量"""
    
    LOW = "low"           # 低风险
    MEDIUM = "medium"     # 中等风险
    HIGH = "high"         # 高风险
    CRITICAL = "critical" # 严重风险（不可接受）


class PositionSide:
    """持仓方向常量"""
    
    LONG = "long"   # 多头
    SHORT = "short" # 空头


class SentimentLevel:
    """情绪等级常量"""
    
    EXTREME_FEAR = "extreme_fear"      # 极度恐慌
    FEAR = "fear"                      # 恐慌
    NEUTRAL = "neutral"                # 中性
    GREED = "greed"                    # 贪婪
    EXTREME_GREED = "extreme_greed"    # 极度贪婪

