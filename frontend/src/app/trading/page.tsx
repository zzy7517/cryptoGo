'use client';

/**
 * 交易页面
 */
import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import CandlestickChart from '@/components/CandlestickChart';
import { useMarketStore } from '@/stores/marketStore';
import { marketApi } from '@/lib/api';
import type { TimeInterval } from '@/types/market';

const INTERVALS: { value: TimeInterval; label: string }[] = [
  { value: '1m', label: '1分钟' },
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '1h', label: '1小时' },
  { value: '4h', label: '4小时' },
  { value: '1d', label: '1天' },
];

export default function TradingPage() {
  const {
    currentSymbol,
    currentInterval,
    klineData,
    tickerData,
    previousPrice,
    setCurrentSymbol,
    setCurrentInterval,
    setKlineData,
    setTickerData,
  } = useMarketStore();

  const [priceAnimation, setPriceAnimation] = useState<'up' | 'down' | null>(null);

  // 获取K线数据
  const { data: klineResponse, refetch: refetchKlines } = useQuery({
    queryKey: ['klines', currentSymbol, currentInterval],
    queryFn: () => marketApi.getKlines(currentSymbol, currentInterval, 100),
    refetchInterval: 30000, // 30秒自动刷新
  });

  // 获取实时价格
  const { data: ticker, refetch: refetchTicker } = useQuery({
    queryKey: ['ticker', currentSymbol],
    queryFn: () => marketApi.getTicker(currentSymbol),
    refetchInterval: 5000, // 5秒自动刷新
  });

  // 更新K线数据
  useEffect(() => {
    if (klineResponse?.data) {
      setKlineData(klineResponse.data);
    }
  }, [klineResponse, setKlineData]);

  // 更新实时价格
  useEffect(() => {
    if (ticker) {
      setTickerData(ticker);
    }
  }, [ticker, setTickerData]);

  // 价格变化动画
  useEffect(() => {
    if (tickerData && previousPrice !== null) {
      if (tickerData.last > previousPrice) {
        setPriceAnimation('up');
      } else if (tickerData.last < previousPrice) {
        setPriceAnimation('down');
      }
      
      const timer = setTimeout(() => setPriceAnimation(null), 500);
      return () => clearTimeout(timer);
    }
  }, [tickerData, previousPrice]);

  const handleSymbolChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setCurrentSymbol(e.target.value);
  };

  const handleIntervalChange = (interval: TimeInterval) => {
    setCurrentInterval(interval);
  };

  const formatNumber = (num: number | null | undefined, decimals: number = 2): string => {
    if (num === null || num === undefined) return '--';
    return num.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatVolume = (num: number | null | undefined): string => {
    if (num === null || num === undefined) return '--';
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(2);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4">
      <div className="max-w-[1920px] mx-auto">
        {/* 顶部标题栏 */}
        <div className="mb-4">
          <h1 className="text-3xl font-bold mb-2">CryptoGo 交易终端</h1>
          <p className="text-gray-400">实时加密货币交易数据</p>
        </div>

        {/* 控制面板 */}
        <div className="bg-gray-900 rounded-lg p-4 mb-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* 交易对选择 */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">交易对</label>
              <input
                type="text"
                value={currentSymbol}
                onChange={handleSymbolChange}
                className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                placeholder="BTC/USDT"
              />
            </div>

            {/* 时间周期选择 */}
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">时间周期</label>
              <div className="flex gap-2">
                {INTERVALS.map((interval) => (
                  <button
                    key={interval.value}
                    onClick={() => handleIntervalChange(interval.value)}
                    className={`px-4 py-2 rounded transition-colors ${
                      currentInterval === interval.value
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {interval.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 主要内容区域 */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
          {/* K线图 - 占3列 */}
          <div className="xl:col-span-3 bg-gray-900 rounded-lg p-4">
            <CandlestickChart data={klineData} symbol={currentSymbol} />
          </div>

          {/* 右侧信息面板 - 占1列 */}
          <div className="space-y-4">
            {/* 实时价格 */}
            <div className="bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-3">实时价格</h3>
              <div
                className={`text-4xl font-bold mb-2 transition-colors duration-300 ${
                  priceAnimation === 'up'
                    ? 'text-green-400'
                    : priceAnimation === 'down'
                    ? 'text-red-400'
                    : 'text-white'
                }`}
              >
                ${formatNumber(tickerData?.last, 2)}
              </div>
              {tickerData && tickerData.percentage !== null && (
                <div
                  className={`text-lg font-semibold ${
                    tickerData.percentage >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {tickerData.percentage >= 0 ? '+' : ''}
                  {formatNumber(tickerData.percentage, 2)}%
                  <span className="text-sm ml-2">
                    ({tickerData.change && tickerData.change >= 0 ? '+' : ''}
                    {formatNumber(tickerData.change, 2)})
                  </span>
                </div>
              )}
            </div>

            {/* 24小时统计 */}
            <div className="bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-3">24小时统计</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">最高价</span>
                  <span className="font-semibold text-green-400">
                    ${formatNumber(tickerData?.high)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">最低价</span>
                  <span className="font-semibold text-red-400">
                    ${formatNumber(tickerData?.low)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">成交量</span>
                  <span className="font-semibold">{formatVolume(tickerData?.volume)}</span>
                </div>
              </div>
            </div>

            {/* 买卖价 */}
            <div className="bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-3">订单簿</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">买一价</span>
                  <span className="font-semibold text-green-400">
                    ${formatNumber(tickerData?.bid)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">卖一价</span>
                  <span className="font-semibold text-red-400">
                    ${formatNumber(tickerData?.ask)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">价差</span>
                  <span className="font-semibold">
                    ${formatNumber(
                      tickerData?.ask && tickerData?.bid
                        ? tickerData.ask - tickerData.bid
                        : 0,
                      2
                    )}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

