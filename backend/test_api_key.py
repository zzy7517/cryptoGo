"""
测试币安 API 密钥的有效性和权限
"""
import ccxt
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_SECRET')

print(f"API Key: {api_key[:10]}..." if api_key else "未找到 API Key")
print("-" * 50)

# 测试币安连接
print("\n测试币安连接...")
try:
    exchange = ccxt.binance({
        'apiKey': api_key,
        'secret': api_secret,
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })

    # 尝试获取账户信息
    account = exchange.fapiPrivateV2GetAccount()
    print("✅ 连接成功！")
    print(f"   账户余额: {account.get('totalWalletBalance', 0)} USDT")
    print(f"   可用余额: {account.get('availableBalance', 0)} USDT")
    print(f"   未实现盈亏: {account.get('totalUnrealizedProfit', 0)} USDT")
    print(f"   可交易: {account.get('canTrade', False)}")

except Exception as e:
    print(f"❌ 连接失败: {str(e)}")

print("\n" + "=" * 50)
