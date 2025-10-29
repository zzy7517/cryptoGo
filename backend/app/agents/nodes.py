"""
LangGraph Trading Agent Nodes
定义交易代理的各个节点函数
创建时间: 2025-10-29
"""
from typing import Dict, Any
from datetime import datetime
from decimal import Decimal

from app.agents.state import TradingState
from app.services.data_collector import get_exchange_connector
from app.services.indicators import calculate_indicators
from app.services.ai_engine import get_ai_engine
from app.core.database import get_db
from app.repositories.trading_session_repo import TradingSessionRepository
from app.repositories.position_repo import PositionRepository
from app.repositories.ai_decision_repo import AIDecisionRepository
from app.repositories.account_snapshot_repo import AccountSnapshotRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


def collect_market_data(state: TradingState) -> TradingState:
    """
    节点1: 收集市场数据
    
    获取实时价格、K线、技术指标、资金费率等市场数据
    """
    logger.info(
        "收集市场数据",
        session_id=state['session_id'],
        loop_count=state['loop_count']
    )
    
    state['current_node'] = 'collect_market_data'
    state['last_update_time'] = datetime.now().isoformat()
    
    try:
        exchange = get_exchange_connector()
        market_data = {}
        
        # 获取第一个交易对的数据（主要分析对象）
        primary_symbol = state['symbols'][0] if state['symbols'] else 'BTC/USDT:USDT'
        
        # 1. 获取实时价格
        ticker = exchange.get_ticker(primary_symbol)
        market_data['ticker'] = ticker
        
        # 2. 获取K线数据
        klines = exchange.get_klines(primary_symbol, interval='1h', limit=100)
        market_data['klines'] = klines
        
        # 3. 计算技术指标
        if klines:
            indicators = calculate_indicators(klines)
            market_data['indicators'] = indicators.get('latest_values', {})
        
        # 4. 获取资金费率（合约特有）
        try:
            funding_rate = exchange.get_funding_rate(primary_symbol)
            market_data['funding_rate'] = funding_rate
        except Exception as e:
            logger.warning(
                "获取资金费率失败",
                session_id=state['session_id'],
                symbol=primary_symbol,
                error=str(e)
            )
            market_data['funding_rate'] = None
        
        # 5. 获取持仓量
        try:
            open_interest = exchange.get_open_interest(primary_symbol)
            market_data['open_interest'] = open_interest
        except Exception as e:
            logger.warning(
                "获取持仓量失败",
                session_id=state['session_id'],
                symbol=primary_symbol,
                error=str(e)
            )
            market_data['open_interest'] = None
        
        state['market_data'] = market_data
        state['error_count'] = 0  # 重置错误计数
        
        logger.info(
            "市场数据收集完成",
            session_id=state['session_id'],
            symbol=primary_symbol,
            price=ticker.get('last')
        )
        
    except Exception as e:
        error_msg = f"收集市场数据失败: {str(e)}"
        logger.exception(
            "收集市场数据失败",
            session_id=state['session_id'],
            node="collect_market_data",
            loop_count=state.get('loop_count', 0)
        )
        state['last_error'] = error_msg
        state['error_count'] = state.get('error_count', 0) + 1
    
    return state


