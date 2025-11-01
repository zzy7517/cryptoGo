"""
技术指标计算服务
基于 pandas_ta 库计算各类技术指标，包括 EMA、MACD、RSI、ATR 等
创建时间: 2025-10-27
"""
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import List, Dict, Any, Optional
from functools import lru_cache

from .logging import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""
    
    def __init__(self):
        """初始化"""
        pass
    
    @staticmethod
    def _calculate_ema_manual(closes: List[float], period: int) -> List[float]:
        """
        手工计算EMA（指数移动平均线）
        
        使用标准EMA算法：
        1. 先计算前N个数据的SMA作为初始EMA
        2. 然后用公式迭代：EMA = (Price - EMA_prev) * multiplier + EMA_prev
        3. multiplier = 2 / (period + 1)
        
        Args:
            closes: 收盘价列表
            period: EMA周期
            
        Returns:
            EMA值列表
        """
        if len(closes) < period:
            # 数据不足，返回0填充
            return [0.0] * len(closes)
        
        result = []
        
        # 前period-1个值用0填充（因为还没有足够数据计算）
        for i in range(period - 1):
            result.append(0.0)
        
        # 计算初始EMA：使用前period个数据的SMA
        initial_sum = sum(closes[:period])
        ema = initial_sum / period
        result.append(ema)
        
        # 计算后续EMA值
        multiplier = 2.0 / (period + 1)
        for i in range(period, len(closes)):
            ema = (closes[i] - ema) * multiplier + ema
            result.append(ema)
        
        return result
    
    @staticmethod
    def _klines_to_dataframe(klines: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        将K线数据转换为DataFrame
        
        Args:
            klines: K线数据列表
            
        Returns:
            DataFrame with OHLCV columns
        """
        df = pd.DataFrame(klines)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        
        # 确保列名符合pandas_ta的要求（小写）
        df.columns = [col.lower() for col in df.columns]
        
        return df
    
    def calculate_ema(
        self, 
        klines: List[Dict[str, Any]], 
        periods: List[int] = [20, 50]
    ) -> Dict[str, List[float]]:
        """
        计算EMA (指数移动平均线)
        
        Args:
            klines: K线数据
            periods: EMA周期列表
            
        Returns:
            {
                'ema20': [...],
                'ema50': [...],
                'timestamps': [...]
            }
        """
        try:
            df = self._klines_to_dataframe(klines)
            
            result = {
                'timestamps': df.index.astype(np.int64) // 10**6  # 转换为毫秒
            }
            
            # 提取收盘价列表
            closes = df['close'].tolist()
            
            for period in periods:
                # 使用手工实现的EMA计算（标准算法）
                ema_values = self._calculate_ema_manual(closes, period)
                result[f'ema{period}'] = ema_values
                logger.debug(f"EMA{period} 计算完成，最新值: {ema_values[-1] if ema_values else 0:.2f}")
            
            logger.info(f"成功计算 EMA，周期: {periods}")
            return result
            
        except Exception as e:
            logger.error(f"计算EMA失败: {str(e)}")
            # 返回空列表而不是抛出异常，确保系统继续运行
            return {f'ema{p}': [] for p in periods}
    
    def calculate_macd(
        self, 
        klines: List[Dict[str, Any]],
        fast: int = 12,
        slow: int = 26, 
        signal: int = 9
    ) -> Dict[str, List[float]]:
        """
        计算MACD指标
        
        Args:
            klines: K线数据
            fast: 快线周期
            slow: 慢线周期
            signal: 信号线周期
            
        Returns:
            {
                'macd': [...],        # MACD线
                'signal': [...],      # 信号线
                'histogram': [...],   # 柱状图
                'timestamps': [...]
            }
        """
        try:
            df = self._klines_to_dataframe(klines)
            
            # pandas_ta的MACD返回DataFrame，包含MACD、MACDh(histogram)、MACDs(signal)
            macd_df = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
            
            if macd_df is not None:
                result = {
                    'timestamps': df.index.astype(np.int64) // 10**6,
                    'macd': macd_df[f'MACD_{fast}_{slow}_{signal}'].fillna(0).tolist(),
                    'signal': macd_df[f'MACDs_{fast}_{slow}_{signal}'].fillna(0).tolist(),
                    'histogram': macd_df[f'MACDh_{fast}_{slow}_{signal}'].fillna(0).tolist(),
                }
            else:
                logger.warning("MACD计算返回None，返回默认值")
                result = {
                    'timestamps': df.index.astype(np.int64) // 10**6,
                    'macd': [0] * len(df),
                    'signal': [0] * len(df),
                    'histogram': [0] * len(df),
                }
            
            logger.info(f"成功计算 MACD ({fast},{slow},{signal})")
            return result
            
        except Exception as e:
            logger.error(f"计算MACD失败: {str(e)}")
            return {'macd': [], 'signal': [], 'histogram': [], 'timestamps': []}
    
    def calculate_rsi(
        self, 
        klines: List[Dict[str, Any]], 
        periods: List[int] = [7, 14]
    ) -> Dict[str, List[float]]:
        """
        计算RSI (相对强弱指标)
        
        Args:
            klines: K线数据
            periods: RSI周期列表
            
        Returns:
            {
                'rsi7': [...],
                'rsi14': [...],
                'timestamps': [...]
            }
        """
        try:
            df = self._klines_to_dataframe(klines)
            
            result = {
                'timestamps': df.index.astype(np.int64) // 10**6
            }
            
            for period in periods:
                rsi = ta.rsi(df['close'], length=period)
                if rsi is not None:
                    result[f'rsi{period}'] = rsi.fillna(0).tolist()
                else:
                    logger.warning(f"RSI{period} 计算返回None，返回默认值")
                    result[f'rsi{period}'] = [50] * len(df)  # 默认中性值50
            
            logger.info(f"成功计算 RSI，周期: {periods}")
            return result
            
        except Exception as e:
            logger.error(f"计算RSI失败: {str(e)}")
            return {f'rsi{p}': [] for p in periods}
    
    def calculate_atr(
        self, 
        klines: List[Dict[str, Any]], 
        periods: List[int] = [3, 14]
    ) -> Dict[str, List[float]]:
        """
        计算ATR (平均真实波幅)
        
        Args:
            klines: K线数据
            periods: ATR周期列表
            
        Returns:
            {
                'atr3': [...],
                'atr14': [...],
                'timestamps': [...]
            }
        """
        try:
            df = self._klines_to_dataframe(klines)
            
            result = {
                'timestamps': df.index.astype(np.int64) // 10**6
            }
            
            for period in periods:
                atr = ta.atr(df['high'], df['low'], df['close'], length=period)
                if atr is not None:
                    result[f'atr{period}'] = atr.fillna(0).tolist()
                else:
                    logger.warning(f"ATR{period} 计算返回None，使用简化计算")
                    # 简化的ATR: high - low 的移动平均
                    tr = df['high'] - df['low']
                    result[f'atr{period}'] = tr.rolling(window=period).mean().fillna(0).tolist()
            
            logger.info(f"成功计算 ATR，周期: {periods}")
            return result
            
        except Exception as e:
            logger.error(f"计算ATR失败: {str(e)}")
            return {f'atr{p}': [] for p in periods}
    
    def calculate_all_indicators(
        self, 
        klines: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        计算所有技术指标
        
        Args:
            klines: K线数据
            
        Returns:
            包含所有指标的字典
        """
        try:
            result = {}
            
            # EMA
            ema_data = self.calculate_ema(klines, periods=[20, 50])
            result['ema'] = ema_data
            
            # MACD
            macd_data = self.calculate_macd(klines)
            result['macd'] = macd_data
            
            # RSI
            rsi_data = self.calculate_rsi(klines, periods=[7, 14])
            result['rsi'] = rsi_data
            
            # ATR
            atr_data = self.calculate_atr(klines, periods=[3, 14])
            result['atr'] = atr_data
            
            # 添加时间戳（使用第一个计算的时间戳）
            result['timestamps'] = ema_data['timestamps']
            
            logger.info("成功计算所有技术指标")
            return result
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {str(e)}")
            raise
    
    def get_latest_values(
        self, 
        klines: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """
        获取最新的指标值（用于实时显示）
        
        Args:
            klines: K线数据
            
        Returns:
            {
                'ema20': 50000.5,
                'ema50': 49500.2,
                'macd': 150.3,
                'signal': 145.2,
                'histogram': 5.1,
                'rsi7': 65.5,
                'rsi14': 62.3,
                'atr3': 120.5,
                'atr14': 150.8
            }
        """
        try:
            df = self._klines_to_dataframe(klines)
            closes = df['close'].tolist()
            
            # 计算各指标 - EMA使用手工实现
            ema20_values = self._calculate_ema_manual(closes, 20)
            ema50_values = self._calculate_ema_manual(closes, 50)
            
            macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
            rsi7 = ta.rsi(df['close'], length=7)
            rsi14 = ta.rsi(df['close'], length=14)
            atr3 = ta.atr(df['high'], df['low'], df['close'], length=3)
            atr14 = ta.atr(df['high'], df['low'], df['close'], length=14)
            
            # 获取最新值
            result = {
                'ema20': float(ema20_values[-1]) if ema20_values else 0.0,
                'ema50': float(ema50_values[-1]) if ema50_values else 0.0,
                'macd': float(macd_df['MACD_12_26_9'].iloc[-1]) if macd_df is not None and not pd.isna(macd_df['MACD_12_26_9'].iloc[-1]) else 0.0,
                'signal': float(macd_df['MACDs_12_26_9'].iloc[-1]) if macd_df is not None and not pd.isna(macd_df['MACDs_12_26_9'].iloc[-1]) else 0.0,
                'histogram': float(macd_df['MACDh_12_26_9'].iloc[-1]) if macd_df is not None and not pd.isna(macd_df['MACDh_12_26_9'].iloc[-1]) else 0.0,
                'rsi7': float(rsi7.iloc[-1]) if rsi7 is not None and not pd.isna(rsi7.iloc[-1]) else 0.0,
                'rsi14': float(rsi14.iloc[-1]) if rsi14 is not None and not pd.isna(rsi14.iloc[-1]) else 0.0,
                'atr3': float(atr3.iloc[-1]) if atr3 is not None and not pd.isna(atr3.iloc[-1]) else 0.0,
                'atr14': float(atr14.iloc[-1]) if atr14 is not None and not pd.isna(atr14.iloc[-1]) else 0.0,
            }
            
            logger.info("成功获取最新指标值")
            return result
            
        except Exception as e:
            logger.error(f"获取最新指标值失败: {str(e)}")
            raise


@lru_cache(maxsize=1)
def get_indicators_calculator() -> TechnicalIndicators:
    """
    获取指标计算器单例
    
    使用 lru_cache 确保只创建一个实例，线程安全
    """
    return TechnicalIndicators()


def calculate_indicators(klines: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算所有技术指标的辅助函数
    
    Args:
        klines: K线数据列表
        
    Returns:
        包含所有指标和最新值的字典
    """
    calculator = get_indicators_calculator()
    
    # 计算所有指标
    all_indicators = calculator.calculate_all_indicators(klines)
    
    # 获取最新值
    latest_values = calculator.get_latest_values(klines)
    
    return {
        'all_indicators': all_indicators,
        'latest_values': latest_values
    }

