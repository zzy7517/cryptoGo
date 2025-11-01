"""
测试币安账户信息和持仓信息查询
"""
import ccxt
import json
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

def test_binance_account():
    """测试币安账户信息"""

    # 初始化交易所
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_SECRET')

    print(f"API Key: {api_key[:10]}...")
    print(f"API Secret: {api_secret[:10]}...")
    print("-" * 80)

    # 初始化 ccxt 交易所
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {
            'defaultType': 'future',  # 使用合约交易
        }
    })

    try:
        # 1. 获取账户信息（合约）- 直接调用 fapi 接口
        print("\n=== 账户信息 (Futures Account) ===")
        account_info = exchange.fapiPrivateV2GetAccount()
        print(json.dumps({
            'totalWalletBalance': account_info.get('totalWalletBalance'),
            'availableBalance': account_info.get('availableBalance'),
            'totalUnrealizedProfit': account_info.get('totalUnrealizedProfit'),
            'totalMarginBalance': account_info.get('totalMarginBalance'),
            'maxWithdrawAmount': account_info.get('maxWithdrawAmount'),
            'canTrade': account_info.get('canTrade'),
            'canDeposit': account_info.get('canDeposit'),
            'canWithdraw': account_info.get('canWithdraw')
        }, indent=2))

        # 2. 显示完整账户信息结构
        print("\n=== 完整账户信息 ===")
        print(json.dumps(account_info, indent=2))

        # 4. 获取持仓信息
        print("\n=== 持仓信息 ===")
        positions = exchange.fapiPrivateV2GetPositionRisk()

        # 过滤出有持仓的记录
        active_positions = [
            pos for pos in positions
            if float(pos.get('positionAmt', 0)) != 0
        ]

        if active_positions:
            print(f"找到 {len(active_positions)} 个持仓:")
            for pos in active_positions:
                print(json.dumps({
                    'symbol': pos.get('symbol'),
                    'positionSide': pos.get('positionSide'),
                    'positionAmt': pos.get('positionAmt'),
                    'entryPrice': pos.get('entryPrice'),
                    'markPrice': pos.get('markPrice'),
                    'unRealizedProfit': pos.get('unRealizedProfit'),
                    'leverage': pos.get('leverage')
                }, indent=2))
        else:
            print("当前没有持仓")

        # 5. 显示完整的持仓数据结构（包括空持仓）
        print("\n=== 完整持仓数据结构（第一个）===")
        if positions:
            print(json.dumps(positions[0], indent=2))

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_binance_account()
