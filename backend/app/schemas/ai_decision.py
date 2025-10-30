"""
AI 决策相关的 schemas
用于 AI 决策记录的创建、查询等
创建时间: 2025-10-29
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AIDecisionBase(BaseModel):
    """AI 决策基础信息"""
    id: int = Field(..., description="决策 ID")
    created_at: datetime = Field(..., description="创建时间")
    session_id: int = Field(..., description="所属会话 ID")
    symbols: Optional[List[str]] = Field(None, description="分析的币种列表")
    decision_type: str = Field(..., description="决策类型: buy, sell, hold, rebalance, close")
    confidence: Optional[float] = Field(None, description="置信度 (0-1)")


class AIDecisionDetail(AIDecisionBase):
    """AI 决策详细信息"""
    prompt_data: Optional[Dict[str, Any]] = Field(None, description="给 AI 的完整 prompt 数据")
    ai_response: Optional[str] = Field(None, description="AI 的原始回复")
    reasoning: Optional[str] = Field(None, description="AI 的推理过程")
    suggested_actions: Optional[Dict[str, Any]] = Field(None, description="建议的具体操作")
    executed: bool = Field(default=False, description="是否已执行")
    execution_result: Optional[Dict[str, Any]] = Field(None, description="执行结果")


class CreateAIDecisionRequest(BaseModel):
    """创建 AI 决策请求"""
    session_id: int = Field(..., description="所属会话 ID")
    symbols: Optional[List[str]] = Field(None, description="分析的币种列表")
    decision_type: str = Field(..., description="决策类型: buy, sell, hold, rebalance, close")
    confidence: Optional[float] = Field(None, description="置信度 (0-1)", ge=0, le=1)
    prompt_data: Optional[Dict[str, Any]] = Field(None, description="给 AI 的完整 prompt 数据")
    ai_response: Optional[str] = Field(None, description="AI 的原始回复")
    reasoning: Optional[str] = Field(None, description="AI 的推理过程")
    suggested_actions: Optional[Dict[str, Any]] = Field(None, description="建议的具体操作")


class UpdateAIDecisionRequest(BaseModel):
    """更新 AI 决策请求"""
    executed: bool = Field(..., description="是否已执行")
    execution_result: Optional[Dict[str, Any]] = Field(None, description="执行结果")


class AIDecisionListResponse(BaseModel):
    """AI 决策列表响应"""
    success: bool = Field(..., description="是否成功")
    data: List[AIDecisionDetail] = Field(default_factory=list, description="决策列表")
    count: int = Field(..., description="决策数量")


class AIDecisionDetailResponse(BaseModel):
    """AI 决策详情响应"""
    success: bool = Field(..., description="是否成功")
    data: Optional[AIDecisionDetail] = Field(None, description="决策详情")


class AIDecisionStatistics(BaseModel):
    """AI 决策统计"""
    total_decisions: int = Field(..., description="总决策次数")
    executed_decisions: int = Field(..., description="已执行决策次数")
    buy_decisions: int = Field(..., description="买入决策次数")
    sell_decisions: int = Field(..., description="卖出决策次数")
    hold_decisions: int = Field(..., description="持有决策次数")
    avg_confidence: float = Field(..., description="平均置信度")
    success_rate: Optional[float] = Field(None, description="成功率 (%)")


class SuggestedAction(BaseModel):
    """建议的操作"""
    symbol: str = Field(..., description="交易对")
    action: str = Field(..., description="操作类型: open_long, open_short, close, adjust")
    quantity: Optional[float] = Field(None, description="数量")
    price: Optional[float] = Field(None, description="价格")
    leverage: Optional[int] = Field(None, description="杠杆")
    stop_loss: Optional[float] = Field(None, description="止损价")
    take_profit: Optional[float] = Field(None, description="止盈价")
    reason: Optional[str] = Field(None, description="原因")

