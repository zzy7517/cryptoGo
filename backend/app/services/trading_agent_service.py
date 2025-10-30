"""
Trading Agent Service
基于 LangChain 的交易 Agent
创建时间: 2025-10-29

架构:
- 使用 LangChain 自动处理工具调用循环
- 无需手写 for 循环，代码更简洁
- 自动管理对话历史和工具调用
"""

from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
import threading
import time
import asyncio

from app.services.data_collector import get_exchange_connector
from app.services.indicators import calculate_indicators
from app.repositories.position_repo import PositionRepository
from app.repositories.ai_decision_repo import AIDecisionRepository
from app.repositories.trading_session_repo import TradingSessionRepository
from app.utils.database import get_db
from app.utils.logging import get_logger
from app.utils.config import settings

logger = get_logger(__name__)


# ==================== Pydantic 模型定义 ====================

class BuyParams(BaseModel):
    """买入参数"""
    symbol: str = Field(description="交易对，如 BTC/USDT:USDT")
    quantity: float = Field(description="购买数量")
    leverage: int = Field(default=1, ge=1, le=20, description="杠杆倍数，1-20")
    stop_loss_pct: Optional[float] = Field(default=None, description="止损百分比")
    take_profit_pct: Optional[float] = Field(default=None, description="止盈百分比")


class SellParams(BaseModel):
    """卖出参数"""
    position_id: int = Field(description="持仓 ID")
    percentage: float = Field(default=100, ge=0, le=100, description="平仓百分比")


class AdjustPositionParams(BaseModel):
    """调整持仓参数"""
    position_id: int = Field(description="持仓 ID")
    stop_loss_pct: Optional[float] = Field(default=None, description="新的止损百分比")
    take_profit_pct: Optional[float] = Field(default=None, description="新的止盈百分比")


# ==================== 工具函数实现 ====================

