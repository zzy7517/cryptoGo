'use client';

/**
 * K线图组件 (Candlestick Chart Component)
 * 
 * 渲染专业级加密货币K线图表，使用 TradingView 的 Lightweight Charts 库
 * 创建时间: 2025-10-27
 * 
 * 文件作用：
 * - 渲染专业级加密货币K线图表
 * - 使用 TradingView 的 Lightweight Charts 库
 * 
 * 主要功能：
 * 1. 蜡烛图展示 - 显示开盘价、最高价、最低价、收盘价
 * 2. 成交量柱状图 - 独立缩放的成交量展示
 * 3. 实时数据更新 - 根据 props 变化自动更新图表
 * 4. 响应式设计 - 监听窗口大小变化，自动调整图表尺寸
 * 5. 交互功能 - 十字准线、缩放、拖动
 * 
 * Props：
 * - data: KlineData[] - K线数据数组
 * - symbol: string - 交易对符号（用于显示标题）
 * 
 * 技术实现：
 * - 使用 useRef 管理图表实例，避免重复创建
 * - 使用 useEffect 处理图表初始化和清理
 * - 数据格式转换：将时间戳转换为秒级，适配图表库
 * - 成交量颜色：涨绿（#26a69a）跌红（#ef5350）
 * 
 * 样式配置：
 * - 暗色主题 (#1a1a1a 背景)
 * - 自定义网格线颜色
 * - 时间轴显示时间但不显示秒
 * 
 * 使用示例：
 * <CandlestickChart data={klineData} symbol="BTC/USDT" />
 */
import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, CandlestickSeries, HistogramSeries } from 'lightweight-charts';
import type { KlineData } from '@/types/market';

interface CandlestickChartProps {
  data: KlineData[];
  symbol: string;
}

export default function CandlestickChart({ data, symbol }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const candlestickSeriesRef = useRef<any>(null);
  const volumeSeriesRef = useRef<any>(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 创建图表
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 500,
      layout: {
        background: { type: ColorType.Solid, color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2a2a2a' },
        horzLines: { color: '#2a2a2a' },
      },
      crosshair: {
        mode: 1,
      },
      rightPriceScale: {
        borderColor: '#2a2a2a',
      },
      timeScale: {
        borderColor: '#2a2a2a',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    chartRef.current = chart;

    // 创建蜡烛图序列
    const candlestickSeries = chart.addSeries(CandlestickSeries, {
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderVisible: false,
      wickUpColor: '#26a69a',
      wickDownColor: '#ef5350',
    });

    candlestickSeriesRef.current = candlestickSeries;

    // 创建成交量柱状图序列
    const volumeSeries = chart.addSeries(HistogramSeries, {
      color: '#26a69a',
      priceFormat: {
        type: 'volume',
      },
      priceScaleId: '',
    });

    volumeSeriesRef.current = volumeSeries;

    // 成交量独立缩放
    chart.priceScale('').applyOptions({
      scaleMargins: {
        top: 0.8,
        bottom: 0,
      },
    });

    // 响应式调整
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chartRef.current.applyOptions({
          width: chartContainerRef.current.clientWidth,
        });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // 更新数据
  useEffect(() => {
    if (!candlestickSeriesRef.current || !volumeSeriesRef.current || data.length === 0) return;

    // 转换数据格式
    const candlestickData = data.map((kline) => ({
      time: Math.floor(kline.timestamp / 1000),
      open: kline.open,
      high: kline.high,
      low: kline.low,
      close: kline.close,
    }));

    const volumeData = data.map((kline) => ({
      time: Math.floor(kline.timestamp / 1000),
      value: kline.volume,
      color: kline.close >= kline.open ? '#26a69a80' : '#ef535080',
    }));

    // 设置数据
    candlestickSeriesRef.current.setData(candlestickData);
    volumeSeriesRef.current.setData(volumeData);

    // 自动调整可见范围
    if (chartRef.current) {
      chartRef.current.timeScale().fitContent();
    }
  }, [data]);

  return (
    <div className="w-full">
      <div className="mb-2 px-2">
        <h3 className="text-lg font-semibold text-gray-200">{symbol}</h3>
      </div>
      <div ref={chartContainerRef} className="w-full rounded-lg overflow-hidden" />
    </div>
  );
}

