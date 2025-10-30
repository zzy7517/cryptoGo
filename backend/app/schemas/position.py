"""
持仓相关的 schemas
用于持仓的创建、查询、更新等
创建时间: 2025-10-29
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class PositionBase(BaseModel):
    """持仓基础信息"""
    id: int = Field(..., description="持仓 ID")
    created_at: datetime = Field(..., description="创建时间")
    session_id: int = Field(..., description="所属会话 ID")
    symbol: str = Field(..., description="交易对符号")
    side: str = Field(..., description="持仓方向: long, short")
    status: str = Field(..., description="状态: active, closed")
    quantity: float = Field(..., description="持仓数量")
    entry_price: float = Field(..., description="入场价格")


class PositionDetail(PositionBase):
    """持仓详细信息"""
    updated_at: datetime = Field(..., description="更新时间")
    current_price: Optional[float] = Field(None, description="当前价格")
    liquidation_price: Optional[float] = Field(None, description="强平价格")
    leverage: int = Field(default=1, description="杠杆倍数")
    margin: Optional[float] = Field(None, description="保证金金额")
    entry_time: Optional[datetime] = Field(None, description="开仓时间")
    exit_time: Optional[datetime] = Field(None, description="平仓时间")
    holding_duration: Optional[str] = Field(None, description="持仓时长")
    unrealized_pnl: Optional[float] = Field(None, description="未实现盈亏")
    realized_pnl: Optional[float] = Field(None, description="已实现盈亏")
    stop_loss: Optional[float] = Field(None, description="止损价")
    take_profit: Optional[float] = Field(None, description="止盈价")
    entry_order_id: Optional[int] = Field(None, description="入场订单 ID")
    exit_order_id: Optional[int] = Field(None, description="出场订单 ID")
    ai_decision_id: Optional[int] = Field(None, description="关联的 AI 决策 ID")


class CreatePositionRequest(BaseModel):
    """创建持仓请求"""
    session_id: int = Field(..., description="所属会话 ID")
    symbol: str = Field(..., description="交易对符号")
    side: str = Field(..., description="持仓方向: long, short")
    quantity: float = Field(..., description="持仓数量", gt=0)
    entry_price: float = Field(..., description="入场价格", gt=0)
    leverage: int = Field(default=1, description="杠杆倍数", ge=1)
    margin: Optional[float] = Field(None, description="保证金金额")
    stop_loss: Optional[float] = Field(None, description="止损价")
    take_profit: Optional[float] = Field(None, description="止盈价")
    entry_order_id: Optional[int] = Field(None, description="入场订单 ID")
    ai_decision_id: Optional[int] = Field(None, description="关联的 AI 决策 ID")


class UpdatePositionRequest(BaseModel):
    """更新持仓请求"""
    current_price: Optional[float] = Field(None, description="当前价格", gt=0)
    stop_loss: Optional[float] = Field(None, description="止损价")
    take_profit: Optional[float] = Field(None, description="止盈价")
    quantity: Optional[float] = Field(None, description="持仓数量", gt=0)


class ClosePositionRequest(BaseModel):
    """平仓请求"""
    exit_price: float = Field(..., description="平仓价格", gt=0)
    exit_order_id: Optional[int] = Field(None, description="出场订单 ID")
    quantity: Optional[float] = Field(None, description="平仓数量（部分平仓）", gt=0)


class PositionListResponse(BaseModel):
    """持仓列表响应"""
    success: bool = Field(..., description="是否成功")
    data: List[PositionDetail] = Field(default_factory=list, description="持仓列表")
    count: int = Field(..., description="持仓数量")


class PositionDetailResponse(BaseModel):
    """持仓详情响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[PositionDetail] = Field(None, description="持仓详情")


class PositionSummary(BaseModel):
    """持仓汇总"""
    total_positions: int = Field(..., description="总持仓数")
    active_positions: int = Field(..., description="活跃持仓数")
    long_positions: int = Field(..., description="多头持仓数")
    short_positions: int = Field(..., description="空头持仓数")
    total_unrealized_pnl: float = Field(..., description="总未实现盈亏")
    total_margin: float = Field(..., description="总保证金")
    avg_leverage: float = Field(..., description="平均杠杆")

