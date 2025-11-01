"""
币安账户信息服务
用于获取币安 Demo Trading 账户的实时信息和持仓
创建时间: 2025-10-31
"""
import ccxt
from typing import Dict, Any, List, Optional
from app.utils.logging import get_logger
from app.utils.config import settings

logger = get_logger(__name__)


class BinanceAccountService:
    """币安账户信息服务"""

    def __init__(self):
        self.api_key = settings.BINANCE_API_KEY
        self.api_secret = settings.BINANCE_SECRET
        self.exchange = None
        self._initialize_exchange()

    def _initialize_exchange(self):
        """初始化交易所连接"""
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.api_secret,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'future',  # 使用合约交易
                },
                'timeout': 30000,  # 30秒超时
            }
            
            # 添加代理配置
            if settings.HTTP_PROXY or settings.HTTPS_PROXY:
                config['proxies'] = {}
                if settings.HTTP_PROXY:
                    config['proxies']['http'] = settings.HTTP_PROXY
                if settings.HTTPS_PROXY:
                    config['proxies']['https'] = settings.HTTPS_PROXY
                logger.info(f"使用代理: {config['proxies']}")
            
            self.exchange = ccxt.binance(config)

            logger.info("已连接到币安合约生产环境")

        except Exception as e:
            logger.error(f"初始化币安交易所失败: {str(e)}")
            raise

    def get_account_info(self) -> Dict[str, Any]:
        """
        获取账户信息

        Returns:
            账户信息字典，包含余额、权限等
        """
        try:
            account_info = self.exchange.fapiPrivateV2GetAccount()

            # 提取主要资产信息（USDT, BTC等）
            assets = account_info.get('assets', [])
            main_assets = {}

            for asset in assets:
                asset_name = asset.get('asset')
                wallet_balance = float(asset.get('walletBalance', 0))

                # 只保留有余额的资产
                if wallet_balance > 0:
                    main_assets[asset_name] = {
                        'walletBalance': wallet_balance,
                        'unrealizedProfit': float(asset.get('unrealizedProfit', 0)),
                        'marginBalance': float(asset.get('marginBalance', 0)),
                        'availableBalance': float(asset.get('availableBalance', 0)),
                        'maxWithdrawAmount': float(asset.get('maxWithdrawAmount', 0))
                    }

            return {
                'totalWalletBalance': float(account_info.get('totalWalletBalance', 0)),
                'availableBalance': float(account_info.get('availableBalance', 0)),
                'totalUnrealizedProfit': float(account_info.get('totalUnrealizedProfit', 0)),
                'totalMarginBalance': float(account_info.get('totalMarginBalance', 0)),
                'maxWithdrawAmount': float(account_info.get('maxWithdrawAmount', 0)),
                'canTrade': account_info.get('canTrade', False),
                'canDeposit': account_info.get('canDeposit', False),
                'canWithdraw': account_info.get('canWithdraw', False),
                'assets': main_assets,
                'updateTime': account_info.get('updateTime', 0)
            }

        except Exception as e:
            logger.error(f"获取账户信息失败: {str(e)}")
            raise

    def get_positions(self) -> List[Dict[str, Any]]:
        """
        获取持仓信息

        Returns:
            持仓列表，只返回有持仓的记录
        """
        try:
            positions = self.exchange.fapiPrivateV2GetPositionRisk()

            # 过滤出有持仓的记录
            active_positions = []
            for pos in positions:
                position_amt = float(pos.get('positionAmt', 0))
                if position_amt != 0:
                    entry_price = float(pos.get('entryPrice', 0))
                    mark_price = float(pos.get('markPrice', 0))
                    unrealized_profit = float(pos.get('unRealizedProfit', 0))

                    # 计算收益率
                    if entry_price != 0 and position_amt != 0:
                        notional = abs(position_amt * entry_price)
                        pnl_pct = (unrealized_profit / notional) * 100 if notional != 0 else 0
                    else:
                        pnl_pct = 0

                    # 判断方向（做多/做空）
                    side = 'long' if position_amt > 0 else 'short'

                    active_positions.append({
                        'symbol': pos.get('symbol'),
                        'side': side,
                        'positionSide': pos.get('positionSide'),
                        'quantity': abs(position_amt),
                        'entryPrice': entry_price,
                        'markPrice': mark_price,
                        'unrealizedProfit': unrealized_profit,
                        'unrealizedProfitPct': round(pnl_pct, 2),
                        'leverage': int(pos.get('leverage', 1)),
                        'marginType': pos.get('marginType'),
                        'liquidationPrice': float(pos.get('liquidationPrice', 0)),
                        'updateTime': pos.get('updateTime', 0)
                    })

            return active_positions

        except Exception as e:
            logger.error(f"获取持仓信息失败: {str(e)}")
            raise

    def get_account_summary(self) -> Dict[str, Any]:
        """
        获取账户摘要信息（账户信息 + 持仓信息）

        Returns:
            包含账户和持仓的完整信息
        """
        try:
            account_info = self.get_account_info()
            positions = self.get_positions()

            return {
                'account': account_info,
                'positions': positions,
                'positionsCount': len(positions)
            }

        except Exception as e:
            logger.error(f"获取账户摘要失败: {str(e)}")
            raise


# 单例实例
_binance_account_service = None


def get_binance_account_service() -> BinanceAccountService:
    """获取币安账户服务单例"""
    global _binance_account_service
    if _binance_account_service is None:
        _binance_account_service = BinanceAccountService()
    return _binance_account_service