def analyze_market(state: TradingState) -> TradingState:
    """
    节点2: AI 市场分析
    
    使用 DeepSeek AI 分析市场数据并生成交易决策
    """
    logger.info(
        "AI 市场分析",
        session_id=state['session_id'],
        loop_count=state.get('loop_count', 0)
    )
    
    state['current_node'] = 'analyze_market'
    state['last_update_time'] = datetime.now().isoformat()
    
    try:
        ai_engine = get_ai_engine()
        
        # 构建分析上下文
        context = f"""
当前持仓情况：
- 活跃持仓数: {len(state['active_positions'])}
- 可用资金: ${state['available_capital']:.2f}
- 账户总价值: ${state['total_value']:.2f}

风险参数：
- 最大单仓: {state['risk_params']['max_position_size'] * 100}%
- 止损: {state['risk_params']['stop_loss_pct'] * 100}%
- 止盈: {state['risk_params']['take_profit_pct'] * 100}%
- 最大杠杆: {state['risk_params']['max_leverage']}x
- 最大持仓数: {state['risk_params']['max_positions']}

请基于市场数据给出交易建议：buy (买入/做多)、sell (卖出/做空)、hold (观望)、close (平仓)
同时给出置信度 (0-1) 和详细推理。
"""
        
        # 调用 AI 分析（不保存到数据库，稍后在 execute 节点保存）
        result = ai_engine.analyze_market(
            market_data=state['market_data'],
            context=context,
            save_to_db=False
        )
        
        # 解析 AI 响应，提取决策信息
        ai_response = result['analysis']
        decision_type = 'hold'  # 默认观望
        confidence = 0.5
        
        # 简单的关键词匹配（后续可以让 AI 返回结构化 JSON）
        if '买入' in ai_response or '做多' in ai_response or 'buy' in ai_response.lower():
            decision_type = 'buy'
            confidence = 0.7
        elif '卖出' in ai_response or '做空' in ai_response or 'sell' in ai_response.lower():
            decision_type = 'sell'
            confidence = 0.7
        elif '平仓' in ai_response or 'close' in ai_response.lower():
            decision_type = 'close'
            confidence = 0.8
        
        # 如果已达到最大持仓数，不建议开新仓
        if len(state['active_positions']) >= state['risk_params']['max_positions']:
            if decision_type in ['buy', 'sell']:
                decision_type = 'hold'
                ai_response += "\n\n[系统提示] 已达到最大持仓数限制，暂不开新仓。"
        
        state['last_decision'] = {
            'decision_type': decision_type,
            'confidence': confidence,
            'reasoning': ai_response,
            'suggested_actions': {
                'symbol': state['symbols'][0] if state['symbols'] else 'BTC/USDT:USDT',
                'action': decision_type,
                'confidence': confidence
            }
        }
        
        state['error_count'] = 0
        
        logger.info(
            "AI 分析完成",
            session_id=state['session_id'],
            decision=decision_type,
            confidence=confidence
        )
        
    except Exception as e:
        error_msg = f"AI 分析失败: {str(e)}"
        logger.exception(
            "AI 分析失败",
            session_id=state['session_id'],
            node="analyze_market",
            loop_count=state.get('loop_count', 0)
        )
        state['last_error'] = error_msg
        state['error_count'] = state.get('error_count', 0) + 1
        
        # 设置默认决策
        state['last_decision'] = {
            'decision_type': 'hold',
            'confidence': 0.0,
            'reasoning': f'分析失败: {error_msg}',
            'suggested_actions': {}
        }
    
    return state


def execute_decision(state: TradingState) -> TradingState:
    """
    节点3: 执行决策
    
    将 AI 决策保存到数据库
    注意：暂不执行实际交易，仅记录决策
    """
    logger.info(
        "执行决策",
        session_id=state['session_id'],
        decision_type=state.get('last_decision', {}).get('decision_type', 'unknown')
    )
    
    state['current_node'] = 'execute_decision'
    state['last_update_time'] = datetime.now().isoformat()
    
    try:
        # 获取数据库会话
        db = next(get_db())
        
        try:
            decision_repo = AIDecisionRepository(db)
            
            decision = state.get('last_decision', {})
            
            # 保存决策到数据库
            db_decision = decision_repo.save_decision(
                session_id=state['session_id'],
                symbols=[state['symbols'][0]] if state['symbols'] else ['BTC/USDT:USDT'],
                decision_type=decision.get('decision_type', 'hold'),
                confidence=Decimal(str(decision.get('confidence', 0.5))),
                prompt_data=state.get('market_data', {}),
                ai_response=decision.get('reasoning', ''),
                reasoning=decision.get('reasoning', ''),
                suggested_actions=decision.get('suggested_actions', {}),
                executed=False  # 暂不执行实际交易
            )
            
            state['last_decision_id'] = db_decision.id
            state['error_count'] = 0
            
            logger.info(
                "决策已保存",
                session_id=state['session_id'],
                decision_id=db_decision.id,
                decision_type=decision.get('decision_type')
            )
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"执行决策失败: {str(e)}"
        logger.exception(
            "执行决策失败",
            session_id=state['session_id'],
            node="execute_decision",
            decision_id=state.get('last_decision_id')
        )
        state['last_error'] = error_msg
        state['error_count'] = state.get('error_count', 0) + 1
    
    return state


