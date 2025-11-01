"""
市场数据处理函数
所有市场数据相关的业务逻辑处理
创建时间: 2025-10-29
"""
from fastapi import HTTPException, Query
from typing import Optional

from ...schemas.market import (
    KlineResponse, 
    KlineData, 
    TickerData, 
    SymbolListResponse,
    SymbolInfo,
    FundingRateData,
    OpenInterestData,
    IndicatorsResponse
)
from ...utils.data_collector import get_exchange
from ...utils.indicators import get_indicators_calculator
from ...utils.config import settings
from ...utils.logging import get_logger

logger = get_logger(__name__)


async def get_klines(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="交易对，如 BTC/USDT"),
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
        exchange = get_exchange()
        klines_data = exchange.get_klines(symbol, interval, limit, since)
        
        return KlineResponse(
            symbol=symbol,
            interval=interval,
            data=[KlineData(**kline) for kline in klines_data],
            count=len(klines_data)
        )
    except Exception as e:
        logger.exception(f"获取K线数据失败", symbol=symbol, interval=interval, error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"获取K线数据失败: {str(e)}")


async def get_ticker(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="交易对，如 BTC/USDT")
):
    """
    获取实时行情数据
    
    返回指定交易对的实时价格、买卖价、24h涨跌幅等信息
    """
    try:
        exchange = get_exchange()
        ticker_data = exchange.get_ticker(symbol)
        
        return TickerData(**ticker_data)
    except Exception as e:
        logger.exception(f"获取实时行情失败", symbol=symbol, error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"获取实时行情失败: {str(e)}")


async def get_symbols(
    quote: str = Query(default="USDT", description="计价货币"),
    active_only: bool = Query(default=True, description="是否只返回活跃交易对")
):
    """
    获取交易对列表（从交易所获取）
    
    返回指定计价货币的所有交易对
    """
    try:
        exchange = get_exchange()
        symbols_data = exchange.get_symbols(quote=quote, active_only=active_only)
        
        return SymbolListResponse(
            symbols=[SymbolInfo(**symbol) for symbol in symbols_data],
            count=len(symbols_data)
        )
    except Exception as e:
        logger.exception(f"获取交易对列表失败", quote=quote, error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"获取交易对列表失败: {str(e)}")


async def get_funding_rate(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="交易对，如 BTC/USDT")
):
    """
    获取资金费率（仅限合约市场）
    
    返回当前资金费率和下次结算时间
    """
    try:
        exchange = get_exchange()
        funding_data = exchange.get_funding_rate(symbol)
        
        return FundingRateData(**funding_data)
    except Exception as e:
        logger.exception(f"获取资金费率失败", symbol=symbol, error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"获取资金费率失败: {str(e)}")


async def get_open_interest(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="交易对，如 BTC/USDT")
):
    """
    获取持仓量（仅限合约市场）
    
    返回当前持仓量
    """
    try:
        exchange = get_exchange()
        oi_data = exchange.get_open_interest(symbol)
        
        return OpenInterestData(**oi_data)
    except Exception as e:
        logger.exception(f"获取持仓量失败", symbol=symbol, error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"获取持仓量失败: {str(e)}")


async def get_indicators(
    symbol: str = Query(default=settings.DEFAULT_SYMBOL, description="交易对，如 BTC/USDT"),
    interval: str = Query(default="1h", description="时间周期: 1m, 5m, 15m, 1h, 4h, 1d"),
    limit: int = Query(default=100, ge=1, le=1000, description="K线数据条数"),
    include_series: bool = Query(default=False, description="是否包含时序数据")
):
    """
    获取技术指标
    
    计算并返回多种技术指标，包括：
    - EMA (20, 50)
    - MACD
    - RSI (7, 14)
    - ATR (3, 14)
    
    可选择是否返回完整时序数据
    """
    try:
        # 获取K线数据
        exchange = get_exchange()
        klines_data = exchange.get_klines(
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        
        if not klines_data:
            raise HTTPException(status_code=404, detail="无法获取K线数据")
        
        # 计算指标
        calculator = get_indicators_calculator()
        
        # 获取最新值
        latest_values = calculator.get_latest_values(klines_data)
        
        # 构建响应
        response_data = {
            "symbol": symbol,
            "interval": interval,
            "latest_values": latest_values
        }
        
        # 如果需要时序数据
        if include_series:
            all_indicators = calculator.calculate_all_indicators(klines_data)
            
            series_data = {
                "timestamps": all_indicators['timestamps'],
                "ema20": all_indicators['ema']['ema20'],
                "ema50": all_indicators['ema']['ema50'],
                "macd": all_indicators['macd']['macd'],
                "signal": all_indicators['macd']['signal'],
                "histogram": all_indicators['macd']['histogram'],
                "rsi7": all_indicators['rsi']['rsi7'],
                "rsi14": all_indicators['rsi']['rsi14'],
                "atr3": all_indicators['atr']['atr3'],
                "atr14": all_indicators['atr']['atr14'],
            }
            response_data["series_data"] = series_data
        
        return IndicatorsResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"获取技术指标失败", symbol=symbol, interval=interval, error_type=type(e).__name__)
        raise HTTPException(status_code=500, detail=f"获取技术指标失败: {str(e)}")

