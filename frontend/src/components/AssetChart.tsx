/**
 * Asset Chart Component (优化版)
 * 资产变化时序图表组件
 * 创建时间: 2025-11-03
 * 更新时间: 2025-11-03 (优化数据采样和展示)
 */
'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { sessionApi } from '@/lib/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

interface AssetChartProps {
  sessionId: number;
}

export default function AssetChart({ sessionId }: AssetChartProps) {
  // 采样间隔（分钟）
  const [sampleInterval, setSampleInterval] = useState(5);

  // 获取资产时序数据
  const { data: timelineResponse, isLoading, error } = useQuery({
    queryKey: ['assetTimeline', sessionId, sampleInterval],
    queryFn: () => sessionApi.getAssetTimeline(sessionId, sampleInterval),
    refetchInterval: 30000, // 每30秒刷新一次
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载资产数据中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-red-500">加载资产数据失败</div>
      </div>
    );
  }

  const timeline = timelineResponse?.data || [];
  const metadata = timelineResponse?.metadata;

  if (timeline.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">暂无资产变化数据</div>
      </div>
    );
  }

  // 格式化时间显示
  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  // 格式化数据用于图表展示
  const chartData = timeline.map((item: any) => ({
    time: formatTime(item.timestamp),
    fullTime: item.timestamp,
    总资产: item.total_asset,
    账户余额: item.account_balance,
    浮动盈亏: item.unrealized_pnl,
  }));

  // 自定义Tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded shadow-lg">
          <p className="text-xs text-gray-600 mb-2">
            {new Date(data.fullTime).toLocaleString('zh-CN')}
          </p>
          <div className="space-y-1">
            <p className="text-sm font-bold text-blue-600">
              总资产: ${data.总资产.toFixed(2)}
            </p>
            <p className="text-sm text-gray-700">
              账户余额: ${data.账户余额.toFixed(2)}
            </p>
            <p className={`text-sm font-semibold ${
              data.浮动盈亏 >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              浮动盈亏: {data.浮动盈亏 >= 0 ? '+' : ''}${data.浮动盈亏.toFixed(2)}
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg p-6 border border-gray-200">
      {/* 标题和控制区域 */}
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">资产变化趋势</h3>
          <p className="text-sm text-gray-500 mt-1">
            从会话开始到现在的完整资产变化
            {metadata && (
              <span className="ml-2 text-xs text-blue-600">
                ({metadata.sampled_records}/{metadata.total_records} 数据点)
              </span>
            )}
          </p>
        </div>

        {/* 采样间隔选择器 */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">采样间隔:</label>
          <select
            value={sampleInterval}
            onChange={(e) => setSampleInterval(Number(e.target.value))}
            className="px-3 py-1 border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={1}>1分钟</option>
            <option value={5}>5分钟</option>
            <option value={10}>10分钟</option>
            <option value={30}>30分钟</option>
            <option value={60}>60分钟</option>
          </select>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <LineChart
          data={chartData}
          margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis
            dataKey="time"
            stroke="#9ca3af"
            style={{ fontSize: '12px' }}
          />
          <YAxis
            stroke="#9ca3af"
            style={{ fontSize: '12px' }}
            tickFormatter={(value) => `$${value.toFixed(0)}`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '14px', paddingTop: '20px' }}
          />
          <Line
            type="monotone"
            dataKey="总资产"
            stroke="#3b82f6"
            strokeWidth={3}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
          <Line
            type="monotone"
            dataKey="账户余额"
            stroke="#8b5cf6"
            strokeWidth={2}
            dot={{ r: 3 }}
            strokeDasharray="5 5"
          />
          <Line
            type="monotone"
            dataKey="浮动盈亏"
            stroke="#10b981"
            strokeWidth={2}
            dot={{ r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* 数据统计 */}
      <div className="mt-6 grid grid-cols-3 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="text-sm text-gray-600 mb-1">当前总资产</div>
          <div className="text-2xl font-bold text-blue-600">
            ${chartData[chartData.length - 1]?.总资产.toFixed(2) || '0.00'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-600 mb-1">当前余额</div>
          <div className="text-xl font-semibold text-gray-900">
            ${chartData[chartData.length - 1]?.账户余额.toFixed(2) || '0.00'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-sm text-gray-600 mb-1">浮动盈亏</div>
          <div className={`text-xl font-semibold ${
            (chartData[chartData.length - 1]?.浮动盈亏 || 0) >= 0
              ? 'text-green-600'
              : 'text-red-600'
          }`}>
            {(chartData[chartData.length - 1]?.浮动盈亏 || 0) >= 0 ? '+' : ''}
            ${chartData[chartData.length - 1]?.浮动盈亏.toFixed(2) || '0.00'}
          </div>
        </div>
      </div>
    </div>
  );
}

