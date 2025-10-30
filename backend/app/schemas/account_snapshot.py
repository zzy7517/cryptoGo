"""
账户快照相关的 schemas
用于账户快照的创建、查询等
创建时间: 2025-10-29
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AccountSnapshotBase(BaseModel):
    """账户快照基础信息"""
    id: int = Field(..., description="快照 ID")
    created_at: datetime = Field(..., description="创建时间")
    session_id: int = Field(..., description="所属会话 ID")
    total_value: float = Field(..., description="账户总价值")
    available_cash: float = Field(..., description="可用现金")


class AccountSnapshotDetail(AccountSnapshotBase):
    """账户快照详细信息"""
    total_pnl: Optional[float] = Field(None, description="总盈亏")
    total_return_pct: Optional[float] = Field(None, description="总收益率 (%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤 (%)")
    positions_summary: Optional[Dict[str, Any]] = Field(None, description="当前所有持仓的快照")
    ai_decision_id: Optional[int] = Field(None, description="关联的 AI 决策 ID")


class CreateSnapshotRequest(BaseModel):
    """创建快照请求"""
    session_id: int = Field(..., description="所属会话 ID")
    total_value: float = Field(..., description="账户总价值", gt=0)
    available_cash: float = Field(..., description="可用现金", ge=0)
    total_pnl: Optional[float] = Field(None, description="总盈亏")
    total_return_pct: Optional[float] = Field(None, description="总收益率 (%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤 (%)")
    positions_summary: Optional[Dict[str, Any]] = Field(None, description="持仓汇总")
    ai_decision_id: Optional[int] = Field(None, description="关联的 AI 决策 ID")


class SnapshotListResponse(BaseModel):
    """快照列表响应"""
    success: bool = Field(..., description="是否成功")
    data: List[AccountSnapshotDetail] = Field(default_factory=list, description="快照列表")
    count: int = Field(..., description="快照数量")


class SnapshotDetailResponse(BaseModel):
    """快照详情响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[AccountSnapshotDetail] = Field(None, description="快照详情")


class EquityCurvePoint(BaseModel):
    """权益曲线点"""
    timestamp: datetime = Field(..., description="时间戳")
    total_value: float = Field(..., description="账户总价值")
    available_cash: float = Field(..., description="可用现金")
    total_pnl: Optional[float] = Field(None, description="总盈亏")
    return_pct: Optional[float] = Field(None, description="收益率 (%)")


class EquityCurveResponse(BaseModel):
    """权益曲线响应"""
    success: bool = Field(..., description="是否成功")
    data: List[EquityCurvePoint] = Field(default_factory=list, description="权益曲线数据")
    count: int = Field(..., description="数据点数量")
    statistics: Optional[Dict[str, Any]] = Field(None, description="统计信息")


class PerformanceMetrics(BaseModel):
    """绩效指标"""
    total_return: float = Field(..., description="总收益率 (%)")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    max_drawdown: Optional[float] = Field(None, description="最大回撤 (%)")
    win_rate: Optional[float] = Field(None, description="胜率 (%)")
    profit_factor: Optional[float] = Field(None, description="盈亏比")
    avg_win: Optional[float] = Field(None, description="平均盈利")
    avg_loss: Optional[float] = Field(None, description="平均亏损")
    total_trades: Optional[int] = Field(None, description="总交易次数")

