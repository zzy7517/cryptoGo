"""
Trading Agent Service
基于 LangChain 的交易 Agent
创建时间: 2025-10-29
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
from pathlib import Path

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

class OpenLongParams(BaseModel):
    """开多仓参数"""
    symbol: str = Field(description="交易对，如 BTC/USDT:USDT")
    quantity: float = Field(description="购买数量")
    leverage: int = Field(default=1, ge=1, le=20, description="杠杆倍数，1-20")
    stop_loss_pct: Optional[float] = Field(default=None, description="止损百分比")
    take_profit_pct: Optional[float] = Field(default=None, description="止盈百分比")


class OpenShortParams(BaseModel):
    """开空仓参数"""
    symbol: str = Field(description="交易对，如 BTC/USDT:USDT")
    quantity: float = Field(description="卖空数量")
    leverage: int = Field(default=1, ge=1, le=20, description="杠杆倍数，1-20")
    stop_loss_pct: Optional[float] = Field(default=None, description="止损百分比")
    take_profit_pct: Optional[float] = Field(default=None, description="止盈百分比")


class ClosePositionParams(BaseModel):
    """平仓参数"""
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
        logger.info("=" * 80)
        logger.info(f"🔍 [工具调用] get_market_data - 开始获取市场数据", symbol=symbol)

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

            logger.info("✅ [工具返回] get_market_data - 成功")
            logger.info(f"📊 市场数据: {result}")
            logger.info("=" * 80)
            return result

        except Exception as e:
            logger.exception(f"❌ [工具返回] get_market_data - 失败: {symbol}")
            logger.info("=" * 80)
            return {"success": False, "symbol": symbol, "error": str(e)}
    
    async def get_positions(self) -> Dict[str, Any]:
        """获取当前持仓
        """
        logger.info("=" * 80)
        logger.info(f"🔍 [工具调用] get_positions - 开始获取持仓", session_id=self.session_id)

        try:
            db = next(get_db())
            try:
                # 初始化仓储对象
                position_repo = PositionRepository(db)
                session_repo = TradingSessionRepository(db)

                # 从数据库查询活跃持仓和会话信息
                positions = position_repo.get_active_positions(self.session_id)
                session = session_repo.get_by_id(self.session_id)

                position_list = []
                total_unrealized_pnl = 0

                # 遍历持仓，转换为字典格式并累计总盈亏
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

                # 组装返回结果
                result = {
                    "success": True,
                    "session_id": self.session_id,
                    "positions": position_list,  # 持仓明细列表
                    "position_count": len(position_list),  # 持仓数量
                    "total_unrealized_pnl": total_unrealized_pnl,  # 浮动盈亏
                    "initial_capital": float(session.initial_capital) if session and session.initial_capital else 0,
                    "session_status": session.status if session else None
                }

                logger.info("✅ [工具返回] get_positions - 成功")
                logger.info(f"💼 持仓信息: 持仓数={len(position_list)}, 总未实现盈亏={total_unrealized_pnl}")
                logger.info(f"📋 详细持仓: {result}")
                logger.info("=" * 80)
                return result

            finally:
                db.close()

        except Exception as e:
            logger.exception(f"❌ [工具返回] get_positions - 失败: {self.session_id}")
            logger.info("=" * 80)
            return {"success": False, "error": str(e)}
    
    async def open_long(self, symbol: str, quantity: float, leverage: int = 1,
                        stop_loss_pct: Optional[float] = None,
                        take_profit_pct: Optional[float] = None) -> Dict[str, Any]:
        """开多仓（做多）"""
        logger.info("=" * 80)
        logger.info(f"🔍 [工具调用] open_long - 执行开多仓操作")
        logger.info(f"📥 开多参数: symbol={symbol}, quantity={quantity}, leverage={leverage}, stop_loss_pct={stop_loss_pct}, take_profit_pct={take_profit_pct}")

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

                result = {
                    "success": True,
                    "action": "open_long",
                    "position_id": position.id,
                    "symbol": symbol,
                    "side": "long",
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "leverage": leverage,
                    "stop_loss": float(position.stop_loss) if position.stop_loss else None,
                    "take_profit": float(position.take_profit) if position.take_profit else None,
                    "message": "开多仓成功（模拟）"
                }

                logger.info("✅ [工具返回] open_long - 开多仓成功")
                logger.info(f"💰 开多结果: position_id={position.id}, entry_price={entry_price}")
                logger.info(f"📋 完整结果: {result}")
                logger.info("=" * 80)
                return result

            finally:
                db.close()

        except Exception as e:
            logger.exception(f"❌ [工具返回] open_long - 开多仓失败: {symbol}")
            logger.info("=" * 80)
            return {"success": False, "error": str(e)}

    async def open_short(self, symbol: str, quantity: float, leverage: int = 1,
                         stop_loss_pct: Optional[float] = None,
                         take_profit_pct: Optional[float] = None) -> Dict[str, Any]:
        """开空仓（做空）"""
        logger.info("=" * 80)
        logger.info(f"🔍 [工具调用] open_short - 执行开空仓操作")
        logger.info(f"📥 开空参数: symbol={symbol}, quantity={quantity}, leverage={leverage}, stop_loss_pct={stop_loss_pct}, take_profit_pct={take_profit_pct}")

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
                    side='short',
                    quantity=Decimal(str(quantity)),
                    entry_price=Decimal(str(entry_price)),
                    leverage=leverage,
                    stop_loss=Decimal(str(entry_price * (1 + stop_loss_pct / 100))) if stop_loss_pct else None,
                    take_profit=Decimal(str(entry_price * (1 - take_profit_pct / 100))) if take_profit_pct else None
                )

                result = {
                    "success": True,
                    "action": "open_short",
                    "position_id": position.id,
                    "symbol": symbol,
                    "side": "short",
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "leverage": leverage,
                    "stop_loss": float(position.stop_loss) if position.stop_loss else None,
                    "take_profit": float(position.take_profit) if position.take_profit else None,
                    "message": "开空仓成功（模拟）"
                }

                logger.info("✅ [工具返回] open_short - 开空仓成功")
                logger.info(f"💰 开空结果: position_id={position.id}, entry_price={entry_price}")
                logger.info(f"📋 完整结果: {result}")
                logger.info("=" * 80)
                return result

            finally:
                db.close()

        except Exception as e:
            logger.exception(f"❌ [工具返回] open_short - 开空仓失败: {symbol}")
            logger.info("=" * 80)
            return {"success": False, "error": str(e)}
    
    async def close_position(self, position_id: int, percentage: float = 100) -> Dict[str, Any]:
        """平仓（既可以平多仓，也可以平空仓）"""
        logger.info("=" * 80)
        logger.info(f"🔍 [工具调用] close_position - 执行平仓操作")
        logger.info(f"📥 平仓参数: position_id={position_id}, percentage={percentage}")

        try:
            db = next(get_db())
            try:
                position_repo = PositionRepository(db)
                position = position_repo.get_by_id(position_id)

                if not position:
                    logger.warning(f"❌ [工具返回] close_position - 持仓不存在: {position_id}")
                    logger.info("=" * 80)
                    return {"success": False, "error": f"持仓 {position_id} 不存在"}

                exchange = get_exchange_connector()
                ticker = exchange.get_ticker(position.symbol)
                exit_price = ticker.get('last')

                entry_price = float(position.entry_price)

                # 根据做多或做空计算盈亏
                if position.side == 'long':
                    pnl = (exit_price - entry_price) * float(position.quantity) * (percentage / 100)
                else:  # short
                    pnl = (entry_price - exit_price) * float(position.quantity) * (percentage / 100)

                if percentage >= 100:
                    position_repo.close_position(position_id, Decimal(str(exit_price)))
                    status = "closed"
                else:
                    status = "partially_closed"

                result = {
                    "success": True,
                    "action": "close_position",
                    "position_id": position_id,
                    "symbol": position.symbol,
                    "side": position.side,
                    "percentage": percentage,
                    "exit_price": exit_price,
                    "pnl": pnl,
                    "status": status,
                    "message": f"平仓 {percentage}% 成功"
                }

                logger.info("✅ [工具返回] close_position - 平仓成功")
                logger.info(f"💸 平仓结果: side={position.side}, pnl={pnl}, exit_price={exit_price}")
                logger.info(f"📋 完整结果: {result}")
                logger.info("=" * 80)
                return result

            finally:
                db.close()

        except Exception as e:
            logger.exception(f"❌ [工具返回] close_position - 平仓失败: {position_id}")
            logger.info("=" * 80)
            return {"success": False, "error": str(e)}
    
    async def adjust_position(self, position_id: int, 
                             stop_loss_pct: Optional[float] = None,
                             take_profit_pct: Optional[float] = None) -> Dict[str, Any]:
        """调整现有持仓的止损和止盈参数"""
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
            包含持仓数量、方向(long/short)、入场价格、当前价格、未实现盈亏等信息的JSON字符串
        """
        import json
        result = await trading_tools.get_positions()
        return json.dumps(result, ensure_ascii=False, default=str)

    @tool
    async def open_long(symbol: str, quantity: float, leverage: int = 1,
                       stop_loss_pct: float = None, take_profit_pct: float = None) -> str:
        """开多仓（做多）- 预期价格上涨时使用

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
        result = await trading_tools.open_long(symbol, quantity, leverage, stop_loss_pct, take_profit_pct)
        return json.dumps(result, ensure_ascii=False, default=str)

    @tool
    async def open_short(symbol: str, quantity: float, leverage: int = 1,
                        stop_loss_pct: float = None, take_profit_pct: float = None) -> str:
        """开空仓（做空）- 预期价格下跌时使用

        Args:
            symbol: 交易对，如 BTC/USDT:USDT
            quantity: 卖空数量（单位：币）
            leverage: 杠杆倍数，1-20，默认 1
            stop_loss_pct: 止损百分比，例如 5 表示涨 5% 止损（注意做空时价格上涨会亏损）
            take_profit_pct: 止盈百分比，例如 10 表示跌 10% 止盈

        Returns:
            操作结果的JSON字符串
        """
        import json
        result = await trading_tools.open_short(symbol, quantity, leverage, stop_loss_pct, take_profit_pct)
        return json.dumps(result, ensure_ascii=False, default=str)

    @tool
    async def close_position(position_id: int, percentage: float = 100) -> str:
        """平仓（既可以平多仓，也可以平空仓）

        Args:
            position_id: 持仓 ID，从 get_positions 获取
            percentage: 平仓百分比，0-100，默认 100 表示全部平仓

        Returns:
            操作结果的JSON字符串
        """
        import json
        result = await trading_tools.close_position(position_id, percentage)
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

    return [get_market_data, get_positions, open_long, open_short, close_position, adjust_position]


# ==================== Trading Agent 主类 (LangChain 版本) ====================

class TradingAgentService:
    """
    基于 LangChain 的交易 Agent 服务

    """
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        
        self.llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.DEEPSEEK_API_KEY,
            base_url="https://api.deepseek.com",
            temperature=0.1
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
        logger.info("🚀" * 30)
        logger.info("🚀 [AI 决策周期] 开始新的决策周期")
        logger.info(f"📌 Session ID: {self.session_id}")
        logger.info(f"📌 交易对: {symbols}")
        logger.info(f"📌 风险参数: {risk_params}")
        logger.info(f"📌 最大迭代次数: {max_iterations}")
        logger.info("🚀" * 30)

        try:
            # 生成系统提示词
            system_prompt = self._get(symbols, risk_params)

            logger.info("📝 [系统提示词] 已生成")
            logger.info("=" * 80)
            logger.info(system_prompt)
            logger.info("=" * 80)

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
4. 判断市场趋势（上涨/下跌/震荡）
5. 做出交易决策：
   - 看涨 → 开多仓 (open_long)
   - 看跌 → 开空仓 (open_short)
   - 需要平仓 → 平仓 (close_position)
   - 震荡或不确定 → 观望
6. 执行决策并说明理由

交易对: {', '.join(symbols)}
"""

            logger.info("💬 [用户输入] 发送给 AI 的任务")
            logger.info("=" * 80)
            logger.info(user_input)
            logger.info("=" * 80)

            logger.info("🤖 [AI 开始思考] LangChain Agent 开始执行...")

            result = await agent_executor.ainvoke({"input": user_input})

            logger.info("🎉 [AI 执行完成] LangChain Agent 执行完成")

            # 解析结果
            output = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])

            logger.info("📊 [AI 最终输出]")
            logger.info("=" * 80)
            logger.info(output)
            logger.info("=" * 80)

            # 提取使用的工具
            tools_used = []
            for idx, step in enumerate(intermediate_steps, 1):
                if len(step) >= 2:
                    action = step[0]
                    observation = step[1]

                    tool_info = {
                        "name": action.tool,
                        "args": action.tool_input
                    }
                    tools_used.append(tool_info)

                    logger.info(f"🔧 [工具调用 #{idx}]")
                    logger.info(f"   工具名称: {action.tool}")
                    logger.info(f"   调用参数: {action.tool_input}")
                    logger.info(f"   返回结果: {observation}")

            logger.info("📈 [决策周期统计]")
            logger.info(f"   总迭代次数: {len(intermediate_steps)}")
            logger.info(f"   工具调用次数: {len(tools_used)}")
            logger.info(f"   使用的工具: {[t['name'] for t in tools_used]}")

            # 保存决策到数据库
            await self._save_decision(output, tools_used)

            logger.info("💾 [数据库] 决策已保存到数据库")
            logger.info("✅" * 30)
            logger.info("✅ [AI 决策周期] 完成")
            logger.info("✅" * 30)

            return {
                "success": True,
                "decision": output,
                "iterations": len(intermediate_steps),
                "tools_used": tools_used,
                "conversation": []  # LangChain 不直接暴露对话历史
            }

        except Exception as e:
            logger.exception("❌ [AI 决策周期] 失败")
            logger.error(f"错误详情: {str(e)}")
            logger.info("❌" * 30)
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
    
    def _get(self, symbols: List[str], risk_params: Dict[str, Any]) -> str:
        """从文件加载系统提示词模板并填充参数"""
        try:
            # 获取提示词文件路径
            prompt_file = Path(__file__).parent.parent / "prompts" / "trading_system_prompt.txt"
            
            # 读取提示词模板
            with open(prompt_file, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # 填充参数
            prompt = template.format(
                symbols=', '.join(symbols),
                max_position_size=risk_params.get('max_position_size', 0.2) * 100,
                stop_loss_pct=risk_params.get('stop_loss_pct', 0.05) * 100,
                take_profit_pct=risk_params.get('take_profit_pct', 0.10) * 100,
                max_leverage=risk_params.get('max_leverage', 3)
            )
            
            logger.info("✅ 系统提示词已从文件加载", file=str(prompt_file))
            return prompt
            
        except Exception as e:
            logger.error(f"❌ 加载系统提示词文件失败: {e}")
            # 如果文件加载失败，返回简单的默认提示词
            return f"你是一个专业的加密货币交易 AI 助手。交易对: {', '.join(symbols)}"


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
            "max_leverage": 3
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
        """启动后台 Agent"""
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
        logger.info("🔄" * 30)
        logger.info("🔄 [后台循环] 后台 Agent 循环开始")
        logger.info(f"📌 Session ID: {session_id}")
        logger.info(f"📌 决策间隔: {decision_interval}秒")
        logger.info("🔄" * 30)

        with self._lock:
            if session_id in self._agents:
                self._agents[session_id]['status'] = 'running'

        try:
            loop_count = 0
            while not stop_event.is_set():
                loop_count += 1
                loop_start = time.time()

                logger.info("🔄" * 30)
                logger.info(f"🔄 [后台循环] 第 {loop_count} 次循环开始")
                logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

                try:
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

                    logger.info(f"✅ [后台循环] 第 {loop_count} 次循环完成, 成功={result.get('success')}")

                    # 检查会话状态
                    if not self._check_session_running(session_id):
                        logger.warning("⚠️  [后台循环] 会话已结束，停止循环")
                        break

                except Exception as e:
                    logger.exception(f"❌ [后台循环] 第 {loop_count} 次循环失败")

                    with self._lock:
                        if session_id in self._agents:
                            self._agents[session_id]['last_error'] = str(e)

                loop_duration = time.time() - loop_start
                sleep_time = max(0, decision_interval - loop_duration)

                logger.info(f"⏱️  [后台循环] 本次循环耗时: {loop_duration:.2f}秒")
                logger.info(f"😴 [后台循环] 等待 {sleep_time:.2f}秒 后进行下一次循环...")
                logger.info("🔄" * 30)

                if sleep_time > 0:
                    stop_event.wait(timeout=sleep_time)

            logger.info("🛑" * 30)
            logger.info("🛑 [后台循环] 后台 Agent 循环正常结束")
            logger.info(f"📊 总循环次数: {loop_count}")
            logger.info("🛑" * 30)

        except Exception as e:
            logger.exception("💥 [后台循环] 后台 Agent 异常终止")

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

