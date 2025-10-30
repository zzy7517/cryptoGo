"""
交易记录相关的 schemas
用于交易记录的创建、查询等
创建时间: 2025-10-29
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class TradeBase(BaseModel):
    """交易基础信息"""
    id: int = Field(..., description="交易 ID")
    created_at: datetime = Field(..., description="创建时间")
    session_id: int = Field(..., description="所属会话 ID")
    symbol: str = Field(..., description="交易对符号")
    side: str = Field(..., description="方向: buy, sell, long, short")
    quantity: float = Field(..., description="交易数量")
    price: float = Field(..., description="成交价格")
    total_value: float = Field(..., description="总价值")


class TradeDetail(TradeBase):
    """交易详细信息"""
    order_type: Optional[str] = Field(None, description="订单类型: market, limit, stop, stop_limit")
    leverage: int = Field(default=1, description="杠杆倍数")
    notional_entry: Optional[float] = Field(None, description="名义入场价值")
    notional_exit: Optional[float] = Field(None, description="名义出场价值")
    entry_time: Optional[datetime] = Field(None, description="开仓时间")
    exit_time: Optional[datetime] = Field(None, description="平仓时间")
    holding_duration: Optional[str] = Field(None, description="持仓时长")
    fee: Optional[float] = Field(None, description="手续费")
    fee_currency: Optional[str] = Field(None, description="手续费币种")
    pnl: Optional[float] = Field(None, description="盈亏金额")
    pnl_pct: Optional[float] = Field(None, description="盈亏百分比")
    position_id: Optional[int] = Field(None, description="关联的持仓 ID")
    ai_decision_id: Optional[int] = Field(None, description="关联的 AI 决策 ID")
    exchange_order_id: Optional[str] = Field(None, description="交易所订单 ID")


class CreateTradeRequest(BaseModel):
    """创建交易请求"""
    session_id: int = Field(..., description="所属会话 ID")
    symbol: str = Field(..., description="交易对符号")
    side: str = Field(..., description="方向: buy, sell, long, short")
    quantity: float = Field(..., description="交易数量", gt=0)
    price: float = Field(..., description="成交价格", gt=0)
    order_type: Optional[str] = Field(default="market", description="订单类型")
    leverage: int = Field(default=1, description="杠杆倍数", ge=1)
    fee: Optional[float] = Field(None, description="手续费")
    fee_currency: Optional[str] = Field(None, description="手续费币种")
    position_id: Optional[int] = Field(None, description="关联的持仓 ID")
    ai_decision_id: Optional[int] = Field(None, description="关联的 AI 决策 ID")
    exchange_order_id: Optional[str] = Field(None, description="交易所订单 ID")


class TradeListResponse(BaseModel):
    """交易列表响应"""
    success: bool = Field(..., description="是否成功")
    data: List[TradeDetail] = Field(default_factory=list, description="交易列表")
    count: int = Field(..., description="交易数量")


class TradeDetailResponse(BaseModel):
    """交易详情响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[TradeDetail] = Field(None, description="交易详情")


class TradeStatistics(BaseModel):
    """交易统计"""
    total_trades: int = Field(..., description="总交易次数")
    winning_trades: int = Field(..., description="盈利交易次数")
    losing_trades: int = Field(..., description="亏损交易次数")
    win_rate: float = Field(..., description="胜率 (%)")
    total_pnl: float = Field(..., description="总盈亏")
    avg_pnl: float = Field(..., description="平均盈亏")
    biggest_win: float = Field(..., description="最大盈利")
    biggest_loss: float = Field(..., description="最大亏损")
    avg_holding_time: Optional[str] = Field(None, description="平均持仓时长")

