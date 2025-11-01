"""
Config 处理函数
返回系统配置信息
创建时间: 2025-11-01
"""
from typing import List
from pydantic import BaseModel, Field
from ...utils.logging import get_logger

logger = get_logger(__name__)


class TradingPairConfig(BaseModel):
    """交易对配置"""
    symbol: str = Field(..., description="交易对符号，如 'BTC/USDT:USDT'")
    name: str = Field(..., description="币种名称，如 '比特币'")
    description: str = Field(None, description="描述信息")


class TradingPairsResponse(BaseModel):
    """交易对配置响应"""
    success: bool = Field(True, description="是否成功")
    data: List[TradingPairConfig] = Field(..., description="交易对列表")


async def get_trading_pairs() -> TradingPairsResponse:
    """
    获取默认交易对配置

    Returns:
        交易对列表
    """
    # 默认交易对配置（与前端 tradingPairs.ts 保持一致）
    trading_pairs = [
        {
            "symbol": "BTC/USDT:USDT",
            "name": "比特币",
            "description": "Bitcoin 永续合约"
        },
        {
            "symbol": "ETH/USDT:USDT",
            "name": "以太坊",
            "description": "Ethereum 永续合约"
        },
        {
            "symbol": "DOGE/USDT:USDT",
            "name": "狗狗币",
            "description": "Dogecoin 永续合约"
        }
    ]

    return TradingPairsResponse(
        success=True,
        data=[TradingPairConfig(**pair) for pair in trading_pairs]
    )
