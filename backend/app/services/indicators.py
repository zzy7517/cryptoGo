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

from app.core.logging import get_logger

logger = get_logger(__name__)


class TechnicalIndicators:
    """技术指标计算器"""
    
    def __init__(self):
        """初始化"""
        pass
    
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
            
            for period in periods:
                ema = ta.ema(df['close'], length=period)
                result[f'ema{period}'] = ema.fillna(0).tolist()
            
            logger.info(f"成功计算 EMA，周期: {periods}")
            return result
            
        except Exception as e:
            logger.error(f"计算EMA失败: {str(e)}")
            raise
    
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
            
            result = {
                'timestamps': df.index.astype(np.int64) // 10**6,
                'macd': macd_df[f'MACD_{fast}_{slow}_{signal}'].fillna(0).tolist(),
                'signal': macd_df[f'MACDs_{fast}_{slow}_{signal}'].fillna(0).tolist(),
                'histogram': macd_df[f'MACDh_{fast}_{slow}_{signal}'].fillna(0).tolist(),
            }
            
            logger.info(f"成功计算 MACD ({fast},{slow},{signal})")
            return result
            
        except Exception as e:
            logger.error(f"计算MACD失败: {str(e)}")
            raise
    
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
                result[f'rsi{period}'] = rsi.fillna(0).tolist()
            
            logger.info(f"成功计算 RSI，周期: {periods}")
            return result
            
        except Exception as e:
            logger.error(f"计算RSI失败: {str(e)}")
            raise
    
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
                result[f'atr{period}'] = atr.fillna(0).tolist()
            
            logger.info(f"成功计算 ATR，周期: {periods}")
            return result
            
        except Exception as e:
            logger.error(f"计算ATR失败: {str(e)}")
            raise
    
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
            
            # 计算各指标
            ema20 = ta.ema(df['close'], length=20)
            ema50 = ta.ema(df['close'], length=50)
            macd_df = ta.macd(df['close'], fast=12, slow=26, signal=9)
            rsi7 = ta.rsi(df['close'], length=7)
            rsi14 = ta.rsi(df['close'], length=14)
            atr3 = ta.atr(df['high'], df['low'], df['close'], length=3)
            atr14 = ta.atr(df['high'], df['low'], df['close'], length=14)
            
            # 获取最新值
            result = {
                'ema20': float(ema20.iloc[-1]) if not pd.isna(ema20.iloc[-1]) else 0.0,
                'ema50': float(ema50.iloc[-1]) if not pd.isna(ema50.iloc[-1]) else 0.0,
                'macd': float(macd_df['MACD_12_26_9'].iloc[-1]) if not pd.isna(macd_df['MACD_12_26_9'].iloc[-1]) else 0.0,
                'signal': float(macd_df['MACDs_12_26_9'].iloc[-1]) if not pd.isna(macd_df['MACDs_12_26_9'].iloc[-1]) else 0.0,
                'histogram': float(macd_df['MACDh_12_26_9'].iloc[-1]) if not pd.isna(macd_df['MACDh_12_26_9'].iloc[-1]) else 0.0,
                'rsi7': float(rsi7.iloc[-1]) if not pd.isna(rsi7.iloc[-1]) else 0.0,
                'rsi14': float(rsi14.iloc[-1]) if not pd.isna(rsi14.iloc[-1]) else 0.0,
                'atr3': float(atr3.iloc[-1]) if not pd.isna(atr3.iloc[-1]) else 0.0,
                'atr14': float(atr14.iloc[-1]) if not pd.isna(atr14.iloc[-1]) else 0.0,
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