class TradingTools:
    """交易工具集合类"""
    
    def __init__(self, session_id: int):
        self.session_id = session_id
    
    async def get_market_data(self, symbol: str) -> Dict[str, Any]:
        """获取市场数据和技术指标"""
        try:
            exchange = get_exchange_connector()
            ticker = exchange.get_ticker(symbol)
            klines = exchange.get_klines(symbol, interval='1h', limit=100)
            
            indicators = {}
            if klines:
                indicators_result = calculate_indicators(klines)
                indicators = indicators_result.get('latest_values', {})
            
            funding_rate = None
            try:
                funding_rate = exchange.get_funding_rate(symbol)
            except Exception:
                pass
            
            open_interest = None
            try:
                open_interest = exchange.get_open_interest(symbol)
            except Exception:
                pass
            
            result = {
                "success": True,
                "symbol": symbol,
                "price": ticker.get('last'),
                "bid": ticker.get('bid'),
                "ask": ticker.get('ask'),
                "volume_24h": ticker.get('baseVolume'),
                "change_24h": ticker.get('percentage'),
                "indicators": {
                    "rsi": indicators.get('rsi'),
                    "macd": indicators.get('macd'),
                    "macd_signal": indicators.get('macd_signal'),
                    "ema_20": indicators.get('ema_20'),
                    "ema_50": indicators.get('ema_50'),
                    "bb_upper": indicators.get('bb_upper'),
                    "bb_middle": indicators.get('bb_middle'),
                    "bb_lower": indicators.get('bb_lower'),
                },
                "funding_rate": funding_rate,
                "open_interest": open_interest,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info("获取市场数据成功", symbol=symbol, price=ticker.get('last'))
            return result
            
        except Exception as e:
            logger.exception(f"获取市场数据失败: {symbol}")
            return {"success": False, "symbol": symbol, "error": str(e)}
    
    async def get_positions(self) -> Dict[str, Any]:
        """获取当前持仓"""
        try:
            db = next(get_db())
            try:
                position_repo = PositionRepository(db)
                session_repo = TradingSessionRepository(db)
                
                positions = position_repo.get_active_positions(self.session_id)
                session = session_repo.get_by_id(self.session_id)
                
                position_list = []
                total_unrealized_pnl = 0
                
                for p in positions:
                    unrealized_pnl = float(p.unrealized_pnl) if p.unrealized_pnl else 0
                    total_unrealized_pnl += unrealized_pnl
                    
                    position_list.append({
                        "id": p.id,
                        "symbol": p.symbol,
                        "side": p.side,
                        "quantity": float(p.quantity),
                        "entry_price": float(p.entry_price),
                        "current_price": float(p.current_price) if p.current_price else None,
                        "unrealized_pnl": unrealized_pnl,
                        "leverage": p.leverage,
                        "stop_loss": float(p.stop_loss) if p.stop_loss else None,
                        "take_profit": float(p.take_profit) if p.take_profit else None,
                        "opened_at": p.opened_at.isoformat() if p.opened_at else None
                    })
                
                result = {
                    "success": True,
                    "session_id": self.session_id,
                    "positions": position_list,
                    "position_count": len(position_list),
                    "total_unrealized_pnl": total_unrealized_pnl,
                    "initial_capital": float(session.initial_capital) if session and session.initial_capital else 0,
                    "session_status": session.status if session else None
                }
                
                logger.info("获取持仓成功", session_id=self.session_id, count=len(position_list))
                return result
                
            finally:
                db.close()
                
        except Exception as e:
            logger.exception(f"获取持仓失败: {self.session_id}")
            return {"success": False, "error": str(e)}
    
    async def buy(self, symbol: str, quantity: float, leverage: int = 1, 
                  stop_loss_pct: Optional[float] = None, 
                  take_profit_pct: Optional[float] = None) -> Dict[str, Any]:
        """执行买入操作"""
        logger.info("执行买入操作", session_id=self.session_id, symbol=symbol, quantity=quantity, leverage=leverage)
        
        try:
            db = next(get_db())
            try:
                position_repo = PositionRepository(db)
                exchange = get_exchange_connector()
                ticker = exchange.get_ticker(symbol)
                entry_price = ticker.get('last')
                
                position = position_repo.create_position(
                    session_id=self.session_id,
                    symbol=symbol,
                    side='long',
                    quantity=Decimal(str(quantity)),
                    entry_price=Decimal(str(entry_price)),
                    leverage=leverage,
                    stop_loss=Decimal(str(entry_price * (1 - stop_loss_pct / 100))) if stop_loss_pct else None,
                    take_profit=Decimal(str(entry_price * (1 + take_profit_pct / 100))) if take_profit_pct else None
                )
                
                return {
                    "success": True,
                    "action": "buy",
                    "position_id": position.id,
                    "symbol": symbol,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "leverage": leverage,
                    "stop_loss": float(position.stop_loss) if position.stop_loss else None,
                    "take_profit": float(position.take_profit) if position.take_profit else None,
                    "message": "买入订单已提交（模拟）"
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.exception(f"买入操作失败: {symbol}")
            return {"success": False, "error": str(e)}
    
    async def sell(self, position_id: int, percentage: float = 100) -> Dict[str, Any]:
        """执行卖出操作"""
        logger.info("执行卖出操作", session_id=self.session_id, position_id=position_id, percentage=percentage)
        
        try:
            db = next(get_db())
            try:
                position_repo = PositionRepository(db)
                position = position_repo.get_by_id(position_id)
                
                if not position:
                    return {"success": False, "error": f"持仓 {position_id} 不存在"}
                
                exchange = get_exchange_connector()
                ticker = exchange.get_ticker(position.symbol)
                exit_price = ticker.get('last')
                
                entry_price = float(position.entry_price)
                pnl = (exit_price - entry_price) * float(position.quantity) * (percentage / 100)
                
                if percentage >= 100:
                    position_repo.close_position(position_id, Decimal(str(exit_price)), Decimal(str(pnl)))
                    status = "closed"
                else:
                    status = "partially_closed"
                
                return {
                    "success": True,
                    "action": "sell",
                    "position_id": position_id,
                    "symbol": position.symbol,
                    "percentage": percentage,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "status": status,
                    "message": f"平仓 {percentage}% 成功"
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.exception(f"卖出操作失败: {position_id}")
            return {"success": False, "error": str(e)}
    
    async def adjust_position(self, position_id: int, 
                             stop_loss_pct: Optional[float] = None,
                             take_profit_pct: Optional[float] = None) -> Dict[str, Any]:
        """调整持仓止损止盈"""
        logger.info("调整持仓", session_id=self.session_id, position_id=position_id)
        
        try:
            db = next(get_db())
            try:
                position_repo = PositionRepository(db)
                position = position_repo.get_by_id(position_id)
                
                if not position:
                    return {"success": False, "error": f"持仓 {position_id} 不存在"}
                
                entry_price = float(position.entry_price)
                new_stop_loss = None
                new_take_profit = None
                
                if stop_loss_pct is not None:
                    new_stop_loss = Decimal(str(entry_price * (1 - stop_loss_pct / 100)))
                
                if take_profit_pct is not None:
                    new_take_profit = Decimal(str(entry_price * (1 + take_profit_pct / 100)))
                
                position_repo.update_stop_loss_take_profit(position_id, new_stop_loss, new_take_profit)
                
                return {
                    "success": True,
                    "action": "adjust",
                    "position_id": position_id,
                    "stop_loss": float(new_stop_loss) if new_stop_loss else None,
                    "take_profit": float(new_take_profit) if new_take_profit else None,
                    "message": "止损止盈已更新"
                }
                
            finally:
                db.close()
                
        except Exception as e:
            logger.exception(f"调整持仓失败: {position_id}")
            return {"success": False, "error": str(e)}


# ==================== 创建 LangChain 工具 ====================

def create_langchain_tools(session_id: int):
    """创建 LangChain 工具列表"""
    trading_tools = TradingTools(session_id)
    
    @tool
    async def get_market_data(symbol: str) -> str:
        """获取加密货币的实时市场数据和技术指标
        
        Args:
            symbol: 交易对，如 BTC/USDT:USDT 或 ETH/USDT:USDT
        
        Returns:
            包含价格、成交量、RSI、MACD、EMA、布林带等信息的JSON字符串
        """
        import json
        result = await trading_tools.get_market_data(symbol)
        return json.dumps(result, ensure_ascii=False, default=str)
    
    @tool
    async def get_positions() -> str:
        """获取当前所有活跃持仓
        
        Returns:
            包含持仓数量、入场价格、当前价格、未实现盈亏等信息的JSON字符串
        """
        import json
        result = await trading_tools.get_positions()
        return json.dumps(result, ensure_ascii=False, default=str)
    
    @tool
    async def buy(symbol: str, quantity: float, leverage: int = 1,
                 stop_loss_pct: float = None, take_profit_pct: float = None) -> str:
        """买入加密货币（开多仓）
        
        Args:
            symbol: 交易对，如 BTC/USDT:USDT
            quantity: 购买数量（单位：币）
            leverage: 杠杆倍数，1-20，默认 1
            stop_loss_pct: 止损百分比，例如 5 表示跌 5% 止损
            take_profit_pct: 止盈百分比，例如 10 表示涨 10% 止盈
        
        Returns:
            操作结果的JSON字符串
        """
        import json
        result = await trading_tools.buy(symbol, quantity, leverage, stop_loss_pct, take_profit_pct)
        return json.dumps(result, ensure_ascii=False, default=str)
    
    @tool
    async def sell(position_id: int, percentage: float = 100) -> str:
        """卖出持仓（平仓）
        
        Args:
            position_id: 持仓 ID，从 get_positions 获取
            percentage: 平仓百分比，0-100，默认 100 表示全部平仓
        
        Returns:
            操作结果的JSON字符串
        """
        import json
        result = await trading_tools.sell(position_id, percentage)
        return json.dumps(result, ensure_ascii=False, default=str)
    
    @tool
    async def adjust_position(position_id: int, stop_loss_pct: float = None,
                            take_profit_pct: float = None) -> str:
        """调整现有持仓的止损止盈价格
        
        Args:
            position_id: 持仓 ID
            stop_loss_pct: 新的止损百分比
            take_profit_pct: 新的止盈百分比
        
        Returns:
            操作结果的JSON字符串
        """
        import json
        result = await trading_tools.adjust_position(position_id, stop_loss_pct, take_profit_pct)
        return json.dumps(result, ensure_ascii=False, default=str)
    
    return [get_market_data, get_positions, buy, sell, adjust_position]


# ==================== Trading Agent 主类 (LangChain 版本) ====================

class TradingAgentService:
    """
    基于 LangChain 的交易 Agent 服务
    
    优点:
    1. 使用 LangChain 自动循环，无需手写 for 循环
    2. 更好的抽象和可维护性
    3. 与 LangChain 生态系统集成
    """
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        
        # 初始化 LLM
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
            temperature=0.7
        )
        
        # 创建工具
        self.tools = create_langchain_tools(session_id)
        
        # Agent 将在 run_decision_cycle 中创建
        self.agent_executor = None
    
    async def run_decision_cycle(
        self,
        symbols: List[str],
        risk_params: Dict[str, Any],
        max_iterations: int = 15  # LangChain 使用 max_iterations
    ) -> Dict[str, Any]:
        """
        运行一次完整的决策周期
        
        Args:
            symbols: 交易对列表
            risk_params: 风险参数
            max_iterations: 最大迭代次数（LangChain 自动循环）
            
        Returns:
            决策结果
        """
        logger.info(
            "开始决策周期",
            session_id=self.session_id,
            symbols=symbols
        )
        
        try:
            # 生成系统提示词
            system_prompt = self._generate_system_prompt(symbols, risk_params)
            
            # 创建 Prompt 模板
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # 创建 Agent
            agent = create_tool_calling_agent(self.llm, self.tools, prompt)
            
            # 创建 Agent Executor（这里 LangChain 会自动处理循环）
            agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                max_iterations=max_iterations,
                verbose=True,  # 显示详细日志
                handle_parsing_errors=True,
                return_intermediate_steps=True  # 返回中间步骤
            )
            
            # 执行 Agent（LangChain 自动循环调用工具）
            user_input = f"""
请开始你的分析和决策：

1. 首先获取所有交易对的市场数据
2. 查看当前持仓情况
3. 综合分析技术指标、持仓状态
4. 做出交易决策（买入/卖出/调整/观望）
5. 执行决策并说明理由

交易对: {', '.join(symbols)}
"""
            
            result = await agent_executor.ainvoke({"input": user_input})
            
            # 解析结果
            output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # 提取使用的工具
            tools_used = []
            for step in intermediate_steps:
                if len(step) >= 1:
                    action = step[0]
                    tools_used.append({
                        "name": action.tool,
                        "args": action.tool_input
                    })
            
            logger.info(
                "决策周期完成",
                session_id=self.session_id,
                tools_count=len(tools_used)
            )
            
            # 保存决策到数据库
            await self._save_decision(output, tools_used)
            
            return {
                "success": True,
                "decision": output,
                "iterations": len(intermediate_steps),
                "tools_used": tools_used,
                "conversation": []  # LangChain 不直接暴露对话历史
            }
            
        except Exception as e:
            logger.exception("决策周期失败")
            return {
                "success": False,
                "error": str(e),
                "iterations": 0,
                "tools_used": [],
                "conversation": []
            }
    
    async def _save_decision(self, decision_text: str, tools_used: List[Dict]) -> None:
        """保存决策到数据库"""
        try:
            db = next(get_db())
            try:
                decision_repo = AIDecisionRepository(db)
                
                # 保存决策
                decision_repo.save_decision(
                    session_id=self.session_id,
                    symbols=[tool["args"].get("symbol") for tool in tools_used if "symbol" in tool.get("args", {})],
                    decision_type="hold",
                    confidence=Decimal("0.7"),
                    prompt_data={},
                    ai_response=decision_text,
                    reasoning=decision_text,
                    suggested_actions={"tools_used": tools_used},
                    executed=True
                )
                
                logger.info("决策已保存到数据库")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.exception("保存决策失败")
    
    def _generate_system_prompt(self, symbols: List[str], risk_params: Dict[str, Any]) -> str:
        """生成系统提示词"""
        return f"""你是一个专业的加密货币交易 AI 助手。你的目标是通过分析市场数据做出明智的交易决策，最大化投资回报的同时严格控制风险。

## 当前配置

**交易对**: {', '.join(symbols)}

**风险管理参数**:
- 最大单仓占比: {risk_params.get('max_position_size', 0.2) * 100}%
- 止损百分比: {risk_params.get('stop_loss_pct', 0.05) * 100}%
- 止盈百分比: {risk_params.get('take_profit_pct', 0.10) * 100}%
- 最大杠杆: {risk_params.get('max_leverage', 3)}x
- 最大持仓数: {risk_params.get('max_positions', 3)}

## 决策流程

1. 使用 get_market_data 获取每个交易对的市场数据
2. 使用 get_positions 查看当前持仓
3. 分析技术指标（RSI, MACD, EMA, 布林带等）
4. 根据分析做出交易决策
5. 使用 buy/sell/adjust_position 执行操作
6. 总结决策理由和风险控制

## 重要原则

1. 风险第一，遵守所有风险参数
2. 技术指标为主要依据
3. 每次开仓必须设置止损止盈
4. 合理分配资金，不要满仓
5. 客观分析，既看机会也看风险

完成所有分析和操作后，给出完整的决策总结。
"""


# ==================== 辅助函数 ====================

async def run_trading_agent(
    session_id: int,
    symbols: List[str],
    risk_params: Optional[Dict[str, Any]] = None,
    max_iterations: int = 15
) -> Dict[str, Any]:
    """
    运行交易 Agent 的便捷函数
    """
    if risk_params is None:
        risk_params = {
            "max_position_size": 0.2,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.10,
            "max_leverage": 3,
            "max_positions": 3
        }
    
    agent = TradingAgentService(session_id)
    
    result = await agent.run_decision_cycle(
        symbols=symbols,
        risk_params=risk_params,
        max_iterations=max_iterations
    )
    
    return result


# ==================== 后台挂机服务 ====================

class BackgroundAgentManager:
    """后台 Agent 管理器"""
    
    def __init__(self):
        self._agents: Dict[int, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        logger.info("BackgroundAgentManager 已初始化")
    
    def start_background_agent(
        self,
        session_id: int,
        symbols: List[str],
        risk_params: Optional[Dict[str, Any]] = None,
        decision_interval: int = 300,
        max_iterations: int = 15
    ) -> Dict[str, Any]:
        """启动后台挂机 Agent"""
        with self._lock:
            if session_id in self._agents:
                raise ValueError(f"Session {session_id} 的 Agent 已在运行")
            
            if risk_params is None:
                risk_params = {
                    "max_position_size": 0.2,
                    "stop_loss_pct": 0.05,
                    "take_profit_pct": 0.10,
                    "max_leverage": 3,
                    "max_positions": 3
                }
            
            stop_event = threading.Event()
            
            thread = threading.Thread(
                target=self._run_background_loop,
                args=(session_id, symbols, risk_params, decision_interval, max_iterations, stop_event),
                daemon=True,
                name=f"BackgroundAgent-{session_id}"
            )
            
            self._agents[session_id] = {
                'thread': thread,
                'stop_event': stop_event,
                'config': {
                    'symbols': symbols,
                    'risk_params': risk_params,
                    'decision_interval': decision_interval,
                    'max_iterations': max_iterations
                },
                'status': 'starting',
                'started_at': datetime.now(),
                'last_run_time': None,
                'run_count': 0,
                'last_error': None
            }
            
            thread.start()
            
            logger.info("后台 Agent 已启动", session_id=session_id)
            
            return {
                'session_id': session_id,
                'status': 'started',
                'decision_interval': decision_interval,
                'symbols': symbols
            }
    
    def stop_background_agent(self, session_id: int) -> Dict[str, Any]:
        """停止后台 Agent"""
        with self._lock:
            if session_id not in self._agents:
                raise ValueError(f"Session {session_id} 的 Agent 未运行")
            
            agent = self._agents[session_id]
            agent['stop_event'].set()
            agent['status'] = 'stopping'
        
        agent['thread'].join(timeout=10)
        
        with self._lock:
            stopped_agent = self._agents.pop(session_id, None)
        
        logger.info("后台 Agent 已停止", session_id=session_id)
        
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
        max_iterations: int,
        stop_event: threading.Event
    ):
        """后台循环"""
        logger.info("后台 Agent 循环开始", session_id=session_id)
        
        with self._lock:
            if session_id in self._agents:
                self._agents[session_id]['status'] = 'running'
        
        try:
            while not stop_event.is_set():
                loop_start = time.time()
                
                try:
                    logger.info("开始决策循环", session_id=session_id)
                    
                    result = asyncio.run(run_trading_agent(
                        session_id=session_id,
                        symbols=symbols,
                        risk_params=risk_params,
                        max_iterations=max_iterations
                    ))
                    
                    with self._lock:
                        if session_id in self._agents:
                            self._agents[session_id]['run_count'] += 1
                            self._agents[session_id]['last_run_time'] = datetime.now()
                            self._agents[session_id]['last_error'] = None
                    
                    logger.info("决策循环完成", session_id=session_id, success=result.get('success'))
                    
                    # 检查会话状态
                    if not self._check_session_running(session_id):
                        break
                    
                except Exception as e:
                    logger.exception("决策循环失败", session_id=session_id)
                    
                    with self._lock:
                        if session_id in self._agents:
                            self._agents[session_id]['last_error'] = str(e)
                
                loop_duration = time.time() - loop_start
                sleep_time = max(0, decision_interval - loop_duration)
                
                if sleep_time > 0:
                    stop_event.wait(timeout=sleep_time)
            
            logger.info("后台 Agent 循环结束", session_id=session_id)
            
        except Exception as e:
            logger.exception("后台 Agent 异常终止", session_id=session_id)
            
            with self._lock:
                if session_id in self._agents:
                    self._agents[session_id]['status'] = 'crashed'
                    self._agents[session_id]['last_error'] = str(e)
        
        finally:
            with self._lock:
                if session_id in self._agents:
                    self._agents[session_id]['status'] = 'stopped'
    
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


def get_agent_service(session_id: int) -> TradingAgentService:
    """
    获取交易 Agent 服务实例
    
    Args:
        session_id: 交易会话 ID
        
    Returns:
        TradingAgentService 实例
    """
    return TradingAgentService(session_id)

