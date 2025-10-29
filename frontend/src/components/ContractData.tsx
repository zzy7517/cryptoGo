'use client';

/**
 * 合约数据展示组件 (Contract Data Component)
 * 
 * 展示永续合约特有的市场数据，帮助交易者了解市场情绪和资金流向
 * 创建时间: 2025-10-27
 * 
 * 文件作用：
 * - 展示永续合约特有的市场数据
 * - 帮助交易者了解市场情绪和资金流向
 * 
 * 展示的数据：
 * 1. 资金费率 (Funding Rate)
 *    - 当前费率百分比
 *    - 下次结算时间
 *    - 费率状态判断（多头费用高/空头费用高/正常）
 *    - 解释：正费率=多头支付空头，负费率=空头支付多头
 * 
 * 2. 持仓量 (Open Interest)
 *    - 总持仓量（合约张数或金额）
 *    - 反映市场参与度和资金规模
 *    - 解释：持仓量上升通常表示资金流入
 * 
 * Props：
 * - fundingRate: FundingRateData | null - 资金费率数据
 * - openInterest: OpenInterestData | null - 持仓量数据
 * - loading?: boolean - 加载状态
 * 
 * 特殊处理：
 * - 现货市场没有资金费率和持仓量，显示提示信息
 * - 永续合约才会显示这些数据
 * 
 * 数据解读：
 * - 资金费率 > 0.05%：多头情绪强烈
 * - 资金费率 < -0.05%：空头情绪强烈
 * - 持仓量增加：资金流入，市场活跃度提升
 * 
 * 使用示例：
 * <ContractData fundingRate={rate} openInterest={oi} loading={false} />
 */
import React from 'react';
import type { FundingRateData, OpenInterestData } from '@/types/market';

interface ContractDataProps {
  fundingRate: FundingRateData | null;
  openInterest: OpenInterestData | null;
  loading?: boolean;
}

export default function ContractData({ fundingRate, openInterest, loading }: ContractDataProps) {
  const formatNumber = (num: number | null | undefined, decimals: number = 2): string => {
    if (num === null || num === undefined) return '--';
    return num.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatVolume = (num: number | null | undefined): string => {
    if (num === null || num === undefined) return '--';
    if (num >= 1000000000) return `${(num / 1000000000).toFixed(2)}B`;
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(2);
  };

  const formatPercentage = (rate: number | null | undefined): string => {
    if (rate === null || rate === undefined) return '--';
    return `${(rate * 100).toFixed(4)}%`;
  };

  const formatTime = (timestamp: number | null | undefined): string => {
    if (!timestamp) return '--';
    const date = new Date(timestamp);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  };

  if (loading) {
    return (
      <div className="space-y-4">
        <div className="bg-gray-900 rounded-lg p-4 animate-pulse">
          <div className="h-4 bg-gray-800 rounded w-1/2 mb-4"></div>
          <div className="space-y-2">
            <div className="h-3 bg-gray-800 rounded"></div>
            <div className="h-3 bg-gray-800 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // 判断资金费率状态
  const getFundingRateStatus = (rate: number | null): { color: string; label: string } => {
    if (rate === null) return { color: 'text-gray-400', label: '无数据' };
    if (rate > 0.0005) return { color: 'text-red-400', label: '多头费用高' };
    if (rate < -0.0005) return { color: 'text-green-400', label: '空头费用高' };
    return { color: 'text-gray-300', label: '费率正常' };
  };

  const fundingStatus = getFundingRateStatus(fundingRate?.funding_rate || null);

  return (
    <div className="space-y-4">
      {/* 资金费率 */}
      <div className="bg-gray-900 rounded-lg p-4">
        <h3 className="text-sm text-gray-400 mb-3 font-semibold">资金费率</h3>
        {fundingRate?.funding_rate !== null ? (
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">当前费率</span>
              <span
                className={`font-semibold text-lg ${
                  (fundingRate?.funding_rate || 0) >= 0 ? 'text-red-400' : 'text-green-400'
                }`}
              >
                {formatPercentage(fundingRate?.funding_rate)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">下次结算</span>
              <span className="font-semibold">{formatTime(fundingRate?.next_funding_time)}</span>
            </div>
            <div className="text-xs mt-2">
              <span className={fundingStatus.color}>● {fundingStatus.label}</span>
            </div>
            <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-800">
              <p>资金费率为正时，多头支付空头</p>
              <p>资金费率为负时，空头支付多头</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-gray-500 text-sm">现货市场无资金费率</p>
          </div>
        )}
      </div>

      {/* 持仓量 */}
      <div className="bg-gray-900 rounded-lg p-4">
        <h3 className="text-sm text-gray-400 mb-3 font-semibold">持仓量</h3>
        {openInterest?.open_interest !== null ? (
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-400 text-sm">总持仓量</span>
              <span className="font-semibold text-lg text-blue-400">
                {formatVolume(openInterest?.open_interest)}
              </span>
            </div>
            <div className="text-xs text-gray-500 mt-2 pt-2 border-t border-gray-800">
              <p>持仓量反映市场参与度</p>
              <p>持仓量上升通常表示资金流入</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-gray-500 text-sm">现货市场无持仓量数据</p>
          </div>
        )}
      </div>
    </div>
  );
}

