"""
Trading Agent 测试脚本
测试 LangGraph Agent 的基本功能
创建时间: 2025-10-29
"""
import asyncio
import time
from app.core.database import get_db
from app.repositories.trading_session_repo import TradingSessionRepository
from app.services.trading_agent_service import get_agent_service
from app.core.logging import get_logger

logger = get_logger(__name__)


def test_agent_lifecycle():
    """
    测试 Agent 生命周期：启动、运行、停止
    """
    print("\n=== 测试 Agent 生命周期 ===\n")
    
    # 1. 创建测试会话
    db = next(get_db())
    try:
        session_repo = TradingSessionRepository(db)
        
        # 检查是否有活跃会话
        active_session = session_repo.get_active_session()
        
        if not active_session:
            # 创建新会话
            print("创建测试会话...")
            session = session_repo.create_session(
                session_name="Agent Test Session",
                initial_capital=10000.0,
                config={
                    "test": True,
                    "decision_interval": 30
                }
            )
            print(f"✅ 会话已创建: {session.id}")
        else:
            session = active_session
            print(f"✅ 使用现有活跃会话: {session.id}")
        
        session_id = session.id
        
    finally:
        db.close()
    
    # 2. 启动 Agent
    print("\n启动 Agent...")
    agent_service = get_agent_service()
    
    try:
        result = agent_service.start_agent(
            session_id=session_id,
            decision_interval=30,  # 30秒一次循环（快速测试）
            symbols=["BTC/USDT:USDT"],
            initial_capital=10000.0
        )
        print(f"✅ Agent 已启动: {result}")
    except ValueError as e:
        print(f"⚠️ Agent 已在运行: {e}")
    
    # 3. 监控 Agent 运行
    print("\n监控 Agent 运行 (60秒)...")
    for i in range(6):
        time.sleep(10)
        status = agent_service.get_agent_status(session_id)
        
        if status:
            print(f"  [{i*10}s] 状态: {status['status']}, 循环: {status['loop_count']}, "
                  f"节点: {status['current_node']}, 错误: {status['error_count']}")
        else:
            print(f"  [{i*10}s] Agent 未运行")
            break
    
    # 4. 停止 Agent
    print("\n停止 Agent...")
    try:
        result = agent_service.stop_agent(session_id)
        print(f"✅ Agent 已停止: {result}")
    except ValueError as e:
        print(f"⚠️ {e}")
    
    # 5. 验证 Agent 已停止
    time.sleep(2)
    status = agent_service.get_agent_status(session_id)
    if status is None:
        print("✅ Agent 状态已清除")
    else:
        print(f"⚠️ Agent 状态仍存在: {status['status']}")
    
    print("\n=== 测试完成 ===\n")


def test_agent_status():
    """
    测试 Agent 状态查询
    """
    print("\n=== 测试 Agent 状态查询 ===\n")
    
    agent_service = get_agent_service()
    
    # 列出所有运行中的 Agent
    running_agents = agent_service.list_running_agents()
    print(f"运行中的 Agent 数量: {len(running_agents)}")
    
    for agent in running_agents:
        print(f"  - Session {agent['session_id']}: {agent['status']}, "
              f"循环 {agent['loop_count']} 次")
    
    print("\n=== 测试完成 ===\n")


def test_agent_config_update():
    """
    测试 Agent 配置更新
    """
    print("\n=== 测试 Agent 配置更新 ===\n")
    
    # 获取活跃会话
    db = next(get_db())
    try:
        session_repo = TradingSessionRepository(db)
        active_session = session_repo.get_active_session()
        
        if not active_session:
            print("⚠️ 没有活跃会话，跳过测试")
            return
        
        session_id = active_session.id
    finally:
        db.close()
    
    agent_service = get_agent_service()
    
    # 检查 Agent 是否运行
    status = agent_service.get_agent_status(session_id)
    if not status:
        print(f"⚠️ Session {session_id} 的 Agent 未运行，跳过测试")
        return
    
    print(f"当前配置: 间隔={status['decision_interval']}秒, 币种={status['symbols']}")
    
    # 更新配置
    print("\n更新配置...")
    try:
        result = agent_service.update_config(
            session_id=session_id,
            decision_interval=60,
            symbols=["BTC/USDT:USDT", "ETH/USDT:USDT"]
        )
        print(f"✅ 配置已更新: {result}")
    except Exception as e:
        print(f"❌ 更新失败: {e}")
    
    # 验证更新
    time.sleep(1)
    status = agent_service.get_agent_status(session_id)
    print(f"新配置: 间隔={status['decision_interval']}秒, 币种={status['symbols']}")
    
    print("\n=== 测试完成 ===\n")


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*50)
    print("CryptoGo Trading Agent 测试")
    print("="*50)
    
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        
        if test_name == "lifecycle":
            test_agent_lifecycle()
        elif test_name == "status":
            test_agent_status()
        elif test_name == "config":
            test_agent_config_update()
        else:
            print(f"未知测试: {test_name}")
            print("可用测试: lifecycle, status, config")
    else:
        print("使用方法:")
        print("  python test_agent.py lifecycle  # 测试生命周期")
        print("  python test_agent.py status     # 测试状态查询")
        print("  python test_agent.py config     # 测试配置更新")
        print("\n运行默认测试 (lifecycle)...\n")
        test_agent_lifecycle()

