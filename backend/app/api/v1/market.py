"""
市场数据 API 路由
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from app.schemas.market import (
    KlineResponse, 
    KlineData, 
    TickerData, 
    SymbolListResponse,
    SymbolInfo,
    MarketStats
)
from app.services.data_collector import get_exchange_connector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/klines", response_model=KlineResponse)
async def get_klines(
    symbol: str = Query(default="BTC/USDT", description="交易对，如 BTC/USDT"),
    interval: str = Query(default="1h", description="时间周期: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(default=100, ge=1, le=1000, description="返回数据条数"),
    since: Optional[int] = Query(default=None, description="起始时间戳（毫秒）")
):
    """
    获取K线数据
    
    支持的时间周期：
    - 1m: 1分钟
    - 5m: 5分钟
    - 15m: 15分钟
    - 1h: 1小时
    - 4h: 4小时
    - 1d: 1天
    """
    try:
        connector = get_exchange_connector()
        klines_data = connector.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit,
            since=since
        )
        
        return KlineResponse(
            symbol=symbol,
            interval=interval,
            data=[KlineData(**kline) for kline in klines_data],
            count=len(klines_data)
        )
    except Exception as e:
        logger.error(f"获取K线数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


@router.get("/ticker", response_model=TickerData)
async def get_ticker(
    symbol: str = Query(default="BTC/USDT", description="交易对，如 BTC/USDT")
):
    """
    获取实时行情数据
    
    返回指定交易对的实时价格、买卖价、24h涨跌幅等信息
    """
    try:
        connector = get_exchange_connector()
        ticker_data = connector.get_ticker(symbol=symbol)
        
        return TickerData(**ticker_data)
    except Exception as e:
        logger.error(f"获取实时行情失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取实时行情失败: {str(e)}")


@router.get("/symbols", response_model=SymbolListResponse)
async def get_symbols(
    quote: str = Query(default="USDT", description="计价货币"),
    active_only: bool = Query(default=True, description="是否只返回活跃交易对")
):
    """
    获取交易对列表
    
    返回指定计价货币的所有交易对
    """
    try:
        connector = get_exchange_connector()
        symbols_data = connector.get_symbols(quote=quote, active_only=active_only)
        
        return SymbolListResponse(
            symbols=[SymbolInfo(**symbol) for symbol in symbols_data],
            count=len(symbols_data)
        )
    except Exception as e:
        logger.error(f"获取交易对列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取交易对列表失败: {str(e)}")


@router.get("/stats", response_model=MarketStats)
async def get_market_stats(
    symbol: str = Query(default="BTC/USDT", description="交易对，如 BTC/USDT")
):
    """
    获取市场统计数据（24h数据）
    
    返回24小时内的最高价、最低价、成交量、涨跌幅等统计信息
    """
    try:
        connector = get_exchange_connector()
        stats_data = connector.get_market_stats(symbol=symbol)
        
        return MarketStats(**stats_data)
    except Exception as e:
        logger.error(f"获取市场统计数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取市场统计数据失败: {str(e)}")


@router.get("/health")
async def health_check():
    """
    健康检查
    
    检查交易所连接是否正常
    """
    try:
        connector = get_exchange_connector()
        # 尝试获取一个简单的数据来验证连接
        ticker = connector.get_ticker()
        return {
            "status": "healthy",
            "exchange": connector.exchange_id,
            "message": "交易所连接正常"
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(status_code=503, detail=f"交易所连接异常: {str(e)}")

