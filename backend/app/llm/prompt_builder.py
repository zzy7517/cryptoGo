"""
Prompt Builder Service - 高级用户提示词构建
详细的市场数据和技术指标提示词构建服务
创建时间: 2025-10-31
"""

from typing import Dict, Any, List
from datetime import datetime
from pathlib import Path
import numpy as np

from ..utils.data_collector import get_exchange
from ..utils.indicators import get_indicators_calculator
from ..repositories.trading_session_repo import TradingSessionRepository
from ..repositories.trade_repo import TradeRepository
from ..utils.database import get_db
from ..utils.logging import get_logger

logger = get_logger(__name__)


class PromptDataCollector:
    """收集prompt需要的详细数据"""
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.exchange = get_exchange()  # 交易所实例
    
    async def collect_coin_data(self, symbol: str) -> Dict[str, Any]:
        """
        收集单个币种的所有数据
        
        Args:
            symbol: 交易对，如 'BTC/USDT:USDT'
            
        Returns:
            币种的完整数据
        """
        try:
            coin_name = symbol.split('/')[0]
            
            # 获取当前价格和ticker数据
            ticker = self.exchange.get_ticker(symbol)
            current_price = ticker.get('last') or 0
            
            mid_price = current_price  # 将在后续从K线数据中更新
            
            # 获取3分钟K线数据（40根用于计算，展示最后10根）
            klines_3m = self.exchange.get_klines(symbol, interval='3m', limit=40)
            
            # 获取4小时K线数据（60根用于计算长期指标）
            klines_4h = self.exchange.get_klines(symbol, interval='4h', limit=60)
            
            # 🆕 计算价格变化百分比
            price_change_1h = 0.0
            price_change_4h = 0.0
            
            # 使用K线数据计算当前价格（更准确）
            if klines_3m:
                current_price_from_kline = klines_3m[-1]['close']
                # 🔄 更新mid_price为K线的close价格
                mid_price = current_price_from_kline
                current_price = current_price_from_kline
                
                # 1小时价格变化：20个3分钟K线前（60分钟）
                if len(klines_3m) >= 21:
                    price_1h_ago = klines_3m[-21]['close']
                    if price_1h_ago > 0:
                        price_change_1h = ((current_price_from_kline - price_1h_ago) / price_1h_ago) * 100
                        logger.debug(f"{coin_name} 1h变化: {price_change_1h:+.2f}% ({price_1h_ago:.2f} -> {current_price_from_kline:.2f})")
            
            # 4小时价格变化：1个4小时K线前
            if klines_4h and len(klines_4h) >= 2:
                current_price_from_kline = klines_4h[-1]['close']
                price_4h_ago = klines_4h[-2]['close']
                if price_4h_ago > 0:
                    price_change_4h = ((current_price_from_kline - price_4h_ago) / price_4h_ago) * 100
                    logger.debug(f"{coin_name} 4h变化: {price_change_4h:+.2f}% ({price_4h_ago:.2f} -> {current_price_from_kline:.2f})")
            
            # 计算3分钟指标（传入symbol以获取实时价格）
            intraday_data = self._calculate_intraday_indicators(klines_3m, count=10, symbol=symbol)
            
            # 计算4小时指标
            longterm_data = self._calculate_longterm_indicators(klines_4h, count=10)
            
            # 获取资金费率
            funding_rate = None
            try:
                fr_data = self.exchange.get_funding_rate(symbol)
                funding_rate = fr_data.get('funding_rate', 0) if fr_data else 0
            except Exception as e:
                logger.debug(f"获取{symbol}资金费率失败: {e}")
                funding_rate = 0
            
            # 获取持仓量（需要计算平均值）
            open_interest_data = await self._get_open_interest_with_avg(symbol)
            
            return {
                'symbol': coin_name,
                'current_price': current_price,
                'mid_price': mid_price,
                'price_change_1h': price_change_1h,  # 🆕
                'price_change_4h': price_change_4h,  # 🆕
                'intraday': intraday_data,
                'longterm': longterm_data,
                'funding_rate': funding_rate,
                'open_interest': open_interest_data
            }
            
        except Exception as e:
            logger.error(f"收集{symbol}数据失败: {e}")
            return None
    
    def _calculate_intraday_indicators(self, klines: List[Dict], count: int = 10, symbol: str = None) -> Dict[str, Any]:
        """
        计算3分钟周期的指标（最近10根K线）
        
        Args:
            klines: K线数据
            count: 返回最近N根K线的数据
            symbol: 交易对（用于获取最新的实时价格）
            
        Returns:
            指标数据
        """
        if not klines or len(klines) < count:
            return {}
        
        try:
            calculator = get_indicators_calculator()
            
            # 只取最近的数据
            recent_klines = klines[-count:]
            
            # 提取价格序列：使用 close 价格作为 Mid Price
            # close 价格代表每个时间段的最终成交价，是最准确的价格参考
            mid_prices = [k['close'] for k in recent_klines]
            
            # 计算指标（使用所有数据以确保指标准确性）
            all_indicators = calculator.calculate_all_indicators(klines)
            
            # 提取最近10个数据点
            result = {
                'mid_prices': mid_prices,
                'ema_20': all_indicators['ema']['ema20'][-count:],
                'macd': all_indicators['macd']['macd'][-count:],
                'rsi_7': all_indicators['rsi']['rsi7'][-count:],
                'rsi_14': all_indicators['rsi']['rsi14'][-count:],
            }
            
            # 获取当前值
            result['current_ema20'] = result['ema_20'][-1] if result['ema_20'] else 0
            result['current_macd'] = result['macd'][-1] if result['macd'] else 0
            result['current_rsi7'] = result['rsi_7'][-1] if result['rsi_7'] else 0
            
            return result
            
        except Exception as e:
            logger.error(f"计算intraday指标失败: {e}")
            return {}
    
    def _calculate_longterm_indicators(self, klines: List[Dict], count: int = 10) -> Dict[str, Any]:
        """
        计算4小时周期的指标
        
        Args:
            klines: K线数据
            count: 返回最近N根K线的数据
            
        Returns:
            长期指标数据
        """
        if not klines or len(klines) < count:
            return {}
        
        try:
            calculator = get_indicators_calculator()
            
            # 计算所有指标
            all_indicators = calculator.calculate_all_indicators(klines)
            
            # 获取最新的完整K线（不包括当前未完成的K线）
            latest_kline = klines[-1]
            current_volume = latest_kline.get('volume', 0)
            
            volumes = [k.get('volume', 0) for k in klines]
            avg_volume = np.mean(volumes) if volumes else 0
            
            result = {
                'ema_20': all_indicators['ema']['ema20'][-1] if all_indicators['ema']['ema20'] else 0,
                'ema_50': all_indicators['ema']['ema50'][-1] if all_indicators['ema']['ema50'] else 0,
                'atr_3': all_indicators['atr']['atr3'][-1] if all_indicators['atr']['atr3'] else 0,
                'atr_14': all_indicators['atr']['atr14'][-1] if all_indicators['atr']['atr14'] else 0,
                'current_volume': current_volume,
                'avg_volume': avg_volume,
                'macd_series': all_indicators['macd']['macd'][-count:],
                'rsi_14_series': all_indicators['rsi']['rsi14'][-count:],
            }
            
            return result
            
        except Exception as e:
            logger.error(f"计算longterm指标失败: {e}")
            return {}
    
    async def _get_open_interest_with_avg(self, symbol: str) -> Dict[str, Any]:
        """
        获取持仓量及其平均值
        
        由于CCXT不直接提供历史持仓量，这里简化处理：
        使用当前持仓量作为最新值和平均值
        """
        try:
            oi_data = self.exchange.get_open_interest(symbol)
            oi_value = oi_data.get('open_interest', 0) if oi_data else 0
            
            return {
                'latest': oi_value,
                'average': oi_value * 0.999  # 近似平均值
            }
        except Exception as e:
            logger.debug(f"获取{symbol}持仓量失败: {e}")
            return {'latest': 0, 'average': 0}
    
    async def collect_account_data(self) -> Dict[str, Any]:
        """
        收集账户数据，包括Sharpe Ratio、保证金使用率等
        
        Returns:
            账户数据
        """
        db = next(get_db())
        try:
            session_repo = TradingSessionRepository(db)
            trade_repo = TradeRepository(db)
            
            session = session_repo.get_by_id(self.session_id)
            if not session:
                return {}
            
            initial_capital = float(session.initial_capital) if session.initial_capital else 0
            current_capital = float(session.current_capital) if session.current_capital else initial_capital
            
            total_pnl = current_capital - initial_capital
            total_return_pct = (total_pnl / initial_capital * 100) if initial_capital > 0 else 0
            
            # 计算Sharpe Ratio
            sharpe_ratio = await self._calculate_sharpe_ratio(self.session_id)
            
            # 🆕 从交易所获取实时账户信息
            try:
                account_info = self.exchange.get_account_info()

                # 🆕 打印原始账户信息
                logger.info("=" * 80)
                logger.info("📊 从交易所获取的原始账户信息:")
                logger.info(f"  totalWalletBalance: {account_info.get('totalWalletBalance', 'N/A')}")
                logger.info(f"  availableBalance: {account_info.get('availableBalance', 'N/A')}")
                logger.info(f"  totalMarginBalance: {account_info.get('totalMarginBalance', 'N/A')}")
                logger.info(f"  totalUnrealizedProfit: {account_info.get('totalUnrealizedProfit', 'N/A')}")
                logger.info("=" * 80)

                total_equity = float(account_info.get('totalWalletBalance', current_capital))
                available_balance = float(account_info.get('availableBalance', current_capital))

                # 获取持仓信息以计算保证金
                positions = self.exchange.get_positions()
                
                # 计算总保证金使用量
                # 保证金 = 仓位价值 / 杠杆
                total_margin_used = 0.0
                for pos in positions:
                    notional = abs(float(pos.get('notional', 0)))  # 仓位价值
                    leverage = float(pos.get('leverage', 1))
                    if leverage > 0:
                        margin = notional / leverage
                        total_margin_used += margin
                
                # 计算保证金使用率
                margin_used_pct = (total_margin_used / total_equity * 100) if total_equity > 0 else 0
                
                # 计算余额占比
                balance_pct = (available_balance / total_equity * 100) if total_equity > 0 else 0
                
                # 持仓数量
                position_count = len(positions)
                
                logger.info(f"💰 账户: 净值{total_equity:.2f}, 可用{available_balance:.2f}({balance_pct:.1f}%), "
                           f"保证金{margin_used_pct:.1f}%, 持仓{position_count}个")
                
                return {
                    'available_cash': available_balance,
                    'account_value': total_equity,
                    'total_return_pct': round(total_return_pct, 2),
                    'sharpe_ratio': round(sharpe_ratio, 3),
                    'balance_pct': round(balance_pct, 1),  # 🆕
                    'margin_used_pct': round(margin_used_pct, 1),  # 🆕
                    'position_count': position_count  # 🆕
                }
                
            except Exception as e:
                logger.warning(f"获取交易所账户信息失败，使用数据库数据: {e}")
                # Fallback到数据库数据
                return {
                    'available_cash': current_capital,
                    'account_value': current_capital,
                    'total_return_pct': round(total_return_pct, 2),
                    'sharpe_ratio': round(sharpe_ratio, 3),
                    'balance_pct': 100.0,
                    'margin_used_pct': 0.0,
                    'position_count': 0
                }
            
        finally:
            db.close()
    
    async def _calculate_sharpe_ratio(self, session_id: int) -> float:
        """
        计算Sharpe Ratio
        
        Sharpe Ratio = (平均回报率 - 无风险利率) / 回报率标准差
        简化处理：假设无风险利率为0
        """
        db = next(get_db())
        try:
            trade_repo = TradeRepository(db)
            
            # 获取所有已完成的交易
            trades = trade_repo.get_by_session(session_id)
            
            if not trades or len(trades) < 2:
                return 0.0
            
            # 计算每笔交易的回报率
            returns = []
            for trade in trades:
                if trade.pnl and trade.entry_price:
                    # 计算回报率 = PNL / (entry_price * quantity)
                    capital_used = float(trade.entry_price) * float(trade.quantity)
                    if capital_used > 0:
                        ret = float(trade.pnl) / capital_used
                        returns.append(ret)
            
            if not returns or len(returns) < 2:
                return 0.0
            
            # 计算平均回报率和标准差
            mean_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0.0
            
            # 计算Sharpe Ratio（年化处理可选）
            sharpe = mean_return / std_return
            
            return float(sharpe)
            
        except Exception as e:
            logger.error(f"计算Sharpe Ratio失败: {e}")
            return 0.0
        finally:
            db.close()
    
    async def collect_positions_detail(self) -> List[Dict[str, Any]]:
        """
        从交易所API收集详细的持仓信息（包括清算价格、订单ID等）

        Returns:
            持仓列表
        """
        try:
            # 直接从交易所API获取实时持仓
            positions = self.exchange.get_positions()
            
            # 获取所有未成交订单
            open_orders = self.exchange.get_open_orders()

            position_list = []
            for p in positions:
                # 过滤掉空持仓
                contracts = float(p.get('contracts', 0))
                if contracts == 0:
                    continue

                # 从交易所API返回的数据结构获取字段
                symbol = p.get('symbol', '')
                coin_symbol = symbol.split('/')[0] if '/' in symbol else symbol
                entry_price = float(p.get('entryPrice', 0))
                mark_price = float(p.get('markPrice', 0))
                liquidation_price = float(p.get('liquidationPrice', 0))
                unrealized_pnl = float(p.get('unrealizedPnl', 0))
                leverage = int(p.get('leverage', 1))
                side = p.get('side', 'long')
                notional = float(p.get('notional', 0))
                update_time = p.get('updateTime', 0)  # 获取更新时间
                
                # 🆕 计算持仓时长
                holding_duration = ""
                if update_time > 0:
                    from datetime import datetime
                    # updateTime 是毫秒时间戳
                    current_time_ms = int(datetime.now().timestamp() * 1000)
                    duration_ms = current_time_ms - update_time
                    duration_minutes = duration_ms // (1000 * 60)
                    
                    if duration_minutes < 60:
                        holding_duration = f"{duration_minutes}分钟"
                    else:
                        duration_hours = duration_minutes // 60
                        duration_min_remainder = duration_minutes % 60
                        holding_duration = f"{duration_hours}小时{duration_min_remainder}分钟"
                    
                    logger.debug(f"{coin_symbol} 持仓时长: {holding_duration}")
                
                # 从未成交订单中查找止盈止损订单
                sl_oid = -1
                tp_oid = -1
                stop_loss_price = None
                take_profit_price = None
                
                # 匹配订单：根据持仓方向和订单类型
                for order in open_orders:
                    if order.get('symbol') != symbol:
                        continue
                    
                    order_type = order.get('type', '')
                    order_side = order.get('side', '')
                    
                    # 对于多头持仓，止盈止损都是卖出
                    # 对于空头持仓，止盈止损都是买入
                    expected_side = 'SELL' if side == 'long' else 'BUY'
                    
                    if order_side == expected_side:
                        if 'STOP' in order_type and 'TAKE_PROFIT' not in order_type:
                            # 止损订单
                            sl_oid = int(order.get('orderId', -1))
                            stop_loss_price = float(order.get('stopPrice', 0)) or float(order.get('price', 0))
                        elif 'TAKE_PROFIT' in order_type:
                            # 止盈订单
                            tp_oid = int(order.get('orderId', -1))
                            take_profit_price = float(order.get('stopPrice', 0)) or float(order.get('price', 0))

                position_detail = {
                    'symbol': coin_symbol,
                    'quantity': contracts if side == 'long' else -contracts,  # 空头为负数
                    'entry_price': entry_price,
                    'current_price': mark_price,
                    'liquidation_price': round(liquidation_price, 2),
                    'unrealized_pnl': round(unrealized_pnl, 2),
                    'leverage': leverage,
                    'holding_duration': holding_duration,  # 🆕
                    'exit_plan': {
                        'profit_target': take_profit_price,
                        'stop_loss': stop_loss_price,
                        'invalidation_condition': 'N/A'  # 可以根据策略设置
                    },
                    'confidence': 0.65,  # 默认值
                    'risk_usd': abs(unrealized_pnl) if unrealized_pnl < 0 else 0,
                    'sl_oid': sl_oid,
                    'tp_oid': tp_oid,
                    'wait_for_fill': False,  # 默认值
                    'entry_oid': -1,  # 开仓订单已成交，无法从open_orders获取
                    'notional_usd': abs(notional)
                }

                position_list.append(position_detail)

            return position_list

        except Exception as e:
            logger.error(f"收集持仓详情失败: {e}")
            return []


