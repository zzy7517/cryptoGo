"""
市场数据相关的 Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class KlineData(BaseModel):
    """单根K线数据"""
    timestamp: int = Field(..., description="时间戳（毫秒）")
    open: float = Field(..., description="开盘价")
    high: float = Field(..., description="最高价")
    low: float = Field(..., description="最低价")
    close: float = Field(..., description="收盘价")
    volume: float = Field(..., description="成交量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1698768000000,
                "open": 34500.0,
                "high": 34800.0,
                "low": 34400.0,
                "close": 34650.0,
                "volume": 123.45
            }
        }


class KlineResponse(BaseModel):
    """K线数据响应"""
    symbol: str = Field(..., description="交易对")
    interval: str = Field(..., description="时间周期")
    data: List[KlineData] = Field(..., description="K线数据列表")
    count: int = Field(..., description="数据条数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "interval": "1h",
                "data": [],
                "count": 100
            }
        }


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
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "last": 34650.0,
                "bid": 34649.5,
                "ask": 34650.5,
                "high": 35000.0,
                "low": 34000.0,
                "volume": 12345.67,
                "change": 650.0,
                "percentage": 1.91,
                "timestamp": 1698768000000
            }
        }


class SymbolInfo(BaseModel):
    """交易对信息"""
    symbol: str = Field(..., description="交易对")
    base: str = Field(..., description="基础货币")
    quote: str = Field(..., description="计价货币")
    active: bool = Field(..., description="是否活跃")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTC/USDT",
                "base": "BTC",
                "quote": "USDT",
                "active": True
            }
        }


class SymbolListResponse(BaseModel):
    """交易对列表响应"""
    symbols: List[SymbolInfo] = Field(..., description="交易对列表")
    count: int = Field(..., description="交易对数量")


class MarketStats(BaseModel):
    """市场统计数据"""
    symbol: str = Field(..., description="交易对")
    price: float = Field(..., description="当前价格")
    high_24h: float = Field(..., description="24h最高价")
    low_24h: float = Field(..., description="24h最低价")
    volume_24h: float = Field(..., description="24h成交量")
    change_24h: float = Field(..., description="24h涨跌额")
    change_percentage_24h: float = Field(..., description="24h涨跌幅（%）")
    timestamp: int = Field(..., description="时间戳")

