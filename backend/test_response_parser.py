"""
测试 AI 响应解析器
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.response_parser import ResponseParser


def test_parse_response():
    """测试解析AI响应"""

    # 模拟AI响应（根据系统提示词格式）
    test_response = """
# 市场分析

当前BTC处于下跌趋势，MACD出现死叉，RSI超卖。ETH跟随BTC下跌，但跌幅相对较小。

综合技术指标和市场情绪，建议：
1. BTC开空仓，目标95000，止损97500
2. ETH观望

```json
[
  {
    "symbol": "BTCUSDT",
    "action": "open_short",
    "leverage": 5,
    "position_size_usd": 5000,
    "stop_loss": 97500,
    "take_profit": 95000,
    "confidence": 85,
    "risk_usd": 300,
    "reasoning": "下跌趋势+MACD死叉+RSI超卖反弹风险控制"
  },
  {
    "symbol": "ETHUSDT",
    "action": "wait",
    "reasoning": "跟随BTC但跌幅较小，观望为主"
  }
]
```
    """

    print("=" * 80)
    print("测试 AI 响应解析器")
    print("=" * 80)

    # 解析响应
    parsed = ResponseParser.parse(test_response)

    # 打印结果
    print("\n【思维链】")
    print(parsed.thinking)

    print("\n【原始JSON】")
    print(parsed.raw_json)

    print(f"\n【决策数量】{len(parsed.decisions)}")

    print("\n【决策详情】")
    for i, decision in enumerate(parsed.decisions, 1):
        print(f"\n决策 [{i}]:")
        print(f"  币种: {decision.symbol}")
        print(f"  操作: {decision.action}")
        print(f"  理由: {decision.reasoning}")

        if decision.action in ["open_long", "open_short"]:
            print(f"  杠杆: {decision.leverage}x")
            print(f"  仓位: ${decision.position_size_usd}")
            print(f"  止损: {decision.stop_loss}")
            print(f"  止盈: {decision.take_profit}")
            print(f"  信心度: {decision.confidence}%")
            print(f"  风险: ${decision.risk_usd}")

        # 验证
        is_valid, error = decision.validate()
        if is_valid:
            print(f"  ✅ 验证通过")
        else:
            print(f"  ❌ 验证失败: {error}")

    # 打印错误
    if parsed.parsing_errors:
        print("\n【解析错误】")
        for error in parsed.parsing_errors:
            print(f"  ❌ {error}")

    # 打印摘要
    print(f"\n【摘要】{parsed.summary}")
    print(f"【状态】{'✅ 成功' if parsed.is_valid else '❌ 失败'}")

    print("\n" + "=" * 80)


def test_parse_with_percentage():
    """测试解析百分比格式"""

    test_response = """
市场分析：BTC突破阻力位，建议做多

```json
[
  {
    "symbol": "BTCUSDT",
    "action": "open_long",
    "leverage": 3,
    "position_size_usd": 3000,
    "stop_loss_pct": 2.5,
    "take_profit_pct": 5.0,
    "confidence": 75,
    "reasoning": "突破阻力位，成交量放大"
  }
]
```
    """

    print("\n" + "=" * 80)
    print("测试百分比格式解析")
    print("=" * 80)

    parsed = ResponseParser.parse(test_response)

    for i, decision in enumerate(parsed.decisions, 1):
        print(f"\n决策 [{i}]:")
        print(f"  币种: {decision.symbol}")
        print(f"  操作: {decision.action}")
        print(f"  止损百分比: {decision.stop_loss_pct}%")
        print(f"  止盈百分比: {decision.take_profit_pct}%")

        is_valid, error = decision.validate()
        print(f"  验证: {'✅ 通过' if is_valid else f'❌ 失败 - {error}'}")


def test_parse_invalid_json():
    """测试解析无效JSON"""

    test_response = """
这是一段没有JSON的响应
    """

    print("\n" + "=" * 80)
    print("测试无效响应")
    print("=" * 80)

    parsed = ResponseParser.parse(test_response)

    print(f"决策数量: {len(parsed.decisions)}")
    print(f"错误: {parsed.parsing_errors}")
    print(f"状态: {'✅ 成功' if parsed.is_valid else '❌ 失败'}")


if __name__ == "__main__":
    # 运行测试
    test_parse_response()
    test_parse_with_percentage()
    test_parse_invalid_json()

    print("\n" + "=" * 80)
    print("✅ 所有测试完成")
    print("=" * 80)
