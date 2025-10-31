"""
Prompt Builder Service - 高级用户提示词构建
基于 nofx 风格的详细市场数据提示词
创建时间: 2025-10-31
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
from decimal import Decimal

from app.services.data_collector import get_exchange_connector
from app.services.indicators import calculate_indicators, get_indicators_calculator
from app.repositories.trading_session_repo import TradingSessionRepository
from app.repositories.position_repo import PositionRepository
from app.repositories.trade_repo import TradeRepository
from app.utils.database import get_db
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PromptDataCollector:
    """收集prompt需要的详细数据"""
    
    def __init__(self, session_id: int):
        self.session_id = session_id
        self.exchange = get_exchange_connector()
    
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
            
            # 获取当前价格
            ticker = self.exchange.get_ticker(symbol)
            current_price = ticker.get('last', 0)
            mid_price = (ticker.get('bid', current_price) + ticker.get('ask', current_price)) / 2
            
            # 获取3分钟K线数据（最近10根）
            klines_3m = self.exchange.get_klines(symbol, interval='3m', limit=30)
            
            # 获取4小时K线数据（最近30根，用于计算长期指标）
            klines_4h = self.exchange.get_klines(symbol, interval='4h', limit=30)
            
            # 计算3分钟指标
            intraday_data = self._calculate_intraday_indicators(klines_3m, count=10)
            
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
                'intraday': intraday_data,
                'longterm': longterm_data,
                'funding_rate': funding_rate,
                'open_interest': open_interest_data
            }
            
        except Exception as e:
            logger.error(f"收集{symbol}数据失败: {e}")
            return None
    
    def _calculate_intraday_indicators(self, klines: List[Dict], count: int = 10) -> Dict[str, Any]:
        """
        计算3分钟周期的指标（最近10根K线）
        
        Args:
            klines: K线数据
            count: 返回最近N根K线的数据
            
        Returns:
            指标数据
        """
        if not klines or len(klines) < count:
            return {}
        
        try:
            calculator = get_indicators_calculator()
            
            # 只取最近的数据
            recent_klines = klines[-count:]
            
            # 提取价格序列
            mid_prices = [(k['high'] + k['low']) / 2 for k in recent_klines]
            
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
            
            # 计算平均成交量（最近20根K线）
            volumes = [k.get('volume', 0) for k in klines[-20:]]
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
                'average': oi_value  # 简化处理，后续可以实现历史数据存储
            }
        except Exception as e:
            logger.debug(f"获取{symbol}持仓量失败: {e}")
            return {'latest': 0, 'average': 0}
    
    async def collect_account_data(self) -> Dict[str, Any]:
        """
        收集账户数据，包括Sharpe Ratio
        
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
            
            return {
                'available_cash': current_capital,
                'account_value': current_capital,
                'total_return_pct': round(total_return_pct, 2),
                'sharpe_ratio': round(sharpe_ratio, 3)
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
            trades = trade_repo.get_trades_by_session(session_id)
            
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
        收集详细的持仓信息（包括清算价格等）
        
        Returns:
            持仓列表
        """
        db = next(get_db())
        try:
            position_repo = PositionRepository(db)
            positions = position_repo.get_active_positions(self.session_id)
            
            position_list = []
            for p in positions:
                # 计算清算价格（简化公式）
                # 做多: liquidation_price = entry_price * (1 - 1/leverage)
                # 做空: liquidation_price = entry_price * (1 + 1/leverage)
                entry_price = float(p.entry_price)
                leverage = p.leverage if p.leverage else 1
                
                if p.side == 'long':
                    liquidation_price = entry_price * (1 - 0.9 / leverage)
                else:  # short
                    liquidation_price = entry_price * (1 + 0.9 / leverage)
                
                # 获取当前价格
                try:
                    ticker = self.exchange.get_ticker(p.symbol)
                    current_price = ticker.get('last', entry_price)
                except:
                    current_price = entry_price
                
                # 计算未实现盈亏
                quantity = float(p.quantity)
                if p.side == 'long':
                    unrealized_pnl = (current_price - entry_price) * quantity * leverage
                else:  # short
                    unrealized_pnl = (entry_price - current_price) * quantity * leverage
                
                position_detail = {
                    'symbol': p.symbol.split('/')[0] if '/' in p.symbol else p.symbol,
                    'quantity': quantity,
                    'entry_price': entry_price,
                    'current_price': current_price,
                    'liquidation_price': round(liquidation_price, 2),
                    'unrealized_pnl': round(unrealized_pnl, 2),
                    'leverage': leverage,
                    'exit_plan': {
                        'profit_target': float(p.take_profit) if p.take_profit else None,
                        'stop_loss': float(p.stop_loss) if p.stop_loss else None,
                        'invalidation_condition': 'N/A'  # 可以后续增强
                    },
                    'confidence': 0.65,  # 默认值，后续可以从AI决策中获取
                    'risk_usd': abs(unrealized_pnl) if unrealized_pnl < 0 else 0,
                    'notional_usd': current_price * quantity * leverage
                }
                
                position_list.append(position_detail)
            
            return position_list
            
        finally:
            db.close()


class AdvancedPromptBuilder:
    """高级Prompt构建器 - nofx风格"""
    
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
        logger.info("🔨 开始构建高级提示词")
        
        try:
            # 加载模板
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # 计算时长
            now = datetime.now()
            minutes_since_start = int((now - start_time).total_seconds() / 60)
            
            # 收集所有币种数据
            logger.info("📊 收集币种数据...")
            coins_data = []
            for symbol in symbols:
                coin_data = await self.collector.collect_coin_data(symbol)
                if coin_data:
                    coins_data.append(coin_data)
            
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
                all_coins_data=all_coins_text,
                total_return_pct=account_data.get('total_return_pct', 0),
                available_cash=account_data.get('available_cash', 0),
                account_value=account_data.get('account_value', 0),
                positions_detail=positions_text,
                sharpe_ratio=account_data.get('sharpe_ratio', 0)
            )
            
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
            
            lines.append(f"ALL {symbol} DATA")
            lines.append(f"current_price = {coin['current_price']}, " +
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
            lines.append("Intraday series (by minute, oldest → latest):")
            lines.append("")
            
            if intraday:
                # Mid prices
                mid_prices = intraday.get('mid_prices', [])
                if mid_prices:
                    lines.append(f"Mid prices: {self._format_array(mid_prices)}")
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
        
        # 将每个持仓格式化为类似example的字符串
        formatted_positions = []
        for pos in positions:
            pos_str = str(pos).replace("'", '"')  # 转换为类似JSON的格式
            formatted_positions.append(pos_str)
        
        return " ".join(formatted_positions)
    
    def _format_array(self, arr: List[float], precision: int = 3) -> str:
        """格式化数组为字符串"""
        if not arr:
            return "[]"
        
        formatted_values = [f"{v:.{precision}f}" if isinstance(v, (int, float)) else str(v) for v in arr]
        return "[" + ", ".join(formatted_values) + "]"


# 便捷函数
async def build_advanced_prompt(
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
    builder = AdvancedPromptBuilder(session_id)
    return await builder.build_prompt(symbols, call_count, start_time)

