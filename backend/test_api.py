"""
API 测试脚本
用于测试 CryptoGo API 的各个端点
"""
import requests
import json

BASE_URL = "http://localhost:8000"


def print_json(data, title=""):
    """格式化打印 JSON 数据"""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print('='*60)
    print(json.dumps(data, indent=2, ensure_ascii=False))


def test_root():
    """测试根路径"""
    response = requests.get(f"{BASE_URL}/")
    print_json(response.json(), "根路径")


def test_health():
    """测试健康检查"""
    response = requests.get(f"{BASE_URL}/health")
    print_json(response.json(), "健康检查")


def test_market_health():
    """测试市场健康检查"""
    response = requests.get(f"{BASE_URL}/api/v1/market/health")
    print_json(response.json(), "市场健康检查")


def test_klines():
    """测试K线数据"""
    params = {
        "symbol": "BTC/USDT",
        "interval": "1h",
        "limit": 5
    }
    response = requests.get(f"{BASE_URL}/api/v1/market/klines", params=params)
    data = response.json()
    print_json(data, f"K线数据 ({data['count']}条)")


def test_ticker():
    """测试实时价格"""
    params = {"symbol": "BTC/USDT"}
    response = requests.get(f"{BASE_URL}/api/v1/market/ticker", params=params)
    print_json(response.json(), "实时价格")


def test_stats():
    """测试市场统计"""
    params = {"symbol": "BTC/USDT"}
    response = requests.get(f"{BASE_URL}/api/v1/market/stats", params=params)
    print_json(response.json(), "24h市场统计")


def test_symbols():
    """测试交易对列表"""
    params = {"quote": "USDT"}
    response = requests.get(f"{BASE_URL}/api/v1/market/symbols", params=params)
    data = response.json()
    # 只显示前5个
    data['symbols'] = data['symbols'][:5]
    print_json(data, f"交易对列表 (总共{data['count']}个，显示前5个)")


def main():
    """运行所有测试"""
    print("\n" + "🚀 CryptoGo API 测试".center(60, "="))
    
    try:
        test_root()
        test_health()
        test_market_health()
        test_klines()
        test_ticker()
        test_stats()
        test_symbols()
        
        print(f"\n{'='*60}")
        print("✅ 所有测试完成！")
        print('='*60 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到服务器")
        print("请确保后端服务正在运行：")
        print("  cd backend && source venv/bin/activate && uvicorn app.main:app --reload\n")
    except Exception as e:
        print(f"\n❌ 错误：{str(e)}\n")


if __name__ == "__main__":
    main()

