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
  Area,
  AreaChart,
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
        <div className="bg-gray-900/95 backdrop-blur-sm p-4 border border-gray-700 rounded-lg shadow-2xl">
          <p className="text-xs text-gray-400 mb-3 font-medium">
            {new Date(data.fullTime).toLocaleString('zh-CN')}
          </p>
          <div className="space-y-2">
            <p className="text-sm font-bold text-blue-400 flex justify-between gap-4">
              <span>总资产</span>
              <span>${data.总资产.toFixed(2)}</span>
            </p>
            <p className="text-sm text-purple-400 flex justify-between gap-4">
              <span>账户余额</span>
              <span>${data.账户余额.toFixed(2)}</span>
            </p>
            <p className={`text-sm font-semibold flex justify-between gap-4 ${
              data.浮动盈亏 >= 0 ? 'text-green-400' : 'text-red-400'
            }`}>
              <span>浮动盈亏</span>
              <span>{data.浮动盈亏 >= 0 ? '+' : ''}${data.浮动盈亏.toFixed(2)}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 border border-gray-200 shadow-lg">
      {/* 标题和控制区域 */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-xl font-bold text-gray-900 tracking-tight">资产变化趋势</h3>
          <p className="text-sm text-gray-600 mt-1">
            从会话开始到现在的完整资产变化
            {metadata && (
              <span className="ml-2 text-xs text-blue-600 font-medium">
                ({metadata.sampled_records}/{metadata.total_records} 数据点)
              </span>
            )}
          </p>
        </div>

        {/* 采样间隔选择器 */}
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 font-medium">采样间隔:</label>
          <select
            value={sampleInterval}
            onChange={(e) => setSampleInterval(Number(e.target.value))}
            className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent shadow-sm"
          >
            <option value={1}>1分钟</option>
            <option value={5}>5分钟</option>
            <option value={10}>10分钟</option>
            <option value={30}>30分钟</option>
            <option value={60}>60分钟</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl p-4 shadow-sm">
        <ResponsiveContainer width="100%" height={450}>
          <LineChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 20, bottom: 10 }}
          >
            <defs>
              <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
              </linearGradient>
              <linearGradient id="colorPnl" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#e5e7eb"
              strokeOpacity={0.5}
              vertical={false}
            />
            <XAxis
              dataKey="time"
              stroke="#9ca3af"
              style={{ fontSize: '11px', fontWeight: 500 }}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <YAxis
              stroke="#9ca3af"
              style={{ fontSize: '11px', fontWeight: 500 }}
              tickFormatter={(value) => `$${value.toFixed(0)}`}
              tickLine={false}
              axisLine={{ stroke: '#e5e7eb' }}
            />
            <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#9ca3af', strokeWidth: 1, strokeDasharray: '5 5' }} />
            <Legend
              wrapperStyle={{ fontSize: '13px', paddingTop: '24px', fontWeight: 500 }}
              iconType="circle"
            />
            <Line
              type="monotone"
              dataKey="总资产"
              stroke="#3b82f6"
              strokeWidth={2.5}
              dot={false}
              activeDot={{ r: 5, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }}
              fill="url(#colorTotal)"
            />
            <Line
              type="monotone"
              dataKey="账户余额"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#8b5cf6', strokeWidth: 2, stroke: '#fff' }}
              strokeDasharray="5 5"
            />
            <Line
              type="monotone"
              dataKey="浮动盈亏"
              stroke="#10b981"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#10b981', strokeWidth: 2, stroke: '#fff' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* 数据统计 */}
      <div className="mt-6 grid grid-cols-3 gap-4">
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 text-center hover:shadow-md transition-shadow">
          <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">当前总资产</div>
          <div className="text-2xl font-bold text-blue-600">
            ${chartData[chartData.length - 1]?.总资产.toFixed(2) || '0.00'}
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 text-center hover:shadow-md transition-shadow">
          <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">当前余额</div>
          <div className="text-2xl font-bold text-purple-600">
            ${chartData[chartData.length - 1]?.账户余额.toFixed(2) || '0.00'}
          </div>
        </div>
        <div className="bg-white rounded-lg p-4 shadow-sm border border-gray-200 text-center hover:shadow-md transition-shadow">
          <div className="text-xs text-gray-500 uppercase tracking-wide font-semibold mb-2">浮动盈亏</div>
          <div className={`text-2xl font-bold ${
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

