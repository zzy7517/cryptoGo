"""
Agent 相关的 schemas
用于 Agent 运行、决策、状态管理等
创建时间: 2025-10-29
更新时间: 2025-10-30（移除 LangChain，改用定时循环）
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class RunAgentRequest(BaseModel):
    """运行 Agent 请求（定时循环版本）"""
    symbols: List[str] = Field(
        default=["BTC/USDT:USDT"],
        description="交易对列表"
    )
    risk_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="风险参数，包含 max_position_size, stop_loss_pct, take_profit_pct 等"
    )
    model: str = Field(
        default="deepseek-chat",
        description="DeepSeek 模型名称，可选 deepseek-chat 或 deepseek-reasoner"
    )


class ToolUsage(BaseModel):
    """工具使用记录"""
    tool_name: str = Field(..., description="工具名称")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="工具参数")
    result: Optional[Any] = Field(None, description="工具执行结果")
    timestamp: Optional[datetime] = Field(None, description="执行时间")


class RunAgentResponse(BaseModel):
    """运行 Agent 响应"""
    success: bool = Field(..., description="是否成功")
    session_id: int = Field(..., description="会话 ID")
    decision: Optional[str] = Field(None, description="决策结果")
    iterations: int = Field(default=0, description="迭代次数")
    tools_used: List[Dict[str, Any]] = Field(default_factory=list, description="使用的工具列表")
    error: Optional[str] = Field(None, description="错误信息")


class BackgroundAgentStatus(BaseModel):
    """后台 Agent 状态"""
    session_id: int = Field(..., description="会话 ID")
    running: bool = Field(..., description="是否正在运行")
    started_at: Optional[datetime] = Field(None, description="启动时间")
    last_run_at: Optional[datetime] = Field(None, description="最后运行时间")
    next_run_at: Optional[datetime] = Field(None, description="下次运行时间")
    total_decisions: int = Field(default=0, description="总决策次数")
    successful_decisions: int = Field(default=0, description="成功决策次数")
    failed_decisions: int = Field(default=0, description="失败决策次数")
    decision_interval: int = Field(..., description="决策间隔（秒）")
    symbols: List[str] = Field(default_factory=list, description="交易对列表")


class StartBackgroundAgentRequest(BaseModel):
    """启动后台 Agent 请求（定时循环模式）"""
    symbols: List[str] = Field(
        default=["BTC/USDT:USDT"],
        description="交易对列表"
    )
    risk_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="风险参数，可包含 decision_interval 字段自定义决策间隔"
    )
    model: str = Field(
        default="deepseek-chat",
        description="DeepSeek 模型名称"
    )


class StartBackgroundAgentResponse(BaseModel):
    """启动后台 Agent 响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[BackgroundAgentStatus] = Field(None, description="Agent 状态")


class StopBackgroundAgentResponse(BaseModel):
    """停止后台 Agent 响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="停止详情")


class BackgroundAgentListItem(BaseModel):
    """后台 Agent 列表项"""
    session_id: int = Field(..., description="会话 ID")
    running: bool = Field(..., description="是否运行中")
    started_at: Optional[datetime] = Field(None, description="启动时间")
    total_decisions: int = Field(default=0, description="总决策次数")

