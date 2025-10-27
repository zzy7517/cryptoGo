"""
市场数据相关的 Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class KlineData(BaseModel):
    """单根K线数据"""
    timestamp: int = Field(..., description="时间戳（毫秒）")
    open: float = Field(..., description="周期开始价格")
    high: float = Field(..., description="周期最高价格")
    low: float = Field(..., description="周期最低价格")
    close: float = Field(..., description="周期结束价格")
    volume: float = Field(..., description="周期成交量")


class KlineResponse(BaseModel):
    """K线数据响应"""
    symbol: str = Field(..., description="交易对")
    interval: str = Field(..., description="时间周期")
    data: List[KlineData] = Field(..., description="K线数据列表")
    count: int = Field(..., description="数据条数")


class TickerData(BaseModel):
    """实时行情数据"""
    symbol: str = Field(..., description="交易对")
    last: float = Field(..., description="最新成交价")
    bid: Optional[float] = Field(None, description="买一价")
    ask: Optional[float] = Field(None, description="卖一价")
    high: Optional[float] = Field(None, description="24h最高价")
    low: Optional[float] = Field(None, description="24h最低价")
    volume: Optional[float] = Field(None, description="24h成交量")
    change: Optional[float] = Field(None, description="24h涨跌额")
    percentage: Optional[float] = Field(None, description="24h涨跌幅（%）")
    timestamp: int = Field(..., description="时间戳（毫秒）")


class SymbolInfo(BaseModel):
    """交易对信息"""
    symbol: str = Field(..., description="交易对")
    base: str = Field(..., description="基础货币")
    quote: str = Field(..., description="计价货币")
    active: bool = Field(..., description="是否活跃")


class SymbolListResponse(BaseModel):
    """交易对列表响应"""
    symbols: List[SymbolInfo] = Field(..., description="交易对列表")
    count: int = Field(..., description="交易对数量")


class FundingRateData(BaseModel):
    """资金费率数据"""
    symbol: str = Field(..., description="交易对")
    funding_rate: Optional[float] = Field(None, description="当前资金费率")
    next_funding_time: Optional[int] = Field(None, description="下次结算时间戳（毫秒）")
    timestamp: int = Field(..., description="时间戳（毫秒）")


class OpenInterestData(BaseModel):
    """持仓量数据"""
    symbol: str = Field(..., description="交易对")
    open_interest: Optional[float] = Field(None, description="持仓量")
    timestamp: int = Field(..., description="时间戳（毫秒）")


class IndicatorLatestValues(BaseModel):
    """最新技术指标值"""
    ema20: float = Field(..., description="EMA 20周期")
    ema50: float = Field(..., description="EMA 50周期")
    macd: float = Field(..., description="MACD线")
    signal: float = Field(..., description="MACD信号线")
    histogram: float = Field(..., description="MACD柱状图")
    rsi7: float = Field(..., description="RSI 7周期")
    rsi14: float = Field(..., description="RSI 14周期")
    atr3: float = Field(..., description="ATR 3周期")
    atr14: float = Field(..., description="ATR 14周期")


class IndicatorSeriesData(BaseModel):
    """技术指标时序数据"""
    timestamps: List[int] = Field(..., description="时间戳列表（毫秒）")
    ema20: List[float] = Field(..., description="EMA 20周期序列")
    ema50: List[float] = Field(..., description="EMA 50周期序列")
    macd: List[float] = Field(..., description="MACD线序列")
    signal: List[float] = Field(..., description="MACD信号线序列")
    histogram: List[float] = Field(..., description="MACD柱状图序列")
    rsi7: List[float] = Field(..., description="RSI 7周期序列")
    rsi14: List[float] = Field(..., description="RSI 14周期序列")
    atr3: List[float] = Field(..., description="ATR 3周期序列")
    atr14: List[float] = Field(..., description="ATR 14周期序列")


class IndicatorsResponse(BaseModel):
    """技术指标响应"""
    symbol: str = Field(..., description="交易对")
    interval: str = Field(..., description="时间周期")
    latest_values: IndicatorLatestValues = Field(..., description="最新指标值")
    series_data: Optional[IndicatorSeriesData] = Field(None, description="时序数据（可选）")

