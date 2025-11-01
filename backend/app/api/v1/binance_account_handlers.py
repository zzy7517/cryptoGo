"""
币安账户信息处理函数
提供获取币安账户余额、持仓等实时信息的接口
创建时间: 2025-10-31
"""
from fastapi import HTTPException
from app.services.binance_account_service import get_binance_account_service
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def get_binance_account_info():
    """
    获取币安账户信息

    返回账户余额、可用资金、未实现盈亏等信息
    """
    try:
        service = get_binance_account_service()
        account_info = service.get_account_info()

        return {
            "success": True,
            "data": account_info
        }

    except Exception as e:
        logger.error(f"获取币安账户信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取币安账户信息失败: {str(e)}"
        )


async def get_binance_positions():
    """
    获取币安持仓信息

    返回当前所有活跃持仓
    """
    try:
        service = get_binance_account_service()
        positions = service.get_positions()

        return {
            "success": True,
            "data": positions,
            "count": len(positions)
        }

    except Exception as e:
        logger.error(f"获取币安持仓信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取币安持仓信息失败: {str(e)}"
        )


async def get_binance_account_summary():
    """
    获取币安账户摘要

    返回账户信息和持仓信息的完整摘要
    """
    try:
        service = get_binance_account_service()
        summary = service.get_account_summary()

        return {
            "success": True,
            "data": summary
        }

    except Exception as e:
        logger.error(f"获取币安账户摘要失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取币安账户摘要失败: {str(e)}"
        )