def update_positions(state: TradingState) -> TradingState:
    """
    节点4: 更新持仓
    
    从数据库读取活跃持仓，更新当前价格和未实现盈亏
    """
    logger.info(
        "更新持仓",
        session_id=state['session_id'],
        active_positions_count=len(state.get('active_positions', []))
    )
    
    state['current_node'] = 'update_positions'
    state['last_update_time'] = datetime.now().isoformat()
    
    try:
        db = next(get_db())
        
        try:
            position_repo = PositionRepository(db)
            
            # 获取活跃持仓
            positions = position_repo.get_active_positions(state['session_id'])
            
            # 更新持仓价格
            if positions and state.get('market_data'):
                current_price = state['market_data'].get('ticker', {}).get('last')
                
                if current_price:
                    for pos in positions:
                        # 只更新匹配的交易对
                        if pos.symbol in state['symbols']:
                            position_repo.update_price(
                                pos.id,
                                Decimal(str(current_price))
                            )
            
            # 刷新持仓列表
            positions = position_repo.get_active_positions(state['session_id'])
            
            # 转换为字典列表
            state['active_positions'] = [
                {
                    'id': p.id,
                    'symbol': p.symbol,
                    'side': p.side,
                    'quantity': float(p.quantity),
                    'entry_price': float(p.entry_price),
                    'current_price': float(p.current_price) if p.current_price else float(p.entry_price),
                    'unrealized_pnl': float(p.unrealized_pnl) if p.unrealized_pnl else 0.0,
                    'leverage': p.leverage
                }
                for p in positions
            ]
            
            # 计算总未实现盈亏
            total_unrealized_pnl = sum(p['unrealized_pnl'] for p in state['active_positions'])
            
            state['error_count'] = 0
            
            logger.info(
                "持仓已更新",
                session_id=state['session_id'],
                positions_count=len(state['active_positions']),
                unrealized_pnl=total_unrealized_pnl
            )
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"更新持仓失败: {str(e)}"
        logger.exception(
            "更新持仓失败",
            session_id=state['session_id'],
            node="update_positions",
            positions_count=len(state.get('active_positions', []))
        )
        state['last_error'] = error_msg
        state['error_count'] = state.get('error_count', 0) + 1
    
    return state


def create_snapshot(state: TradingState) -> TradingState:
    """
    节点5: 创建账户快照
    
    记录当前账户状态到数据库
    """
    logger.info(
        "创建账户快照",
        session_id=state['session_id'],
        loop_count=state.get('loop_count', 0)
    )
    
    state['current_node'] = 'create_snapshot'
    state['last_update_time'] = datetime.now().isoformat()
    
    try:
        db = next(get_db())
        
        try:
            snapshot_repo = AccountSnapshotRepository(db)
            session_repo = TradingSessionRepository(db)
            
            # 获取会话信息
            session = session_repo.get_by_id(state['session_id'])
            if not session:
                raise Exception(f"会话 {state['session_id']} 不存在")
            
            # 计算总价值和盈亏
            total_unrealized_pnl = sum(p['unrealized_pnl'] for p in state['active_positions'])
            total_value = state['available_capital'] + total_unrealized_pnl
            
            initial_capital = float(session.initial_capital) if session.initial_capital else state['available_capital']
            total_pnl = total_value - initial_capital
            total_return_pct = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0
            
            # 更新状态
            state['total_value'] = total_value
            
            # 创建快照
            snapshot_repo.create_snapshot(
                session_id=state['session_id'],
                total_value=Decimal(str(total_value)),
                available_cash=Decimal(str(state['available_capital'])),
                total_pnl=Decimal(str(total_pnl)),
                total_return_pct=Decimal(str(total_return_pct)),
                positions_summary={'positions': state['active_positions']},
                ai_decision_id=state.get('last_decision_id')
            )
            
            # 增加循环计数
            state['loop_count'] = state.get('loop_count', 0) + 1
            state['error_count'] = 0
            
            logger.info(
                "快照已创建",
                session_id=state['session_id'],
                loop_count=state['loop_count'],
                total_value=total_value,
                total_pnl=total_pnl
            )
            
        finally:
            db.close()
            
    except Exception as e:
        error_msg = f"创建快照失败: {str(e)}"
        logger.exception(
            "创建快照失败",
            session_id=state['session_id'],
            node="create_snapshot",
            loop_count=state.get('loop_count', 0)
        )
        state['last_error'] = error_msg
        state['error_count'] = state.get('error_count', 0) + 1
    
    return state


def check_continue(state: TradingState) -> str:
    """
    条件边: 检查是否继续循环
    
    Returns:
        'continue': 继续循环
        'stop': 停止循环
    """
    # 检查会话是否仍在运行
    try:
        db = next(get_db())
        try:
            session_repo = TradingSessionRepository(db)
            session = session_repo.get_by_id(state['session_id'])
            
            if not session:
                logger.warning(
                    "会话不存在，停止循环",
                    session_id=state['session_id']
                )
                return 'stop'
            
            if session.status != 'running':
                logger.info(
                    "会话已停止，Agent 循环结束",
                    session_id=state['session_id'],
                    status=session.status
                )
                return 'stop'
            
            # 检查连续错误次数
            if state.get('error_count', 0) >= 5:
                logger.error(
                    "连续错误次数过多，停止循环",
                    session_id=state['session_id'],
                    error_count=state['error_count']
                )
                # 标记会话为 crashed
                session_repo.update(state['session_id'], status='crashed')
                return 'stop'
            
            return 'continue'
            
        finally:
            db.close()
            
    except Exception as e:
        logger.exception(
            "检查继续状态失败",
            session_id=state['session_id']
        )
        return 'stop'

