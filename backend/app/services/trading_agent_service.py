"""
Trading Agent Service
管理 LangGraph 交易代理的生命周期
创建时间: 2025-10-29
"""
import asyncio
import threading
import time
from typing import Dict, Optional, Any
from datetime import datetime

from app.agents.graph import create_trading_graph
from app.agents.state import create_initial_state, TradingState
from app.core.database import get_db
from app.repositories.trading_session_repo import TradingSessionRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class TradingAgentService:
    """
    交易代理服务
    
    管理多个交易会话的 Agent 实例，支持启动、停止、状态查询
    """
    
    def __init__(self):
        """初始化服务"""
        self._agents: Dict[int, Dict[str, Any]] = {}
        """运行中的 Agent 注册表 {session_id: {thread, state, stop_flag, ...}}"""
        
        self._lock = threading.Lock()
        """线程锁，保护 _agents 字典"""
        
        logger.info("TradingAgentService 已初始化")
    
    def start_agent(
        self,
        session_id: int,
        decision_interval: int = 60,
        symbols: Optional[list] = None,
        initial_capital: float = 10000.0,
        risk_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        启动交易代理
        
        Args:
            session_id: 会话 ID
            decision_interval: 决策间隔（秒）
            symbols: 交易对列表
            initial_capital: 初始资金
            risk_params: 风险参数
            
        Returns:
            启动结果
            
        Raises:
            ValueError: 如果 Agent 已在运行
        """
        with self._lock:
            if session_id in self._agents:
                raise ValueError(f"Session {session_id} 的 Agent 已在运行")
            
            # 创建初始状态
            initial_state = create_initial_state(
                session_id=session_id,
                decision_interval=decision_interval,
                symbols=symbols,
                initial_capital=initial_capital,
                risk_params=risk_params
            )
            
            # 创建停止标志
            stop_flag = threading.Event()
            
            # 创建并启动线程
            thread = threading.Thread(
                target=self._run_agent_loop,
                args=(session_id, initial_state, stop_flag),
                daemon=True,
                name=f"Agent-{session_id}"
            )
            
            # 注册 Agent
            self._agents[session_id] = {
                'thread': thread,
                'state': initial_state,
                'stop_flag': stop_flag,
                'started_at': datetime.now(),
                'status': 'starting',
                'last_loop_time': None,
                'loop_count': 0,
                'last_error': None
            }
            
            thread.start()
            
            logger.info(
                f"Agent 已启动",
                session_id=session_id,
                interval=decision_interval,
                symbols=symbols
            )
            
            return {
                'session_id': session_id,
                'status': 'started',
                'decision_interval': decision_interval,
                'symbols': symbols
            }
    
    def stop_agent(self, session_id: int) -> Dict[str, Any]:
        """
        停止交易代理
        
        Args:
            session_id: 会话 ID
            
        Returns:
            停止结果
            
        Raises:
            ValueError: 如果 Agent 不存在
        """
        with self._lock:
            if session_id not in self._agents:
                raise ValueError(f"Session {session_id} 的 Agent 未运行")
            
            agent = self._agents[session_id]
            
            # 设置停止标志
            agent['stop_flag'].set()
            agent['status'] = 'stopping'
        
        # 等待线程结束（最多10秒）
        agent['thread'].join(timeout=10)
        
        with self._lock:
            # 从注册表移除
            stopped_agent = self._agents.pop(session_id, None)
        
        logger.info(
            "Agent 已停止",
            session_id=session_id,
            loop_count=stopped_agent['loop_count'] if stopped_agent else 0
        )
        
        return {
            'session_id': session_id,
            'status': 'stopped',
            'loop_count': stopped_agent['loop_count'] if stopped_agent else 0
        }
    
    def get_agent_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        获取 Agent 状态
        
        Args:
            session_id: 会话 ID
            
        Returns:
            Agent 状态字典，如果不存在则返回 None
        """
        with self._lock:
            agent = self._agents.get(session_id)
            
            if not agent:
                return None
            
            return {
                'session_id': session_id,
                'status': agent['status'],
                'started_at': agent['started_at'].isoformat(),
                'last_loop_time': agent['last_loop_time'].isoformat() if agent['last_loop_time'] else None,
                'loop_count': agent['loop_count'],
                'current_node': agent['state'].get('current_node', 'unknown'),
                'decision_interval': agent['state'].get('decision_interval', 60),
                'symbols': agent['state'].get('symbols', []),
                'error_count': agent['state'].get('error_count', 0),
                'last_error': agent['last_error'],
                'is_alive': agent['thread'].is_alive()
            }
    
    def list_running_agents(self) -> list:
        """
        列出所有运行中的 Agent
        
        Returns:
            Agent 状态列表
        """
        with self._lock:
            return [
                self.get_agent_status(session_id)
                for session_id in self._agents.keys()
            ]
    
    def update_config(
        self,
        session_id: int,
        decision_interval: Optional[int] = None,
        symbols: Optional[list] = None,
        risk_params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        更新 Agent 配置（无需重启）
        
        Args:
            session_id: 会话 ID
            decision_interval: 新的决策间隔
            symbols: 新的交易对列表
            risk_params: 新的风险参数
            
        Returns:
            更新结果
            
        Raises:
            ValueError: 如果 Agent 不存在
        """
        with self._lock:
            if session_id not in self._agents:
                raise ValueError(f"Session {session_id} 的 Agent 未运行")
            
            agent = self._agents[session_id]
            state = agent['state']
            
            # 更新配置
            if decision_interval is not None:
                state['decision_interval'] = decision_interval
            
            if symbols is not None:
                state['symbols'] = symbols
            
            if risk_params is not None:
                state['risk_params'].update(risk_params)
            
            logger.info(
                f"Agent 配置已更新",
                session_id=session_id,
                interval=decision_interval,
                symbols=symbols
            )
            
            return {
                'session_id': session_id,
                'status': 'updated',
                'decision_interval': state['decision_interval'],
                'symbols': state['symbols']
            }
    
    def _run_agent_loop(
        self,
        session_id: int,
        initial_state: TradingState,
        stop_flag: threading.Event
    ):
        """
        Agent 循环主函数（在独立线程中运行）
        
        Args:
            session_id: 会话 ID
            initial_state: 初始状态
            stop_flag: 停止标志
        """
        logger.info(
            "Agent 循环开始",
            session_id=session_id,
            interval=initial_state['decision_interval']
        )
        
        try:
            # 创建状态图
            graph = create_trading_graph()
            
            # 当前状态
            current_state = initial_state
            
            # 更新状态为运行中
            with self._lock:
                if session_id in self._agents:
                    self._agents[session_id]['status'] = 'running'
            
            # 主循环
            while not stop_flag.is_set():
                loop_start_time = time.time()
                
                try:
                    logger.info(
                        "开始新的决策循环",
                        session_id=session_id,
                        loop_number=current_state['loop_count'] + 1
                    )
                    
                    # 执行状态图（单次迭代）
                    # LangGraph 会自动执行整个流程直到遇到 END 或回到起点
                    result = graph.invoke(current_state)
                    
                    # 更新状态
                    current_state = result
                    
                    # 更新注册表
                    with self._lock:
                        if session_id in self._agents:
                            self._agents[session_id]['state'] = current_state
                            self._agents[session_id]['loop_count'] = current_state.get('loop_count', 0)
                            self._agents[session_id]['last_loop_time'] = datetime.now()
                            self._agents[session_id]['last_error'] = current_state.get('last_error')
                    
                    # 检查是否应该停止（由 check_continue 判断）
                    if not current_state.get('should_continue', True):
                        logger.info(
                            "Agent 自动停止（会话已结束）",
                            session_id=session_id
                        )
                        break
                    
                    logger.info(
                        "决策循环完成",
                        session_id=session_id,
                        loop_count=current_state['loop_count']
                    )
                    
                except Exception as e:
                    error_msg = f"循环执行失败: {str(e)}"
                    logger.exception(
                        "循环执行失败",
                        session_id=session_id,
                        loop_count=current_state.get('loop_count', 0)
                    )
                    
                    with self._lock:
                        if session_id in self._agents:
                            self._agents[session_id]['last_error'] = error_msg
                    
                    # 发生错误时，等待一段时间再继续
                    time.sleep(10)
                
                # 计算本次循环耗时
                loop_duration = time.time() - loop_start_time
                
                # 等待至下一个决策周期
                interval = current_state.get('decision_interval', 60)
                sleep_time = max(0, interval - loop_duration)
                
                if sleep_time > 0:
                    logger.debug(
                        "等待下一个决策周期",
                        session_id=session_id,
                        sleep_seconds=round(sleep_time, 1)
                    )
                    # 使用可中断的等待
                    stop_flag.wait(timeout=sleep_time)
            
            logger.info(
                "Agent 循环结束",
                session_id=session_id,
                total_loops=current_state.get('loop_count', 0)
            )
            
        except Exception as e:
            logger.exception(
                "Agent 循环异常终止",
                session_id=session_id
            )
            
            with self._lock:
                if session_id in self._agents:
                    self._agents[session_id]['status'] = 'crashed'
                    self._agents[session_id]['last_error'] = str(e)
        
        finally:
            # 清理
            with self._lock:
                if session_id in self._agents:
                    self._agents[session_id]['status'] = 'stopped'


# 全局单例
_agent_service: Optional[TradingAgentService] = None


def get_agent_service() -> TradingAgentService:
    """
    获取 TradingAgentService 全局单例
    
    Returns:
        TradingAgentService 实例
    """
    global _agent_service
    
    if _agent_service is None:
        _agent_service = TradingAgentService()
    
    return _agent_service

