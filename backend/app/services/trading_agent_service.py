"""
Trading Agent Service - 定时循环版本（无 LangChain）
参考 nofx 项目逻辑：预先收集数据 -> 一次性调用 AI -> 执行决策 -> 保存
创建时间: 2025-10-30
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from decimal import Decimal
import threading
import time
import asyncio
import json
from pathlib import Path

from app.services.data_collector import get_exchange_connector
from app.services.ai_engine import get_ai_engine
from app.services.prompt_builder import build_advanced_prompt
from app.repositories.position_repo import PositionRepository
from app.repositories.ai_decision_repo import AIDecisionRepository
from app.repositories.trading_session_repo import TradingSessionRepository
from app.utils.database import get_db
from app.utils.logging import get_logger

logger = get_logger(__name__)


# ==================== 数据结构定义 ====================

class TradingContext:
    """交易上下文"""
    
    def __init__(self):
        self.current_time: str = ""
        self.call_count: int = 0
        self.session_id: int = 0
        
        # 候选交易对
        self.symbols: List[str] = []
        
        # 风险参数
        self.risk_params: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "current_time": self.current_time,
            "call_count": self.call_count,
            "session_id": self.session_id,
            "symbols": self.symbols,
            "risk_params": self.risk_params
        }


class Decision:
    """AI 决策"""
    
    def __init__(
        self,
        symbol: str,
        action: str,
        reasoning: str,
        leverage: int = 1,
        position_size_usd: float = 0,
        stop_loss_pct: Optional[float] = None,
        take_profit_pct: Optional[float] = None,
        confidence: int = 50
    ):
        self.symbol = symbol
        self.action = action  # open_long, open_short, close_long, close_short, hold, wait
        self.reasoning = reasoning
        self.leverage = leverage
        self.position_size_usd = position_size_usd
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.confidence = confidence
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "action": self.action,
            "reasoning": self.reasoning,
            "leverage": self.leverage,
            "position_size_usd": self.position_size_usd,
            "stop_loss_pct": self.stop_loss_pct,
            "take_profit_pct": self.take_profit_pct,
            "confidence": self.confidence
        }


# ==================== AI 决策函数 ====================

def build_system_prompt(risk_params: Dict[str, Any]) -> str:
    """构建系统提示词"""
    try:
        # 从文件加载提示词模板
        prompt_file = Path(__file__).parent.parent / "prompts" / "trading_system_prompt.txt"
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            template = f.read()
        
        # 填充参数
        prompt = template.format(
            symbols=', '.join(risk_params.get('symbols', [])),
            max_position_size=risk_params.get('max_position_size', 0.2) * 100,
            stop_loss_pct=risk_params.get('stop_loss_pct', 0.05) * 100,
            take_profit_pct=risk_params.get('take_profit_pct', 0.10) * 100,
            max_leverage=risk_params.get('max_leverage', 3)
        )
        
        return prompt
        
    except Exception as e:
        logger.error(f"❌ 加载系统提示词失败: {e}")
        # 返回简单的默认提示词
        return "你是一个专业的加密货币交易 AI 助手。"


def parse_ai_response(response: str) -> List[Decision]:
    """
    解析 AI 响应，提取决策列表
    
    Args:
        response: AI 响应文本
        
    Returns:
        决策列表
    """
    logger.info("🔍 开始解析 AI 响应")
    
    try:
        # 查找 JSON 数组
        json_start = response.find('[')
        json_end = response.rfind(']') + 1
        
        if json_start == -1 or json_end == 0:
            logger.warning("⚠️ 未找到 JSON 数组，返回空决策列表")
            return []
        
        json_str = response[json_start:json_end]
        
        # 解析 JSON
        decisions_data = json.loads(json_str)
        
        # 转换为 Decision 对象
        decisions = []
        for data in decisions_data:
            decision = Decision(
                symbol=data.get('symbol', ''),
                action=data.get('action', 'wait'),
                reasoning=data.get('reasoning', ''),
                leverage=data.get('leverage', 1),
                position_size_usd=data.get('position_size_usd', 0),
                stop_loss_pct=data.get('stop_loss_pct'),
                take_profit_pct=data.get('take_profit_pct'),
                confidence=data.get('confidence', 50)
            )
            decisions.append(decision)
        
        logger.info(f"✅ 成功解析 {len(decisions)} 个决策")
        return decisions
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ JSON 解析失败: {e}")
        return []
    except Exception as e:
        logger.error(f"❌ 解析 AI 响应失败: {e}")
        return []


async def get_ai_decision(
    context: TradingContext,
    start_time: datetime
) -> tuple[str, List[Decision], str]:
    """
    调用 AI 获取交易决策（一次性调用）
    
    Args:
        context: 交易上下文
        start_time: 交易开始时间
        
    Returns:
        (AI 完整响应, 决策列表, 用户提示词)
    """
    logger.info("🤖 开始调用 AI 进行决策")
    
    try:
        # 构建系统提示词
        system_prompt = build_system_prompt(context.risk_params)
        
        # 构建用户提示词（使用高级提示词）
        logger.info("📝 构建高级提示词")
        user_prompt = await build_advanced_prompt(
            session_id=context.session_id,
            symbols=context.symbols,
            call_count=context.call_count,
            start_time=start_time
        )
        
        # 调用 AI
        ai_engine = get_ai_engine()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = ai_engine.chat(messages, temperature=0.3)
        
        logger.info("✅ AI 调用成功")
        logger.debug(f"AI 响应: {response}")
        
        # 解析决策
        decisions = parse_ai_response(response)
        
        return response, decisions, user_prompt
        
    except Exception as e:
        logger.error(f"❌ AI 调用失败: {e}")
        raise


# ==================== 决策执行函数 ====================

async def execute_decision(decision: Decision, session_id: int) -> Dict[str, Any]:
    """
    执行单个决策
    
    Args:
        decision: 决策对象
        session_id: 交易会话 ID
        
    Returns:
        执行结果
    """
    logger.info(f"🔧 执行决策: {decision.symbol} {decision.action}")
    
    try:
        db = next(get_db())
        try:
            position_repo = PositionRepository(db)
            exchange = get_exchange_connector()
            
            # 根据不同的 action 执行不同的操作
            if decision.action == "open_long":
                # 开多仓
                ticker = exchange.get_ticker(decision.symbol)
                entry_price = ticker.get('last')
                
                # 计算购买数量
                quantity = decision.position_size_usd / entry_price if entry_price > 0 else 0
                
                position = position_repo.create_position(
                    session_id=session_id,
                    symbol=decision.symbol,
                    side='long',
                    quantity=Decimal(str(quantity)),
                    entry_price=Decimal(str(entry_price)),
                    leverage=decision.leverage,
                    stop_loss=Decimal(str(entry_price * (1 - decision.stop_loss_pct / 100))) if decision.stop_loss_pct else None,
                    take_profit=Decimal(str(entry_price * (1 + decision.take_profit_pct / 100))) if decision.take_profit_pct else None
                )
                
                logger.info(f"✅ 开多仓成功: {decision.symbol}, 仓位ID={position.id}")
                return {"success": True, "action": "open_long", "position_id": position.id}
                
            elif decision.action == "open_short":
                # 开空仓
                ticker = exchange.get_ticker(decision.symbol)
                entry_price = ticker.get('last')
                
                # 计算卖空数量
                quantity = decision.position_size_usd / entry_price if entry_price > 0 else 0
                
                position = position_repo.create_position(
                    session_id=session_id,
                    symbol=decision.symbol,
                    side='short',
                    quantity=Decimal(str(quantity)),
                    entry_price=Decimal(str(entry_price)),
                    leverage=decision.leverage,
                    stop_loss=Decimal(str(entry_price * (1 + decision.stop_loss_pct / 100))) if decision.stop_loss_pct else None,
                    take_profit=Decimal(str(entry_price * (1 - decision.take_profit_pct / 100))) if decision.take_profit_pct else None
                )
                
                logger.info(f"✅ 开空仓成功: {decision.symbol}, 仓位ID={position.id}")
                return {"success": True, "action": "open_short", "position_id": position.id}
                
            elif decision.action in ["close_long", "close_short"]:
                # 平仓：查找对应的持仓
                side = "long" if decision.action == "close_long" else "short"
                positions = position_repo.get_active_positions(session_id)
                
                target_position = None
                for pos in positions:
                    if pos.symbol == decision.symbol and pos.side == side:
                        target_position = pos
                        break
                
                if not target_position:
                    logger.warning(f"⚠️ 未找到要平仓的持仓: {decision.symbol} {side}")
                    return {"success": False, "error": "持仓不存在"}
                
                # 获取当前价格
                ticker = exchange.get_ticker(decision.symbol)
                exit_price = ticker.get('last')
                
                # 平仓
                position_repo.close_position(target_position.id, Decimal(str(exit_price)))
                
                logger.info(f"✅ 平仓成功: {decision.symbol} {side}, 仓位ID={target_position.id}")
                return {"success": True, "action": decision.action, "position_id": target_position.id}
                
            elif decision.action == "hold":
                # 保持持仓不变
                logger.info(f"⏸️ 保持持仓: {decision.symbol}")
                return {"success": True, "action": "hold"}
                
            elif decision.action == "wait":
                # 观望，不做任何操作
                logger.info(f"👀 观望: {decision.symbol}")
                return {"success": True, "action": "wait"}
                
            else:
                logger.warning(f"⚠️ 未知的操作类型: {decision.action}")
                return {"success": False, "error": f"未知操作: {decision.action}"}
                
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"❌ 执行决策失败: {e}")
        return {"success": False, "error": str(e)}


# ==================== Trading Agent 主类（定时循环版本）====================

class TradingAgentService:
    """
    基于定时循环的交易 Agent 服务
    
    参考 nofx 项目逻辑：
    1. 使用定时器触发周期性决策
    2. 每个周期独立：收集数据 -> 调用 AI -> 执行决策 -> 保存
    3. 不使用 LangChain，直接调用 AI API
    """
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.call_count = 0
        self.is_running = False
        self.start_time = datetime.now()
    
    async def run_decision_cycle(
        self,
        symbols: List[str],
        risk_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        运行一次完整的决策周期
        
        Args:
            symbols: 交易对列表
            risk_params: 风险参数
            
        Returns:
            决策结果
        """
        self.call_count += 1
        
        logger.info("=" * 80)
        logger.info(f"⏰ 决策周期 #{self.call_count} 开始")
        logger.info(f"📌 Session ID: {self.session_id}")
        logger.info(f"📌 交易对: {symbols}")
        logger.info("=" * 80)
        
        try:
            # 1. 构建交易上下文
            context = TradingContext()
            context.current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            context.call_count = self.call_count
            context.session_id = self.session_id
            context.symbols = symbols
            context.risk_params = risk_params
            context.risk_params['symbols'] = symbols  # 添加到 risk_params 供提示词使用
            
            # 2. 调用 AI 获取决策（使用高级提示词）
            logger.info("🤖 调用 AI 进行决策分析...")
            ai_response, decisions, user_prompt = await get_ai_decision(
                context, 
                start_time=self.start_time
            )
            
            logger.info(f"✅ AI 决策完成，共 {len(decisions)} 个决策")
            
            # 打印 AI 响应
            logger.info("=" * 80)
            logger.info("💭 AI 分析结果:")
            logger.info("=" * 80)
            logger.info(ai_response)
            logger.info("=" * 80)
            
            # 打印决策列表
            logger.info(f"📋 决策列表 ({len(decisions)} 个):")
            for i, d in enumerate(decisions, 1):
                logger.info(f"  [{i}] {d.symbol} - {d.action}")
                logger.info(f"      理由: {d.reasoning}")
                if d.action in ["open_long", "open_short"]:
                    logger.info(f"      杠杆: {d.leverage}x, 仓位: ${d.position_size_usd:.2f}")
                    logger.info(f"      止损: {d.stop_loss_pct}%, 止盈: {d.take_profit_pct}%")
                    logger.info(f"      信心度: {d.confidence}%")
            
            # 3. 执行决策
            logger.info("🔧 开始执行决策...")
            execution_results = []
            
            for i, decision in enumerate(decisions, 1):
                logger.info(f"执行决策 [{i}/{len(decisions)}]: {decision.symbol} {decision.action}")
                
                result = await execute_decision(decision, self.session_id)
                execution_results.append({
                    "decision": decision.to_dict(),
                    "result": result
                })
                
                # 短暂延迟
                if result.get('success'):
                    await asyncio.sleep(0.5)
            
            logger.info("✅ 决策执行完成")
            
            # 4. 保存决策记录到数据库
            await self._save_decision(
                ai_response=ai_response,
                decisions=decisions,
                execution_results=execution_results,
                context=context,
                user_prompt=user_prompt  # 传递完整的用户prompt
            )
            
            logger.info("✅" * 30)
            logger.info(f"✅ 决策周期 #{self.call_count} 完成")
            logger.info("✅" * 30)
            
            return {
                "success": True,
                "call_count": self.call_count,
                "decisions_count": len(decisions),
                "ai_response": ai_response,
                "decisions": [d.to_dict() for d in decisions],
                "execution_results": execution_results
            }
            
        except Exception as e:
            logger.exception(f"❌ 决策周期失败: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "call_count": self.call_count
            }
    
    async def _save_decision(
        self,
        ai_response: str,
        decisions: List[Decision],
        execution_results: List[Dict],
        context: TradingContext,
        user_prompt: str = ""
    ) -> None:
        """保存决策到数据库"""
        try:
            db = next(get_db())
            try:
                decision_repo = AIDecisionRepository(db)

                # 提取所有涉及的交易对
                symbols = list(set([d.symbol for d in decisions]))

                # 判断决策类型（简化处理）
                decision_type = "hold"
                for d in decisions:
                    if d.action == "open_long":
                        decision_type = "buy"
                        break
                    elif d.action == "open_short":
                        decision_type = "sell"
                        break

                # 计算平均信心度
                avg_confidence = sum([d.confidence for d in decisions]) / len(decisions) if decisions else 50

                # 保存决策（prompt_data存储完整的用户输入prompt）
                decision_repo.save_decision(
                    session_id=self.session_id,
                    symbols=symbols,
                    decision_type=decision_type,
                    confidence=Decimal(str(avg_confidence / 100)),
                    prompt_data={
                        "user_prompt": user_prompt,  # 完整的用户prompt
                        "context": context.to_dict()  # 上下文信息
                    },
                    ai_response=ai_response,
                    reasoning=ai_response[:500],  # 截取前500字符
                    suggested_actions={
                        "decisions": [d.to_dict() for d in decisions],
                        "execution_results": execution_results
                    },
                    executed=True
                )

                logger.info("💾 决策已保存到数据库")

            finally:
                db.close()

        except Exception as e:
            logger.exception(f"❌ 保存决策失败: {e}")


