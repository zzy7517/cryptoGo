/**
 * Asset Chart Component
 * 资产变化时序图表组件
 * 创建时间: 2025-11-03
 * 更新时间: 2025-11-04 (移除采样逻辑，全量展示数据)
 */
'use client';

import React from 'react';
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
  // 获取资产时序数据（全量）
  const { data: timelineResponse, isLoading, error } = useQuery({
    queryKey: ['assetTimeline', sessionId],
    queryFn: () => sessionApi.getAssetTimeline(sessionId),
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
            <p className="text-lg font-bold text-blue-400 flex justify-between gap-4">
              <span>总资产</span>
              <span>${data.总资产.toFixed(2)}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl p-6 border border-gray-200 shadow-lg">
      {/* 标题区域 */}
      <div className="mb-6">
        <h3 className="text-xl font-bold text-gray-900 tracking-tight">资产变化趋势</h3>
        <p className="text-sm text-gray-600 mt-1">
          从会话开始到现在的完整资产变化
          {metadata && (
            <span className="ml-2 text-xs text-blue-600 font-medium">
              ({metadata.total_records} 个决策点)
            </span>
          )}
        </p>
      </div>

      <div className="bg-white rounded-xl p-4 shadow-sm">
        <ResponsiveContainer width="100%" height={450}>
          <LineChart
            data={chartData}
            margin={{ top: 10, right: 30, left: 20, bottom: 10 }}
          >
            <defs>
              <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
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
              strokeWidth={3}
              dot={false}
              activeDot={{ r: 6, fill: '#3b82f6', strokeWidth: 2, stroke: '#fff' }}
              fill="url(#colorTotal)"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

