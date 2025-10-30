'use client';

/**
 * 技术指标展示组件 (Technical Indicators Component)
 * 
 * 展示加密货币的技术分析指标，提供可视化的指标状态判断
 * 创建时间: 2025-10-27
 * 
 * 文件作用：
 * - 展示加密货币的技术分析指标
 * - 提供可视化的指标状态判断
 * 
 * 支持的技术指标：
 * 1. EMA (指数移动平均线)
 *    - EMA(20): 短期均线
 *    - EMA(50): 长期均线
 *    - 显示短期趋势方向（金叉/死叉）
 * 
 * 2. MACD (平滑异同移动平均线)
 *    - MACD线、信号线、柱状图
 *    - 判断看涨/看跌趋势
 * 
 * 3. RSI (相对强弱指标)
 *    - RSI(7): 短期超买超卖
 *    - RSI(14): 标准超买超卖指标
 *    - 可视化进度条（70超买、30超卖）
 * 
 * 4. ATR (平均真实波幅)
 *    - ATR(3): 短期波动率
 *    - ATR(14): 标准波动率
 *    - 判断市场波动性
 * 
 * Props：
 * - indicators: IndicatorLatestValues | null - 指标数据
 * - loading?: boolean - 加载状态
 * 
 * UI特性：
 * - 加载骨架屏动画
 * - 颜色编码（绿色=看涨/超卖，红色=看跌/超买）
 * - RSI 可视化进度条
 * - 智能状态判断和提示
 * 
 * 使用示例：
 * <TechnicalIndicators indicators={data} loading={false} />
 */
import React from 'react';
import type { IndicatorLatestValues } from '@/types/market';

interface TechnicalIndicatorsProps {
  indicators: IndicatorLatestValues | null;
  loading?: boolean;
}

export default function TechnicalIndicators({ indicators, loading }: TechnicalIndicatorsProps) {
  const formatNumber = (num: number | null | undefined, decimals: number = 2): string => {
    if (num === null || num === undefined) return '--';
    return num.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  // 判断RSI超买超卖
  const getRSIStatus = (rsi: number): { color: string; label: string } => {
    if (rsi >= 70) return { color: 'text-red-500', label: '超买' };
    if (rsi <= 30) return { color: 'text-green-500', label: '超卖' };
    return { color: 'text-gray-700', label: '正常' };
  };

  // 判断MACD趋势
  const getMACDStatus = (histogram: number): { color: string; label: string } => {
    if (histogram > 0) return { color: 'text-green-500', label: '看涨' };
    if (histogram < 0) return { color: 'text-red-500', label: '看跌' };
    return { color: 'text-gray-700', label: '中性' };
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="bg-white rounded-lg p-6 animate-pulse shadow-sm border border-gray-200">
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
            <div className="h-3 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (!indicators) {
    return (
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <p className="text-gray-600 text-center">暂无技术指标数据</p>
      </div>
    );
  }

  const rsi14Status = getRSIStatus(indicators.rsi14);
  const macdStatus = getMACDStatus(indicators.histogram);

  return (
    <div className="space-y-4">
      {/* EMA 指标 */}
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-4">EMA (指数移动平均线)</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">EMA(20)</span>
            <span className="font-bold text-teal-600">
              ${formatNumber(indicators.ema20, 2)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">EMA(50)</span>
            <span className="font-bold text-cyan-600">
              ${formatNumber(indicators.ema50, 2)}
            </span>
          </div>
          <div className="text-xs mt-2">
            {indicators.ema20 > indicators.ema50 ? (
              <span className="text-green-600 font-medium">● 短期趋势向上</span>
            ) : (
              <span className="text-red-600 font-medium">● 短期趋势向下</span>
            )}
          </div>
        </div>
      </div>

      {/* MACD 指标 */}
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-4">MACD</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">MACD线</span>
            <span className="font-bold text-gray-800">{formatNumber(indicators.macd, 2)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">信号线</span>
            <span className="font-bold text-gray-800">{formatNumber(indicators.signal, 2)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">柱状图</span>
            <span className={`font-bold ${indicators.histogram >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              {formatNumber(indicators.histogram, 2)}
            </span>
          </div>
          <div className="text-xs mt-2">
            <span className={`${macdStatus.color} font-medium`}>● {macdStatus.label}</span>
          </div>
        </div>
      </div>

      {/* RSI 指标 */}
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-4">RSI (相对强弱指标)</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">RSI(7)</span>
            <span className="font-bold text-gray-800">{formatNumber(indicators.rsi7, 2)}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">RSI(14)</span>
            <span className={`font-bold ${rsi14Status.color}`}>
              {formatNumber(indicators.rsi14, 2)}
            </span>
          </div>
          {/* RSI 可视化条 */}
          <div className="mt-3">
            <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`absolute h-full transition-all duration-300 ${
                  indicators.rsi14 >= 70
                    ? 'bg-red-500'
                    : indicators.rsi14 <= 30
                    ? 'bg-green-500'
                    : 'bg-gradient-to-r from-teal-500 to-cyan-500'
                }`}
                style={{ width: `${indicators.rsi14}%` }}
              ></div>
            </div>
            <div className="flex justify-between text-xs text-gray-500 mt-2">
              <span>0</span>
              <span className="text-green-600 font-medium">30</span>
              <span>50</span>
              <span className="text-red-600 font-medium">70</span>
              <span>100</span>
            </div>
          </div>
          <div className="text-xs mt-2">
            <span className={`${rsi14Status.color} font-medium`}>● {rsi14Status.label}</span>
          </div>
        </div>
      </div>

      {/* ATR 指标 */}
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-sm font-medium text-gray-700 mb-4">ATR (平均真实波幅)</h3>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">ATR(3)</span>
            <span className="font-bold text-teal-600">
              ${formatNumber(indicators.atr3, 2)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-gray-600 text-sm">ATR(14)</span>
            <span className="font-bold text-cyan-600">
              ${formatNumber(indicators.atr14, 2)}
            </span>
          </div>
          <div className="text-xs mt-2">
            {indicators.atr3 > indicators.atr14 ? (
              <span className="text-teal-600 font-medium">● 波动性增加</span>
            ) : (
              <span className="text-gray-600 font-medium">● 波动性正常</span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

