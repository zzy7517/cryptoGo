"""
账户信息处理函数
提供获取账户余额、持仓等实时信息的接口
交易所类型通过配置自动选择
创建时间: 2025-10-31

注意：虽然 get_account_info 和 get_positions 的路由端点已删除，
但底层 service 方法仍保留，因为它们被内部逻辑调用：
- get_account_info: 被 trading_agent_service 调用
- get_positions: 被 get_account_summary 内部调用
"""
from fastapi import HTTPException
from ...services.account_service import AccountService
from ...utils.logging import get_logger

logger = get_logger(__name__)


async def get_account_summary():
    """
    获取账户摘要

    自动根据配置使用对应的交易所
    返回账户信息和持仓信息的完整摘要
    """
    try:
        service = AccountService.get_instance()
        summary = service.get_account_summary()

        return {
            "success": True,
            "data": summary
        }

    except Exception as e:
        logger.error(f"获取账户摘要失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取账户摘要失败: {str(e)}"
        )
