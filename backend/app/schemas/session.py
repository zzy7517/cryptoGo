"""
交易会话相关的 schemas
用于会话创建、查询、更新等
创建时间: 2025-10-29
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class SessionConfig(BaseModel):
    """会话配置"""
    max_position_size: Optional[float] = Field(None, description="最大持仓比例")
    stop_loss_pct: Optional[float] = Field(None, description="止损百分比")
    take_profit_pct: Optional[float] = Field(None, description="止盈百分比")
    max_leverage: Optional[int] = Field(None, description="最大杠杆倍数")
    max_positions: Optional[int] = Field(None, description="最大持仓数量")
    decision_interval: Optional[int] = Field(None, description="决策间隔（秒）")


class StartSessionRequest(BaseModel):
    """开始会话请求"""
    session_name: Optional[str] = Field(None, description="会话名称")
    initial_capital: Optional[float] = Field(None, description="初始资金", gt=0)
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")

    # Agent 配置（必定启动）
    auto_start_agent: bool = Field(default=True, description="是否自动启动 Agent（默认必定启动）")
    symbols: Optional[List[str]] = Field(
        None, 
        description="交易币种列表，例如 ['BTC/USDT:USDT', 'ETH/USDT:USDT']。如果未提供，使用默认币种"
    )
    decision_interval: Optional[int] = Field(60, description="决策间隔（秒），默认 60 秒", ge=10, le=3600)
    risk_params: Optional[Dict[str, Any]] = Field(None, description="风险参数配置")
    margin_mode: Optional[str] = Field("CROSSED", description="保证金模式: CROSSED(全仓) 或 ISOLATED(逐仓)")


class EndSessionRequest(BaseModel):
    """结束会话请求"""
    session_id: Optional[int] = Field(None, description="会话 ID，不提供则结束当前活跃会话")
    status: str = Field(default="completed", description="结束状态: completed, stopped, crashed")
    notes: Optional[str] = Field(None, description="备注信息")


class SessionBase(BaseModel):
    """会话基础信息"""
    id: int = Field(..., description="会话 ID")
    session_name: Optional[str] = Field(None, description="会话名称")
    status: str = Field(..., description="会话状态")
    created_at: datetime = Field(..., description="创建时间")
    ended_at: Optional[datetime] = Field(None, description="结束时间")


class SessionBasic(SessionBase):
    """会话基本信息（列表展示）"""
    initial_capital: Optional[float] = Field(None, description="初始资金")
    final_capital: Optional[float] = Field(None, description="最终资金")
    total_pnl: Optional[float] = Field(None, description="总盈亏")
    total_return_pct: Optional[float] = Field(None, description="总收益率 (%)")
    total_trades: int = Field(default=0, description="总交易次数")


class SessionDetail(SessionBasic):
    """会话详细信息"""
    winning_trades: int = Field(default=0, description="盈利交易次数")
    losing_trades: int = Field(default=0, description="亏损交易次数")
    config: Optional[Dict[str, Any]] = Field(None, description="运行配置")
    notes: Optional[str] = Field(None, description="备注信息")


class SessionWithAgentStatus(SessionBasic):
    """带 Agent 状态的会话信息"""
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")
    agent_status: Optional[Dict[str, Any]] = Field(None, description="Agent 状态")


class StartSessionResponse(BaseModel):
    """开始会话响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="会话数据")


class EndSessionResponse(BaseModel):
    """结束会话响应"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Dict[str, Any]] = Field(None, description="会话数据")


class SessionListResponse(BaseModel):
    """会话列表响应"""
    success: bool = Field(..., description="是否成功")
    data: List[SessionBasic] = Field(default_factory=list, description="会话列表")
    count: int = Field(..., description="会话数量")


class SessionDetailResponse(BaseModel):
    """会话详情响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[SessionDetail] = Field(None, description="会话详情")