class PromptBuilder:
    """高级Prompt构建器 - 详细市场数据和技术分析"""
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.collector = PromptDataCollector(session_id)
        self.template_path = Path(__file__).parent.parent / "prompts" / "user_prompt_template.txt"
    
    async def build_prompt(
        self, 
        symbols: List[str],
        call_count: int,
        start_time: datetime
    ) -> str:
        """
        构建完整的用户提示词
        
        Args:
            symbols: 交易对列表
            call_count: 调用次数
            start_time: 开始时间
            
        Returns:
            格式化的提示词
        """
        try:
            # 加载模板
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # 计算时长
            now = datetime.now()
            minutes_since_start = int((now - start_time).total_seconds() / 60)
            
            # 🆕 单独收集BTC数据用于市场概览
            btc_symbol = 'BTC/USDT:USDT'
            btc_overview = ""
            btc_data = None
            
            # 如果BTC不在symbols中，单独获取
            if btc_symbol not in symbols:
                logger.info("📊 获取BTC市场概览...")
                btc_data = await self.collector.collect_coin_data(btc_symbol)
            
            # 收集所有币种数据
            logger.info("📊 收集币种数据...")
            coins_data = []
            for symbol in symbols:
                coin_data = await self.collector.collect_coin_data(symbol)
                if coin_data:
                    coins_data.append(coin_data)
                    # 如果BTC在symbols中，记录下来用于概览
                    if symbol == btc_symbol:
                        btc_data = coin_data
            
            # 🆕 格式化BTC概览
            if btc_data:
                intraday = btc_data.get('intraday', {})
                btc_overview = (
                    f"**BTC**: {btc_data['current_price']:.2f} "
                    f"(1h: {btc_data.get('price_change_1h', 0):+.2f}%, "
                    f"4h: {btc_data.get('price_change_4h', 0):+.2f}%) | "
                    f"MACD: {intraday.get('current_macd', 0):.4f} | "
                    f"RSI: {intraday.get('current_rsi7', 0):.2f}\n\n"
                )
                logger.info(f"✅ BTC概览: 价格 {btc_data['current_price']:.2f}, "
                           f"1h {btc_data.get('price_change_1h', 0):+.2f}%, "
                           f"4h {btc_data.get('price_change_4h', 0):+.2f}%")
            
            # 格式化币种数据
            all_coins_text = self._format_all_coins_data(coins_data)
            
            # 收集账户数据
            logger.info("💰 收集账户数据...")
            account_data = await self.collector.collect_account_data()
            
            # 收集持仓数据
            logger.info("📦 收集持仓数据...")
            positions = await self.collector.collect_positions_detail()
            positions_text = self._format_positions(positions)
            
            # 填充模板
            prompt = template.format(
                minutes_since_start=minutes_since_start,
                current_time=now.strftime("%Y-%m-%d %H:%M:%S.%f"),
                call_count=call_count,
                btc_overview=btc_overview,  # 🆕
                all_coins_data=all_coins_text,
                total_return_pct=account_data.get('total_return_pct', 0),
                available_cash=account_data.get('available_cash', 0),
                account_value=account_data.get('account_value', 0),
                positions_detail=positions_text,
                sharpe_ratio=account_data.get('sharpe_ratio', 0),
                balance_pct=account_data.get('balance_pct', 0),  # 🆕
                margin_used_pct=account_data.get('margin_used_pct', 0),  # 🆕
                position_count=account_data.get('position_count', 0)  # 🆕
            )

            # 🆕 打印账户信息和持仓信息部分
            logger.info("=" * 80)
            logger.info("📋 传给AI的账户和持仓信息:")
            logger.info(f"  净值(account_value): ${account_data.get('account_value', 0):.2f}")
            logger.info(f"  可用余额(available_cash): ${account_data.get('available_cash', 0):.2f}")
            logger.info(f"  余额占比(balance_pct): {account_data.get('balance_pct', 0):.1f}%")
            logger.info(f"  保证金占用(margin_used_pct): {account_data.get('margin_used_pct', 0):.1f}%")
            logger.info(f"  持仓数量(position_count): {account_data.get('position_count', 0)}")
            logger.info(f"  持仓详情(positions_detail): {positions_text}")
            logger.info("=" * 80)

            logger.info("✅ 提示词构建完成")
            return prompt
            
        except Exception as e:
            logger.error(f"❌ 构建提示词失败: {e}")
            raise
    
    def _format_all_coins_data(self, coins_data: List[Dict[str, Any]]) -> str:
        """格式化所有币种数据"""
        lines = []
        
        for coin in coins_data:
            symbol = coin['symbol']
            intraday = coin.get('intraday', {})
            longterm = coin.get('longterm', {})
            
            lines.append(f"### {symbol}")
            # 🆕 添加价格变化百分比
            lines.append(f"current_price = {coin['current_price']:.2f}, " +
                        f"1h_change = {coin.get('price_change_1h', 0):+.2f}%, " +
                        f"4h_change = {coin.get('price_change_4h', 0):+.2f}%, " +
                        f"current_ema20 = {intraday.get('current_ema20', 0):.3f}, " +
                        f"current_macd = {intraday.get('current_macd', 0):.3f}, " +
                        f"current_rsi (7 period) = {intraday.get('current_rsi7', 0):.3f}")
            lines.append("")
            
            # 资金费率和持仓量
            lines.append(f"In addition, here is the latest {symbol} open interest and funding rate for perps (the instrument you are trading):")
            lines.append("")
            
            oi = coin.get('open_interest', {})
            lines.append(f"Open Interest: Latest: {oi.get('latest', 0):.2f} Average: {oi.get('average', 0):.2f}")
            lines.append("")
            
            fr = coin.get('funding_rate', 0)
            lines.append(f"Funding Rate: {fr:.8g}")
            lines.append("")
            
            # Intraday数据（3分钟）
            lines.append("Intraday series (3‑minute intervals, oldest → latest):")
            lines.append("")
            
            if intraday:
                # Mid prices - BTC和ETH不加前缀，其他币种加前缀
                # Mid prices 保持原始精度，不固定小数位
                mid_prices = intraday.get('mid_prices', [])
                if mid_prices:
                    formatted_mid_prices = self._format_mid_prices(mid_prices)
                    if symbol in ['BTC', 'ETH']:
                        lines.append(f"Mid prices: {formatted_mid_prices}")
                    else:
                        lines.append(f"{symbol} mid prices: {formatted_mid_prices}")
                    lines.append("")
                
                # EMA 20
                ema_20 = intraday.get('ema_20', [])
                if ema_20:
                    lines.append(f"EMA indicators (20‑period): {self._format_array(ema_20)}")
                    lines.append("")
                
                # MACD
                macd = intraday.get('macd', [])
                if macd:
                    lines.append(f"MACD indicators: {self._format_array(macd)}")
                    lines.append("")
                
                # RSI 7
                rsi_7 = intraday.get('rsi_7', [])
                if rsi_7:
                    lines.append(f"RSI indicators (7‑Period): {self._format_array(rsi_7)}")
                    lines.append("")
                
                # RSI 14
                rsi_14 = intraday.get('rsi_14', [])
                if rsi_14:
                    lines.append(f"RSI indicators (14‑Period): {self._format_array(rsi_14)}")
                    lines.append("")
            
            # 长期数据（4小时）
            lines.append("Longer‑term context (4‑hour timeframe):")
            lines.append("")
            
            if longterm:
                lines.append(f"20‑Period EMA: {longterm.get('ema_20', 0):.3f} vs. 50‑Period EMA: {longterm.get('ema_50', 0):.3f}")
                lines.append("")
                
                lines.append(f"3‑Period ATR: {longterm.get('atr_3', 0):.3f} vs. 14‑Period ATR: {longterm.get('atr_14', 0):.3f}")
                lines.append("")
                
                lines.append(f"Current Volume: {longterm.get('current_volume', 0):.3f} vs. Average Volume: {longterm.get('avg_volume', 0):.3f}")
                lines.append("")
                
                # MACD series
                macd_series = longterm.get('macd_series', [])
                if macd_series:
                    lines.append(f"MACD indicators: {self._format_array(macd_series)}")
                    lines.append("")
                
                # RSI 14 series
                rsi_14_series = longterm.get('rsi_14_series', [])
                if rsi_14_series:
                    lines.append(f"RSI indicators (14‑Period): {self._format_array(rsi_14_series)}")
                    lines.append("")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_positions(self, positions: List[Dict[str, Any]]) -> str:
        """格式化持仓信息"""
        if not positions:
            return "No positions"
        
        # 将每个持仓格式化为类似example的字符串（保持单引号）
        formatted_positions = []
        for pos in positions:
            pos_str = str(pos)  # 保持Python dict的原始格式（使用单引号）
            formatted_positions.append(pos_str)
        
        return " ".join(formatted_positions)
    
    def _format_array(self, arr: List[float], precision: int = 3) -> str:
        """格式化数组为字符串"""
        if not arr:
            return "[]"
        
        formatted_values = [f"{v:.{precision}f}" if isinstance(v, (int, float)) else str(v) for v in arr]
        return "[" + ", ".join(formatted_values) + "]"
    
    def _format_mid_prices(self, arr: List[float]) -> str:
        """格式化 Mid Prices 数组，保持原始精度"""
        if not arr:
            return "[]"
        
        # 保持原始精度，使用 Python 的默认格式化
        formatted_values = [str(float(v)) for v in arr]
        return "[" + ", ".join(formatted_values) + "]"


# 便捷函数
async def build_user_prompt(
    session_id: int,
    symbols: List[str],
    call_count: int,
    start_time: datetime
) -> str:
    """
    构建高级用户提示词的便捷函数
    
    Args:
        session_id: 交易会话ID
        symbols: 交易对列表
        call_count: 调用次数
        start_time: 开始时间
        
    Returns:
        格式化的提示词
    """
    builder = PromptBuilder(session_id)
    return await builder.build_prompt(symbols, call_count, start_time)

