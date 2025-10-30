"""
Trading Agent 测试脚本
测试基于 DeepSeek Function Calling 的 Agent（支持后台挂机）
创建时间: 2025-10-29
"""
import asyncio
import time
from app.utils.database import get_db
from app.repositories.trading_session_repo import TradingSessionRepository
from app.services.trading_agent_service import run_trading_agent, get_background_agent_manager
from app.utils.logging import get_logger

logger = get_logger(__name__)


async def test_agent_once():
    """测试单次运行 Agent"""
    print("\n" + "="*60)
    print("测试 1: 单次运行 Agent")
    print("="*60 + "\n")
    
    # 使用测试会话 ID
    test_session_id = 999999
    
    print("运行 Agent...")
    result = await run_trading_agent(
        session_id=test_session_id,
        symbols=["BTC/USDT:USDT"],
        risk_params={
            "max_position_size": 0.2,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
            "max_leverage": 3,
            "max_positions": 3
        },
        max_iterations=10,
        model="deepseek-chat"
    )
    
    print("\n" + "="*60)
    print("决策结果:")
    print("="*60)
    print(f"成功: {result['success']}")
    print(f"迭代次数: {result['iterations']}")
    print(f"使用的工具: {len(result.get('tools_used', []))} 个")
    
    if result.get('tools_used'):
        print("\n工具调用:")
        for i, tool in enumerate(result['tools_used'], 1):
            print(f"  {i}. {tool['name']}")
    
    if result.get('decision'):
        print("\n" + "="*60)
        print("AI 决策:")
        print("="*60)
        # 只显示前500字符
        decision = result['decision']
        print(decision[:500] + "..." if len(decision) > 500 else decision)
    
    if result.get('error'):
        print(f"\n❌ 错误: {result['error']}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


def test_background_agent():
    """测试后台挂机 Agent"""
    print("\n" + "="*60)
    print("测试 2: 后台挂机 Agent")
    print("="*60 + "\n")
    
    # 创建测试会话
    db = next(get_db())
    try:
        session_repo = TradingSessionRepository(db)
        
        # 检查是否有活跃会话
        active_session = session_repo.get_active_session()
        
        if not active_session:
            # 创建新会话
            print("创建测试会话...")
            session = session_repo.create_session(
                session_name="Background Agent Test",
                initial_capital=10000.0,
                config={"test": True}
            )
            print(f"✅ 会话已创建: {session.id}")
        else:
            session = active_session
            print(f"✅ 使用现有会话: {session.id}")
        
        session_id = session.id
        
    finally:
        db.close()
    
    # 启动后台 Agent
    print("\n启动后台 Agent...")
    manager = get_background_agent_manager()
    
    try:
        result = manager.start_background_agent(
            session_id=session_id,
            symbols=["BTC/USDT:USDT"],
            risk_params={
                "max_position_size": 0.2,
                "stop_loss_pct": 0.05,
                "take_profit_pct": 0.10,
                "max_leverage": 3,
                "max_positions": 3
            },
            decision_interval=30,  # 30秒一次（快速测试）
            model="deepseek-chat",
            max_iterations=10
        )
        print(f"✅ 后台 Agent 已启动: {result}")
    except ValueError as e:
        print(f"⚠️ Agent 已在运行: {e}")
    
    # 监控运行
    print("\n监控后台 Agent (60秒)...")
    for i in range(6):
        time.sleep(10)
        status = manager.get_agent_status(session_id)
        
        if status:
            print(f"  [{i*10}s] 状态: {status['status']}, "
                  f"运行次数: {status['run_count']}, "
                  f"最后运行: {status['last_run_time'] or '未运行'}")
        else:
            print(f"  [{i*10}s] Agent 未运行")
            break
    
    # 停止 Agent
    print("\n停止后台 Agent...")
    try:
        result = manager.stop_background_agent(session_id)
        print(f"✅ Agent 已停止: {result}")
    except ValueError as e:
        print(f"⚠️ {e}")
    
    # 验证已停止
    time.sleep(2)
    status = manager.get_agent_status(session_id)
    if status is None:
        print("✅ Agent 状态已清除")
    else:
        print(f"⚠️ Agent 状态仍存在: {status['status']}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


def test_list_agents():
    """测试列出所有 Agent"""
    print("\n" + "="*60)
    print("测试 3: 列出所有运行的 Agent")
    print("="*60 + "\n")
    
    manager = get_background_agent_manager()
    agents = manager.list_agents()
    
    print(f"运行中的 Agent 数量: {len(agents)}")
    
    for agent in agents:
        if agent:
            print(f"\n  Session {agent['session_id']}:")
            print(f"    状态: {agent['status']}")
            print(f"    运行次数: {agent['run_count']}")
            print(f"    配置: {agent['config']['symbols']}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60 + "\n")


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*60)
    print("CryptoGo Trading Agent 测试")
    print("基于 DeepSeek Function Calling + 后台挂机")
    print("="*60)
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        
        if test_name == "once":
            asyncio.run(test_agent_once())
        elif test_name == "background":
            test_background_agent()
        elif test_name == "list":
            test_list_agents()
        else:
            print(f"\n未知测试: {test_name}")
            print("\n可用测试:")
            print("  once       - 单次运行 Agent")
            print("  background - 后台挂机 Agent")
            print("  list       - 列出运行的 Agent")
    else:
        print("\n使用方法:")
        print("  python test_agent.py once       # 单次运行")
        print("  python test_agent.py background # 后台挂机")
        print("  python test_agent.py list       # 列出 Agent")
        print("\n运行默认测试 (once)...\n")
        asyncio.run(test_agent_once())
