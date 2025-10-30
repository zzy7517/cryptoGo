/**
 * Market View Component
 * 市场行情组件 - 显示K线图和所有市场数据
 * 创建时间: 2025-10-29
 */
'use client';

import React from 'react';
import CandlestickChart from './CandlestickChart';
import TechnicalIndicators from './TechnicalIndicators';
import ContractData from './ContractData';
import type { KlineData, TickerData } from '@/types/market';

interface MarketViewProps {
  // K线数据
  klineData: KlineData[];
  currentSymbol: string;
  
  // 实时价格数据
  tickerData: TickerData | null;
  priceAnimation: 'up' | 'down' | null;
  
  // 技术指标
  indicators: any;
  indicatorsLoading: boolean;
  
  // 合约数据
  fundingRate: any;
  openInterest: any;
  fundingLoading: boolean;
  openInterestLoading: boolean;
}

export default function MarketView({
  klineData,
  currentSymbol,
  tickerData,
  priceAnimation,
  indicators,
  indicatorsLoading,
  fundingRate,
  openInterest,
  fundingLoading,
  openInterestLoading,
}: MarketViewProps) {
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
    <div className="grid grid-cols-1 xl:grid-cols-4 gap-6">
      {/* K线图 - 占3列 */}
      <div className="xl:col-span-3 bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <CandlestickChart data={klineData} symbol={currentSymbol} />
      </div>

      {/* 右侧信息面板 - 占1列 */}
      <div className="space-y-6 max-h-[calc(100vh-200px)] overflow-y-auto custom-scrollbar">
        {/* 实时价格 */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-600 mb-3">实时价格</h3>
          <div
            className={`text-4xl font-bold mb-2 transition-colors duration-300 ${
              priceAnimation === 'up'
                ? 'text-green-500'
                : priceAnimation === 'down'
                ? 'text-red-500'
                : 'text-gray-800'
            }`}
          >
            ${formatNumber(tickerData?.last, 2)}
          </div>
          {tickerData && tickerData.percentage !== null && (
            <div
              className={`text-lg font-semibold ${
                tickerData.percentage >= 0 ? 'text-green-500' : 'text-red-500'
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
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-600 mb-4">24小时统计</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">最高价</span>
              <span className="font-bold text-green-500">
                ${formatNumber(tickerData?.high)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">最低价</span>
              <span className="font-bold text-red-500">
                ${formatNumber(tickerData?.low)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">成交量</span>
              <span className="font-bold text-gray-800">{formatVolume(tickerData?.volume)}</span>
            </div>
          </div>
        </div>

        {/* 买卖价 */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-600 mb-4">订单簿</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">买一价</span>
              <span className="font-bold text-green-500">
                ${formatNumber(tickerData?.bid)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">卖一价</span>
              <span className="font-bold text-red-500">
                ${formatNumber(tickerData?.ask)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-600">价差</span>
              <span className="font-bold text-gray-800">
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

        {/* 技术指标 */}
        <TechnicalIndicators
          indicators={indicators?.latest_values || null}
          loading={indicatorsLoading}
        />

        {/* 合约数据 */}
        <ContractData
          fundingRate={fundingRate || null}
          openInterest={openInterest || null}
          loading={fundingLoading || openInterestLoading}
        />
      </div>

      {/* 自定义滚动条样式 */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f3f4f6;
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: linear-gradient(180deg, #14b8a6, #06b6d4);
          border-radius: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: linear-gradient(180deg, #0d9488, #0891b2);
        }
      `}</style>
    </div>
  );
}

