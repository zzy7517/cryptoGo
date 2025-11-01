"""
Trading Agent Service - 定时循环版本（无 LangChain）
核心逻辑：数据收集 -> AI分析决策 -> 执行交易 -> 记录保存
创建时间: 2025-10-30
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from decimal import Decimal
import threading
import time
import asyncio
import json
from pathlib import Path

from ..utils.data_collector import get_exchange
from .llm_service import get_llm
from ..llm.prompt_builder import build_user_prompt
from .trader_service import get_trader
from ..exchanges.base import PositionSide as TraderPositionSide
from ..llm.response_parser import ResponseParser, Decision as ParsedDecision
from ..repositories.trade_repo import TradeRepository
from ..repositories.ai_decision_repo import AIDecisionRepository
from ..repositories.trading_session_repo import TradingSessionRepository
from ..utils.database import get_db
from ..utils.logging import get_logger

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
        stop_loss_price: Optional[float] = None,
        take_profit_price: Optional[float] = None,
        confidence: int = 50,
        risk_usd: Optional[float] = None
    ):
        self.symbol = symbol
        self.action = action  # open_long, open_short, close_long, close_short, hold, wait
        self.reasoning = reasoning
        self.leverage = leverage
        self.position_size_usd = position_size_usd
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.stop_loss_price = stop_loss_price  # 绝对价格（优先使用）
        self.take_profit_price = take_profit_price  # 绝对价格（优先使用）
        self.confidence = confidence
        self.risk_usd = risk_usd

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "symbol": self.symbol,
            "action": self.action,
            "reasoning": self.reasoning,
            "leverage": self.leverage,
            "position_size_usd": self.position_size_usd,
            "confidence": self.confidence
        }

        # 只添加非None的字段
        if self.stop_loss_pct is not None:
            result["stop_loss_pct"] = self.stop_loss_pct
        if self.take_profit_pct is not None:
            result["take_profit_pct"] = self.take_profit_pct
        if self.stop_loss_price is not None:
            result["stop_loss_price"] = self.stop_loss_price
        if self.take_profit_price is not None:
            result["take_profit_price"] = self.take_profit_price
        if self.risk_usd is not None:
            result["risk_usd"] = self.risk_usd

        return result


# ==================== AI 决策函数 ====================

async def build_system_prompt(risk_params: Dict[str, Any], session_id: int) -> str:
    """构建系统提示词"""
    # 从文件加载提示词模板
    prompt_file = Path(__file__).parent.parent / "prompts" / "trading_system_prompt.txt"
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        template = f.read()
    
        # 获取账户净值
        from .account_service import get_account_service
    account_service = get_account_service()
    account_info = account_service.get_account_info()
    account_equity = account_info.get('totalMarginBalance', 10000)  # 默认10000
    
    # 计算仓位和杠杆值
    altcoin_min = account_equity * 0.8
    altcoin_max = account_equity * 1.5
    altcoin_leverage = risk_params.get('altcoin_leverage', 5)
    
    btc_eth_min = account_equity * 5
    btc_eth_max = account_equity * 10
    btc_eth_leverage = risk_params.get('btc_eth_leverage', 3)
    
    # 使用字符串替换，以支持特殊字符的占位符
    prompt = template
    prompt = prompt.replace('{账户净值*0.8}', f'{altcoin_min:.0f}')
    prompt = prompt.replace('{账户净值*1.5}', f'{altcoin_max:.0f}')
    prompt = prompt.replace('{山寨币杠杆}', str(altcoin_leverage))
    prompt = prompt.replace('{账户净值*5}', f'{btc_eth_min:.0f}')
    prompt = prompt.replace('{账户净值*10}', f'{btc_eth_max:.0f}')
    prompt = prompt.replace('{BTC/ETH杠杆}', str(btc_eth_leverage))
    
    logger.info(f"✅ 系统提示词加载成功，账户净值: {account_equity:.2f}")
    
    return prompt


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
        # 使用新的解析器
        parsed = ResponseParser.parse(response)

        # 如果有解析错误，记录日志
        if parsed.parsing_errors:
            logger.warning(f"⚠️ 解析过程中出现错误:")
            for error in parsed.parsing_errors:
                logger.warning(f"  - {error}")

        # 转换为Decision对象（保持兼容性）
        decisions = []
        for parsed_decision in parsed.decisions:
            decision = Decision(
                symbol=parsed_decision.symbol,
                action=parsed_decision.action,
                reasoning=parsed_decision.reasoning,
                leverage=parsed_decision.leverage,
                position_size_usd=parsed_decision.position_size_usd,
                stop_loss_pct=parsed_decision.stop_loss_pct,
                take_profit_pct=parsed_decision.take_profit_pct,
                stop_loss_price=parsed_decision.stop_loss,
                take_profit_price=parsed_decision.take_profit,
                confidence=parsed_decision.confidence,
                risk_usd=parsed_decision.risk_usd
            )
            decisions.append(decision)

        logger.info(f"✅ 成功解析 {len(decisions)} 个有效决策")

        # 记录思维链（如果有）
        if parsed.thinking:
            logger.info(f"💭 AI 思维链摘要: {parsed.thinking[:200]}...")

        return decisions

    except Exception as e:
        logger.exception(f"❌ 解析 AI 响应失败: {e}")
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
        system_prompt = await build_system_prompt(context.risk_params, context.session_id)
        
        logger.info("📝 构建用户提示词")
        user_prompt = await build_user_prompt(
            session_id=context.session_id,
            symbols=context.symbols,
            call_count=context.call_count,
            start_time=start_time
        )
        
        # 调用 AI
        ai_engine = get_llm()
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # 使用 asyncio.to_thread 将同步调用转为异步，避免阻塞事件循环
        response = await asyncio.to_thread(ai_engine.chat, messages, temperature=0.3)
        
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
    执行单个决策（使用真实交易）
    
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
            trade_repo = TradeRepository(db)
            
            # 创建交易器（自动从配置读取交易所类型）
            trader = get_trader()
            
            # 根据不同的 action 执行不同的操作
            if decision.action == "open_long":
                # 获取当前价格用于计算数量
                exchange = get_exchange()
                # 使用 asyncio.to_thread 避免阻塞事件循环
                ticker = await asyncio.to_thread(exchange.get_ticker, decision.symbol)
                current_price = ticker.get('last') or 0
                
                # 计算购买数量
                quantity = decision.position_size_usd / current_price if current_price > 0 else 0
                
                if quantity <= 0:
                    return {"success": False, "error": "数量无效"}
                
                # 计算止损止盈价格（优先使用绝对价格，其次使用百分比）
                stop_loss_price = None
                take_profit_price = None

                if decision.stop_loss_price is not None:
                    # 使用绝对价格
                    stop_loss_price = decision.stop_loss_price
                elif decision.stop_loss_pct is not None:
                    # 使用百分比计算
                    stop_loss_price = current_price * (1 - decision.stop_loss_pct / 100)

                if decision.take_profit_price is not None:
                    # 使用绝对价格
                    take_profit_price = decision.take_profit_price
                elif decision.take_profit_pct is not None:
                    # 使用百分比计算
                    take_profit_price = current_price * (1 + decision.take_profit_pct / 100)
                
                # 执行开多仓交易
                logger.info(f"📈 开多仓: {decision.symbol} 数量={quantity:.6f}")
                # 使用 asyncio.to_thread 避免阻塞事件循环
                order_result = await asyncio.to_thread(
                    trader.open_long,
                    symbol=decision.symbol,
                    quantity=quantity,
                    leverage=decision.leverage,
                    stop_loss_price=stop_loss_price,
                    take_profit_price=take_profit_price
                )
                
                if not order_result.success:
                    logger.error(f"❌ 开多仓失败: {order_result.error}")
                    return {"success": False, "error": order_result.error}

                # 不创建交易记录，持仓信息从交易所API获取
                # 只有平仓时才创建完整的交易记录

                logger.info(f"✅ 开多仓成功: {decision.symbol}, 订单ID={order_result.order_id}")
                return {
                    "success": True,
                    "action": "open_long",
                    "order_id": order_result.order_id,
                    "entry_price": float(order_result.avg_price or current_price),
                    "quantity": float(order_result.filled_quantity or quantity)
                }
                
            elif decision.action == "open_short":
                # 获取当前价格用于计算数量
                exchange = get_exchange()
                # 使用 asyncio.to_thread 避免阻塞事件循环
                ticker = await asyncio.to_thread(exchange.get_ticker, decision.symbol)
                current_price = ticker.get('last') or 0
                
                # 计算卖空数量
                quantity = decision.position_size_usd / current_price if current_price > 0 else 0
                
                if quantity <= 0:
                    return {"success": False, "error": "数量无效"}
                
                # 计算止损止盈价格（优先使用绝对价格，其次使用百分比）
                stop_loss_price = None
                take_profit_price = None

                if decision.stop_loss_price is not None:
                    # 使用绝对价格（做空时止损在上方）
                    stop_loss_price = decision.stop_loss_price
                elif decision.stop_loss_pct is not None:
                    # 使用百分比计算（做空时止损在上方）
                    stop_loss_price = current_price * (1 + decision.stop_loss_pct / 100)

                if decision.take_profit_price is not None:
                    # 使用绝对价格（做空时止盈在下方）
                    take_profit_price = decision.take_profit_price
                elif decision.take_profit_pct is not None:
                    # 使用百分比计算（做空时止盈在下方）
                    take_profit_price = current_price * (1 - decision.take_profit_pct / 100)
                
                # 执行开空仓交易
                logger.info(f"📉 开空仓: {decision.symbol} 数量={quantity:.6f}")
                # 使用 asyncio.to_thread 避免阻塞事件循环
                order_result = await asyncio.to_thread(
                    trader.open_short,
                    symbol=decision.symbol,
                    quantity=quantity,
                    leverage=decision.leverage,
                    stop_loss_price=stop_loss_price,
                    take_profit_price=take_profit_price
                )
                
                if not order_result.success:
                    logger.error(f"❌ 开空仓失败: {order_result.error}")
                    return {"success": False, "error": order_result.error}

                # 不创建交易记录，持仓信息从交易所API获取
                # 只有平仓时才创建完整的交易记录

                logger.info(f"✅ 开空仓成功: {decision.symbol}, 订单ID={order_result.order_id}")
                return {
                    "success": True,
                    "action": "open_short",
                    "order_id": order_result.order_id,
                    "entry_price": float(order_result.avg_price or current_price),
                    "quantity": float(order_result.filled_quantity or quantity)
                }
                
            elif decision.action in ["close_long", "close_short"]:
                # 平仓：从交易所API查找对应的持仓
                side = "long" if decision.action == "close_long" else "short"

                # 从交易所获取实时持仓
                exchange = get_exchange()
                positions = await asyncio.to_thread(exchange.get_positions)

                target_position = None
                for pos in positions:
                    # ccxt返回的持仓格式: {'symbol': 'BTC/USDT:USDT', 'side': 'long', 'contracts': 0.001, ...}
                    if pos.get('symbol') == decision.symbol and pos.get('side') == side:
                        target_position = pos
                        break

                if not target_position or float(target_position.get('contracts', 0)) == 0:
                    logger.warning(f"⚠️ 未找到要平仓的持仓: {decision.symbol} {side}")
                    return {"success": False, "error": "持仓不存在"}

                quantity = float(target_position.get('contracts', 0))

                # 执行平仓交易
                position_side = TraderPositionSide.LONG if side == "long" else TraderPositionSide.SHORT
                logger.info(f"🔻 平仓: {decision.symbol} {side} 数量={quantity}")
                # 使用 asyncio.to_thread 避免阻塞事件循环
                order_result = await asyncio.to_thread(
                    trader.close_position,
                    symbol=decision.symbol,
                    position_side=position_side,
                    quantity=quantity
                )

                if not order_result.success:
                    logger.error(f"❌ 平仓失败: {order_result.error}")
                    return {"success": False, "error": order_result.error}

                # 创建完整的交易记录
                exit_price = Decimal(str(order_result.avg_price)) if order_result.avg_price else Decimal(str(target_position.get('markPrice', 0)))
                filled_quantity = Decimal(str(order_result.filled_quantity or quantity))
                leverage_value = int(target_position.get('leverage', 1))

                # 从持仓信息获取开仓价格和时间
                entry_price = Decimal(str(target_position.get('entryPrice', 0)))

                # 获取开仓时间（从持仓的 updateTime 或当前时间推算）
                # 注意：币安API的 updateTime 是最后更新时间，不一定是开仓时间
                # 这里简化处理，实际应该从订单历史获取
                from datetime import datetime, timezone, timedelta
                exit_time = datetime.now(timezone.utc)

                # 假设持仓时间（实际应该从交易所获取准确时间）
                # 这里用一个简化的估算：从 position 的 info 中获取
                entry_time = exit_time - timedelta(minutes=5)  # 临时方案

                # 创建完整的交易记录
                trade = trade_repo.create_closed_trade(
                    session_id=session_id,
                    symbol=decision.symbol,
                    side=side,  # 'long' or 'short'
                    quantity=filled_quantity,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    entry_time=entry_time,
                    exit_time=exit_time,
                    leverage=leverage_value,
                    entry_fee=Decimal(0),  # 开仓手续费需要从历史订单获取
                    exit_fee=Decimal(str(order_result.fee)) if order_result.fee else Decimal(0),
                    fee_currency=order_result.fee_currency or 'USDT',
                    ai_decision_id=None,
                    entry_order_id=None,  # 需要从交易所获取
                    exit_order_id=order_result.order_id
                )

                logger.info(f"✅ 平仓成功: {decision.symbol} {side}, 交易ID={trade.id}, P&L=${float(trade.pnl):.2f}")
                return {
                    "success": True,
                    "action": decision.action,
                    "trade_id": trade.id,
                    "order_id": order_result.order_id,
                    "exit_price": float(exit_price),
                    "quantity": float(filled_quantity),
                    "pnl": float(trade.pnl)
                }
                
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
        logger.exception(f"❌ 执行决策失败: {e}")
        return {"success": False, "error": str(e)}


# ==================== Trading Agent 主类（定时循环版本）====================

class TradingAgentService:
    """
    基于定时循环的交易 Agent 服务
    
    核心流程：
    1. 使用定时器触发周期性决策
    2. 每个周期独立：收集数据 -> 调用 AI -> 执行决策 -> 保存
    3. 未使用复杂agent框架
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
                    reasoning=ai_response,  # 完整的AI响应（移除500字符限制）
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
    """
    后台交易管理器
    
    管理会话的后台交易任务
    状态存储在数据库中，内存只保留 Task 引用
    """
    
    def __init__(self):
        # 只存储 Task 引用和取消事件
        self._tasks: Dict[int, asyncio.Task] = {}
        self._cancel_events: Dict[int, asyncio.Event] = {}
        self._lock = asyncio.Lock()
        logger.info("✨ 后台交易管理器已初始化")
    
    async def start_background_agent(
        self,
        session_id: int,
        symbols: List[str],
        risk_params: Optional[Dict[str, Any]] = None,
        decision_interval: int = 180  # 默认3分钟
    ) -> Dict[str, Any]:
        """
        启动后台 Agent
        
        Args:
            session_id: 交易会话 ID
            symbols: 交易对列表
            risk_params: 风险参数
            decision_interval: 决策间隔（秒），默认180秒（3分钟）
        """
        async with self._lock:
            if session_id in self._tasks:
                raise ValueError(f"Session {session_id} 的 Agent 已在运行")
            
            if risk_params is None:
                risk_params = {
                    "max_position_size": 0.2,
                    "stop_loss_pct": 0.05,
                    "take_profit_pct": 0.10,
                    "max_leverage": 3
                }
            
            # 更新数据库：设置后台状态为 starting
            await self._update_session_status(
                session_id=session_id,
                background_status='starting',
                background_started_at=datetime.now(timezone.utc),
                decision_interval=decision_interval,
                trading_symbols=symbols,
                trading_params=risk_params,
                decision_count=0,
                last_error=None
            )
            
            # 创建取消事件
            cancel_event = asyncio.Event()
            
            # 创建 asyncio.Task
            task = asyncio.create_task(
                self._run_background_loop(
                    session_id, symbols, risk_params, decision_interval, cancel_event
                ),
                name=f"BackgroundAgent-{session_id}"
            )
            
            self._tasks[session_id] = task
            self._cancel_events[session_id] = cancel_event
            
            logger.info(f"✅ 后台交易已启动", session_id=session_id, interval=decision_interval)
            
            return {
                'session_id': session_id,
                'status': 'started',
                'decision_interval': decision_interval,
                'symbols': symbols
            }
    
    async def stop_background_agent(self, session_id: int) -> Dict[str, Any]:
        """
        停止后台交易
        
        优雅地取消 asyncio.Task 并等待其完成
        """
        logger.info(f"🛑 [stop] 开始停止 Session {session_id}...")
        
        async with self._lock:
            if session_id not in self._tasks:
                logger.error(f"❌ [stop] Session {session_id} 后台交易未运行")
                raise ValueError(f"Session {session_id} 后台交易未运行")
            
            # 更新数据库状态为 stopping
            await self._update_session_status(
                session_id=session_id,
                background_status='stopping'
            )
            
            cancel_event = self._cancel_events[session_id]
            task = self._tasks[session_id]
            
            logger.info(f"🚩 [stop] 设置取消信号...")
            cancel_event.set()
        
        # 在锁外等待 task 完成（避免死锁）
        logger.info(f"⏳ [stop] 等待 Task 完成 (最多10秒)...")
        try:
            await asyncio.wait_for(task, timeout=10)
            logger.info(f"✅ [stop] Task 已正常完成")
        except asyncio.TimeoutError:
            logger.warning(f"⏱️ [stop] Task 超时，强制取消...")
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"✅ [stop] Task 已被取消")
        except asyncio.CancelledError:
            logger.info(f"✅ [stop] Task 已被取消")
        except Exception as e:
            logger.error(f"❌ [stop] Task 异常: {e}")
        
        # 清理内存中的引用
        async with self._lock:
            self._tasks.pop(session_id, None)
            self._cancel_events.pop(session_id, None)
            logger.info(f"🗑️ [stop] 已从内存中移除 Task 引用")
        
        # 获取最终的运行次数
        status = await self._get_session_status(session_id)
        run_count = status.get('decision_count', 0) if status else 0
        
        logger.info(f"⏹️ [stop] 后台交易已停止 (Session {session_id})")
        
        return {
            'session_id': session_id,
            'status': 'stopped',
            'run_count': run_count
        }
    
    async def get_agent_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """获取后台交易状态 - 从数据库读取"""
        # 从数据库获取会话信息
        session_data = await self._get_session_status(session_id)
        
        if not session_data:
            return None
        
        # 检查后台状态是否为 idle（从未启动）
        if session_data.get('background_status') == 'idle':
            return None

        return {
            'session_id': session_id,
            'status': session_data.get('background_status', 'idle'),
            'started_at': session_data.get('background_started_at').isoformat() if session_data.get('background_started_at') else None,
            'stopped_at': session_data.get('background_stopped_at').isoformat() if session_data.get('background_stopped_at') else None,
            'last_run_time': session_data.get('last_decision_time').isoformat() if session_data.get('last_decision_time') else None,
            'run_count': session_data.get('decision_count', 0),
            'config': {
                'symbols': session_data.get('trading_symbols', []),
                'decision_interval': session_data.get('decision_interval', 180),
                'risk_params': session_data.get('trading_params', {})
            },
            'last_error': session_data.get('last_error')
        }
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        列出所有运行中的 Agent (同步版本，用于非async上下文)
        
        注意：这个方法是同步的，仅用于 shutdown 时调用
        """
        logger.info(f"📋 [list_agents] 开始（同步版本）...")
        result = []
        for session_id in list(self._tasks.keys()):
            task = self._tasks.get(session_id)
            if task and not task.done():
                result.append({
                    'session_id': session_id
                })
        logger.info(f"📋 [list_agents] 返回 {len(result)} 个 Agent")
        return result
    
    async def _run_background_loop(
        self,
        session_id: int,
        symbols: List[str],
        risk_params: Dict[str, Any],
        decision_interval: int,
        cancel_event: asyncio.Event
    ):
        """
        后台循环 - 定时执行交易决策
        
        使用 asyncio.sleep 等待固定间隔，每个周期调用一次决策
        使用 asyncio.Event 进行优雅取消
        状态存储在数据库中
        """
        logger.info("🔄" * 30)
        logger.info("🔄 后台循环启动")
        logger.info(f"📌 Session ID: {session_id}")
        logger.info(f"📌 决策间隔: {decision_interval}秒")
        logger.info("🔄" * 30)
        
        # 更新数据库状态为 running
        await self._update_session_status(
            session_id=session_id,
            background_status='running'
        )
        
        # 创建 Agent 实例
        agent = TradingAgentService(session_id)
        
        try:
            # 首次立即执行
            logger.info("🚀 执行首次决策周期...")
            try:
                result = await agent.run_decision_cycle(symbols, risk_params)
                
                # 更新数据库
                await self._increment_decision_count(session_id)
                
                logger.info(f"✅ 首次决策完成, 成功={result.get('success')}")
                
            except Exception as e:
                logger.exception(f"❌ 首次决策失败: {e}")
                
                # 记录错误到数据库
                await self._update_session_status(
                    session_id=session_id,
                    last_error=str(e)
                )
            
            # 定时循环
            loop_count = 1
            while not cancel_event.is_set():
                # 等待下一个周期（可被取消信号中断）
                logger.info(f"😴 等待 {decision_interval}秒后进行下一次决策...")
                logger.info(f"🚩 [循环] 取消信号状态: {cancel_event.is_set()}")
                
                try:
                    # 使用 asyncio.wait_for 实现可中断的等待
                    await asyncio.wait_for(
                        cancel_event.wait(),
                        timeout=decision_interval
                    )
                    # 如果 wait() 返回了，说明收到取消信号
                    logger.info(f"🛑 [循环] 收到取消信号，退出循环")
                    break
                except asyncio.TimeoutError:
                    # 超时是正常的，继续下一次循环
                    logger.info(f"⏰ [循环] 等待超时，开始新周期")
                
                # 再次检查取消信号
                if cancel_event.is_set():
                    logger.info(f"🛑 [循环] 检测到取消信号，退出循环")
                    break
                
                loop_count += 1
                loop_start = time.time()
                
                logger.info("🔄" * 30)
                logger.info(f"🔄 决策周期 #{loop_count} 开始")
                logger.info(f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                
                try:
                    result = await agent.run_decision_cycle(symbols, risk_params)
                    
                    # 更新数据库
                    await self._increment_decision_count(session_id)
                    
                    logger.info(f"✅ 决策周期 #{loop_count} 完成, 成功={result.get('success')}")
                    
                    # 检查会话状态
                    if not await self._check_session_running(session_id):
                        logger.warning("⚠️ 会话已结束，停止循环")
                        break
                    
                except Exception as e:
                    logger.exception(f"❌ 决策周期 #{loop_count} 失败: {e}")
                    
                    # 记录错误到数据库
                    await self._update_session_status(
                        session_id=session_id,
                        last_error=str(e)
                    )
                
                loop_duration = time.time() - loop_start
                logger.info(f"⏱️ 本次周期耗时: {loop_duration:.2f}秒")
                logger.info("🔄" * 30)
            
            logger.info("🛑" * 30)
            logger.info("🛑 后台循环正常结束")
            logger.info(f"📊 总循环次数: {loop_count}")
            logger.info("🛑" * 30)
            
        except asyncio.CancelledError:
            logger.info(f"🛑 Task 被取消 (Session {session_id})")
            raise  # 重新抛出以正确处理取消
            
        except Exception as e:
            logger.exception(f"💥 后台循环异常终止: {e}")
            
            # 更新数据库：后台崩溃
            await self._update_session_status(
                session_id=session_id,
                background_status='crashed',
                last_error=str(e),
                background_stopped_at=datetime.now(timezone.utc)
            )
            
            # Agent 崩溃时，自动将会话状态改为 crashed
            try:
                db = next(get_db())
                try:
                    def update_session():
                        from .trading_session_service import TradingSessionService
                        session_service = TradingSessionService(db)
                        session_service.end_session(
                            session_id=session_id,
                            status='crashed',
                            notes=f'Agent 异常终止: {str(e)}'
                        )
                    
                    await asyncio.to_thread(update_session)
                    logger.info(f"✅ 已将会话 {session_id} 状态改为 crashed")
                except Exception as update_error:
                    logger.error(f"更新会话状态失败: {str(update_error)}")
                    try:
                        db.rollback()
                    except Exception:
                        pass
                finally:
                    try:
                        db.close()
                    except Exception as close_error:
                        logger.debug(f"关闭数据库会话时出错: {close_error}")
            except Exception as db_error:
                logger.error(f"数据库操作失败: {str(db_error)}")
        
        finally:
            logger.info(f"🔚 [loop] finally 块 - Session {session_id}")
            
            # 更新数据库：后台停止
            await self._update_session_status(
                session_id=session_id,
                background_status='stopped',
                background_stopped_at=datetime.now(timezone.utc)
            )
            
            logger.info(f"🎬 [loop] Task 即将退出 - Session {session_id}")
    
    async def _update_session_status(self, session_id: int, **kwargs):
        """
        更新会话状态字段
        
        Args:
            session_id: 会话 ID
            **kwargs: 要更新的字段（background_status, decision_count 等）
        """
        db = next(get_db())
        try:
            def update():
                from ..models.trading_session import TradingSession
                session = db.query(TradingSession).filter_by(id=session_id).first()
                if session:
                    for key, value in kwargs.items():
                        if hasattr(session, key):
                            setattr(session, key, value)
                    db.commit()
            
            await asyncio.to_thread(update)
        except Exception as e:
            logger.error(f"更新会话状态失败: {e}", session_id=session_id)
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception as close_error:
                logger.debug(f"关闭数据库会话时出错: {close_error}")
    
    async def _get_session_status(self, session_id: int) -> Optional[Dict[str, Any]]:
        """
        从数据库获取会话状态
        
        Args:
            session_id: 会话 ID
            
        Returns:
            会话状态字典
        """
        db = next(get_db())
        try:
            def query():
                from ..models.trading_session import TradingSession
                session = db.query(TradingSession).filter_by(id=session_id).first()
                if not session:
                    return None
                
                return {
                    'background_status': session.background_status,
                    'background_started_at': session.background_started_at,
                    'background_stopped_at': session.background_stopped_at,
                    'last_decision_time': session.last_decision_time,
                    'decision_count': session.decision_count,
                    'decision_interval': session.decision_interval,
                    'trading_symbols': session.trading_symbols,
                    'last_error': session.last_error,
                    'trading_params': session.trading_params
                }
            
            return await asyncio.to_thread(query)
        except Exception as e:
            logger.error(f"获取会话状态失败: {e}", session_id=session_id)
            return None
        finally:
            try:
                db.close()
            except Exception as close_error:
                logger.debug(f"关闭数据库会话时出错: {close_error}")
    
    async def _increment_decision_count(self, session_id: int):
        """
        增加决策执行次数并更新最后决策时间
        
        Args:
            session_id: 会话 ID
        """
        db = next(get_db())
        try:
            def update():
                from ..models.trading_session import TradingSession
                session = db.query(TradingSession).filter_by(id=session_id).first()
                if session:
                    session.decision_count = (session.decision_count or 0) + 1
                    session.last_decision_time = datetime.now(timezone.utc)
                    # 清除错误信息（成功执行后）
                    session.last_error = None
                    db.commit()
            
            await asyncio.to_thread(update)
        except asyncio.CancelledError:
            # 任务被取消，安全地回滚并关闭数据库连接
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.debug(f"回滚数据库失败: {rollback_error}")
            raise  # 重新抛出 CancelledError
        except Exception as e:
            logger.error(f"更新决策次数失败: {e}", session_id=session_id)
            try:
                db.rollback()
            except Exception:
                pass
        finally:
            try:
                db.close()
            except Exception as close_error:
                logger.debug(f"关闭数据库会话时出错: {close_error}")
    
    async def _check_session_running(self, session_id: int) -> bool:
        """检查会话是否仍在运行"""
        db = next(get_db())
        try:
            def query():
                session_repo = TradingSessionRepository(db)
                session = session_repo.get_by_id(session_id)
                return session is not None and session.status == 'running'
            
            return await asyncio.to_thread(query)
        except Exception as e:
            logger.debug(f"检查会话状态失败: {e}", session_id=session_id)
            return False
        finally:
            try:
                db.close()
            except Exception as close_error:
                logger.debug(f"关闭数据库会话时出错: {close_error}")


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