# ==================== 后台循环管理器 ====================

class BackgroundAgentManager:
    """后台 Agent 管理器 - 定时循环版本"""
    
    def __init__(self):
        self._agents: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        logger.info("BackgroundAgentManager 已初始化（定时循环版本）")
    
    def start_background_agent(
        self,
        session_id: int,
        symbols: List[str],
        risk_params: Optional[Dict[str, Any]] = None,
        decision_interval: int = 180  # 默认3分钟
    ) -> Dict[str, Any]:
        """
        启动后台 Agent（定时循环）
        
        Args:
            session_id: 交易会话 ID
            symbols: 交易对列表
            risk_params: 风险参数
            decision_interval: 决策间隔（秒），默认180秒（3分钟）
        """
        with self._lock:
            if session_id in self._agents:
                raise ValueError(f"Session {session_id} 的 Agent 已在运行")
            
            if risk_params is None:
                risk_params = {
                    "max_position_size": 0.2,
                    "stop_loss_pct": 0.05,
                    "take_profit_pct": 0.10,
                    "max_leverage": 3
                }
            
            stop_event = threading.Event()
            
            thread = threading.Thread(
                target=self._run_background_loop,
                args=(session_id, symbols, risk_params, decision_interval, stop_event),
                daemon=True,
                name=f"BackgroundAgent-{session_id}"
            )
            
            self._agents[session_id] = {
                'thread': thread,
                'stop_event': stop_event,
                'config': {
                    'symbols': symbols,
                    'risk_params': risk_params,
                    'decision_interval': decision_interval
                },
                'status': 'starting',
                'started_at': datetime.now(),
                'last_run_time': None,
                'run_count': 0,
                'last_error': None
            }
            
            thread.start()
            
            logger.info(f"✅ 后台 Agent 已启动", session_id=session_id, interval=decision_interval)
            
            return {
                'session_id': session_id,
                'status': 'started',
                'decision_interval': decision_interval,
                'symbols': symbols
            }
    
    def stop_background_agent(self, session_id: int) -> Dict[str, Any]:
        """停止后台 Agent"""
        logger.info(f"🛑 [stop_background_agent] 开始 - Session {session_id} 获取锁...")
        with self._lock:
            logger.info(f"✅ [stop_background_agent] 已获取锁")
            if session_id not in self._agents:
                logger.error(f"❌ [stop_background_agent] Session {session_id} 的 Agent 未运行")
                raise ValueError(f"Session {session_id} 的 Agent 未运行")
            
            agent = self._agents[session_id]
            logger.info(f"🚩 [stop_background_agent] 设置停止信号...")
            agent['stop_event'].set()
            agent['status'] = 'stopping'
        logger.info(f"⏳ [stop_background_agent] 等待线程结束 (最多10秒)...")
        agent['thread'].join(timeout=10)
        logger.info(f"✅ [stop_background_agent] 线程 join 完成")
        logger.info(f"📌 [stop_background_agent] 线程最终状态 - 存活: {agent['thread'].is_alive()}")
        
        logger.info(f"🔒 [stop_background_agent] 再次获取锁以清理...")
        with self._lock:
            logger.info(f"✅ [stop_background_agent] 已获取锁")
            stopped_agent = self._agents.pop(session_id, None)
            logger.info(f"🗑️ [stop_background_agent] 已从字典中移除 Agent")
        
        logger.info(f"⏹️ [stop_background_agent] 后台 Agent 已停止 - Session {session_id}")
        
        return {
            'session_id': session_id,
            'status': 'stopped',
            'run_count': stopped_agent['run_count'] if stopped_agent else 0
        }
    
    def get_agent_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取 Agent 状态"""
        with self._lock:
            agent = self._agents.get(session_id)
            
            if not agent:
                return None
            
            return {
                'session_id': session_id,
                'status': agent['status'],
                'started_at': agent['started_at'].isoformat(),
                'last_run_time': agent['last_run_time'].isoformat() if agent['last_run_time'] else None,
                'run_count': agent['run_count'],
                'config': agent['config'],
                'last_error': agent['last_error'],
                'is_alive': agent['thread'].is_alive()
            }
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """列出所有运行中的 Agent"""
        with self._lock:
            return [self.get_agent_status(sid) for sid in self._agents.keys()]
    
    def _run_background_loop(
        self,
        session_id: int,
        symbols: List[str],
        risk_params: Dict[str, Any],
        decision_interval: int,
        stop_event: threading.Event
    ):
        """
        后台循环（参考 nofx 的定时循环逻辑）
        
        使用 time.sleep 等待固定间隔，每个周期调用一次决策
        """
        logger.info("🔄" * 30)
        logger.info("🔄 后台循环启动")
        logger.info(f"📌 Session ID: {session_id}")
        logger.info(f"📌 决策间隔: {decision_interval}秒")
        logger.info("🔄" * 30)
        
        with self._lock:
            if session_id in self._agents:
                self._agents[session_id]['status'] = 'running'
        
        # 创建 Agent 实例
        agent = TradingAgentService(session_id)
        
        # 为这个线程创建一个持久的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 首次立即执行
            logger.info("🚀 执行首次决策周期...")
            try:
                result = loop.run_until_complete(agent.run_decision_cycle(symbols, risk_params))
                
                with self._lock:
                    if session_id in self._agents:
                        self._agents[session_id]['run_count'] += 1
                        self._agents[session_id]['last_run_time'] = datetime.now()
                        self._agents[session_id]['last_error'] = None
                
                logger.info(f"✅ 首次决策完成, 成功={result.get('success')}")
                
            except Exception as e:
                logger.exception(f"❌ 首次决策失败: {e}")
                
                with self._lock:
                    if session_id in self._agents:
                        self._agents[session_id]['last_error'] = str(e)
            
            # 定时循环
            loop_count = 1
            while not stop_event.is_set():
                # 等待下一个周期
                logger.info(f"😴 等待 {decision_interval}秒 后进行下一次决策...")
                logger.info(f"🚩 [循环] 停止信号状态: {stop_event.is_set()}")
                
                # 使用 stop_event.wait 代替 time.sleep，这样可以快速响应停止信号
                logger.info(f"⏳ [循环] 开始等待 (timeout={decision_interval}秒)...")
                wait_result = stop_event.wait(timeout=decision_interval)
                logger.info(f"✅ [循环] 等待结束, wait 返回值: {wait_result}")
                logger.info(f"🚩 [循环] 停止信号状态: {stop_event.is_set()}")
                
                if wait_result:
                    # 如果是因为停止信号而返回，退出循环
                    logger.info(f"🛑 [循环] 收到停止信号，退出循环")
                    break
                
                loop_count += 1
                loop_start = time.time()
                
                logger.info("🔄" * 30)
                logger.info(f"🔄 决策周期 #{loop_count} 开始")
                logger.info(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                try:
                    result = loop.run_until_complete(agent.run_decision_cycle(symbols, risk_params))
                    
                    with self._lock:
                        if session_id in self._agents:
                            self._agents[session_id]['run_count'] += 1
                            self._agents[session_id]['last_run_time'] = datetime.now()
                            self._agents[session_id]['last_error'] = None
                    
                    logger.info(f"✅ 决策周期 #{loop_count} 完成, 成功={result.get('success')}")
                    
                    # 检查会话状态
                    if not self._check_session_running(session_id):
                        logger.warning("⚠️ 会话已结束，停止循环")
                        break
                    
                except Exception as e:
                    logger.exception(f"❌ 决策周期 #{loop_count} 失败: {e}")
                    
                    with self._lock:
                        if session_id in self._agents:
                            self._agents[session_id]['last_error'] = str(e)
                
                loop_duration = time.time() - loop_start
                logger.info(f"⏱️ 本次周期耗时: {loop_duration:.2f}秒")
                logger.info("🔄" * 30)
            
            logger.info("🛑" * 30)
            logger.info("🛑 后台循环正常结束")
            logger.info(f"📊 总循环次数: {loop_count}")
            logger.info("🛑" * 30)
            
        except Exception as e:
            logger.exception(f"💥 后台循环异常终止: {e}")
            
            with self._lock:
                if session_id in self._agents:
                    self._agents[session_id]['status'] = 'crashed'
                    self._agents[session_id]['last_error'] = str(e)
            
            # Agent 崩溃时，自动将会话状态改为 crashed
            try:
                db = next(get_db())
                try:
                    from app.services.trading_session_service import TradingSessionService
                    session_service = TradingSessionService(db)
                    session_service.end_session(
                        session_id=session_id,
                        status='crashed',
                        notes=f'Agent 异常终止: {str(e)}'
                    )
                    logger.info(f"✅ 已将会话 {session_id} 状态改为 crashed")
                except Exception as update_error:
                    logger.error(f"更新会话状态失败: {str(update_error)}")
                finally:
                    db.close()
            except Exception as db_error:
                logger.error(f"数据库操作失败: {str(db_error)}")
        
        finally:
            logger.info(f"🔚 [_run_background_loop] finally 块 - Session {session_id}")
            
            # 清理事件循环
            try:
                # 取消所有未完成的任务
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                
                # 等待所有任务完成
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                
                # 关闭事件循环
                loop.close()
                logger.info(f"✅ [_run_background_loop] 事件循环已清理")
            except Exception as e:
                logger.error(f"⚠️ [_run_background_loop] 清理事件循环失败: {e}")
            
            logger.info(f"🔒 [_run_background_loop] 获取锁以更新状态...")
            with self._lock:
                logger.info(f"✅ [_run_background_loop] 已获取锁")
                if session_id in self._agents:
                    self._agents[session_id]['status'] = 'stopped'
                    logger.info(f"✅ [_run_background_loop] 状态已更新为 stopped")
                else:
                    logger.warning(f"⚠️ [_run_background_loop] Session {session_id} 已不在 _agents 字典中")
            logger.info(f"🎬 [_run_background_loop] 线程即将退出 - Session {session_id}")
    
    def _check_session_running(self, session_id: int) -> bool:
        """检查会话是否仍在运行"""
        try:
            db = next(get_db())
            try:
                session_repo = TradingSessionRepository(db)
                session = session_repo.get_by_id(session_id)
                return session is not None and session.status == 'running'
            finally:
                db.close()
        except Exception:
            return False


# 全局单例
_background_manager: Optional[BackgroundAgentManager] = None


def get_background_agent_manager() -> BackgroundAgentManager:
    """获取后台 Agent 管理器单例"""
    global _background_manager
    
    if _background_manager is None:
        _background_manager = BackgroundAgentManager()
    
    return _background_manager


# ==================== 便捷函数 ====================

async def run_trading_agent(
    session_id: int,
    symbols: List[str],
    risk_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    运行交易 Agent 的便捷函数（单次执行）
    
    Args:
        session_id: 交易会话 ID
        symbols: 交易对列表
        risk_params: 风险参数
        
    Returns:
        决策结果
    """
    if risk_params is None:
        risk_params = {
            "max_position_size": 0.2,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
            "max_leverage": 3
        }
    
    agent = TradingAgentService(session_id)
    result = await agent.run_decision_cycle(symbols, risk_params)
    
    return result
