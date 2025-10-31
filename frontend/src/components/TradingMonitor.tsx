/**
 * Trading Monitor Component
 * 交易监控组件 - 显示Agent状态、持仓、交易历史、盈亏统计
 * 创建时间: 2025-10-29
 */
'use client';

import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { sessionApi, agentApi } from '@/lib/api';
import AgentMonitor from './AgentMonitor';
import ChatPanel from './ChatPanel';

interface TradingMonitorProps {
  sessionId: number;
}

export default function TradingMonitor({ sessionId }: TradingMonitorProps) {
  // 获取会话详情
  const { data: sessionDetails, isLoading, refetch } = useQuery({
    queryKey: ['sessionDetails', sessionId],
    queryFn: () => sessionApi.getSessionDetails(sessionId),
    refetchInterval: 10000, // 每10秒刷新
  });

  const details = sessionDetails?.data;

  const formatNumber = (num: number | null | undefined, decimals: number = 2): string => {
    if (num === null || num === undefined) return '--';
    return num.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatTime = (timestamp: string | null | undefined): string => {
    if (!timestamp) return '--';
    return new Date(timestamp).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载交易数据中...</div>
      </div>
    );
  }

  if (!details) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">无法获取会话数据</div>
      </div>
    );
  }

  const session = details.session;
  const positions = details.positions || [];
  const trades = details.trades || [];
  const decisions = details.decisions || [];

  return (
    <div className="space-y-6">
      {/* Agent 监控卡片 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <AgentMonitor sessionId={sessionId} />
        </div>
        
        {/* 账户概览 */}
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
          <h3 className="text-sm font-medium text-gray-700 mb-4">账户概览</h3>
          <div className="space-y-3">
            <div>
              <div className="text-xs text-gray-500 mb-1">初始资金</div>
              <div className="text-lg font-bold text-gray-800">
                ${formatNumber(session?.initial_capital, 2)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">当前资金</div>
              <div className="text-2xl font-bold text-teal-600">
                ${formatNumber(session?.final_capital || session?.initial_capital, 2)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">盈亏</div>
              <div className={`text-xl font-bold ${
                (session?.total_pnl || 0) >= 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                {(session?.total_pnl || 0) >= 0 ? '+' : ''}
                ${formatNumber(session?.total_pnl, 2)}
              </div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">收益率</div>
              <div className={`text-lg font-bold ${
                (session?.total_return_pct || 0) >= 0 ? 'text-green-500' : 'text-red-500'
              }`}>
                {(session?.total_return_pct || 0) >= 0 ? '+' : ''}
                {formatNumber(session?.total_return_pct, 2)}%
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 持仓信息 */}
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">当前持仓</h3>
        {positions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">交易对</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">方向</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">数量</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">均价</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">当前价</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">盈亏</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">收益率</th>
                </tr>
              </thead>
              <tbody>
                {positions.map((position: any) => {
                  const pnl = position.unrealized_pnl || 0;
                  const pnlPct = position.unrealized_pnl_pct || 0;
                  return (
                    <tr key={position.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                      <td className="py-3 px-4 font-medium text-gray-800">{position.symbol}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-semibold ${
                          position.side === 'long' 
                            ? 'bg-green-100 text-green-700' 
                            : 'bg-red-100 text-red-700'
                        }`}>
                          {position.side === 'long' ? '多' : '空'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right font-mono">{formatNumber(position.quantity, 4)}</td>
                      <td className="py-3 px-4 text-right font-mono">${formatNumber(position.entry_price, 2)}</td>
                      <td className="py-3 px-4 text-right font-mono">${formatNumber(position.current_price, 2)}</td>
                      <td className={`py-3 px-4 text-right font-bold ${pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {pnl >= 0 ? '+' : ''}${formatNumber(pnl, 2)}
                      </td>
                      <td className={`py-3 px-4 text-right font-bold ${pnlPct >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {pnlPct >= 0 ? '+' : ''}{formatNumber(pnlPct, 2)}%
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            暂无持仓
          </div>
        )}
      </div>

      {/* 交易历史 */}
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">交易历史</h3>
        {trades.length > 0 ? (
          <div className="overflow-x-auto max-h-96 overflow-y-auto custom-scrollbar">
            <table className="w-full">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-gray-200">
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">时间</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">交易对</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">方向</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">数量</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">价格</th>
                  <th className="text-right py-3 px-4 text-sm font-semibold text-gray-700">总额</th>
                  <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700">状态</th>
                </tr>
              </thead>
              <tbody>
                {trades.slice(0, 50).map((trade: any) => (
                  <tr key={trade.id} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                    <td className="py-3 px-4 text-xs text-gray-600">
                      {formatTime(trade.created_at)}
                    </td>
                    <td className="py-3 px-4 font-medium text-gray-800">{trade.symbol}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-semibold ${
                        trade.side === 'buy' 
                          ? 'bg-green-100 text-green-700' 
                          : 'bg-red-100 text-red-700'
                      }`}>
                        {trade.side === 'buy' ? '买入' : '卖出'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right font-mono text-sm">{formatNumber(trade.quantity, 4)}</td>
                    <td className="py-3 px-4 text-right font-mono text-sm">${formatNumber(trade.price, 2)}</td>
                    <td className="py-3 px-4 text-right font-mono text-sm font-semibold">
                      ${formatNumber(trade.quantity * trade.price, 2)}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${
                        trade.status === 'filled' 
                          ? 'bg-blue-100 text-blue-700' 
                          : trade.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-700'
                          : 'bg-gray-100 text-gray-700'
                      }`}>
                        {trade.status === 'filled' ? '已成交' : trade.status === 'pending' ? '待成交' : trade.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-400">
            暂无交易记录
          </div>
        )}
      </div>

      {/* AI 聊天记录 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 h-[600px]">
        <ChatPanel sessionId={sessionId} />
      </div>

      {/* 自定义滚动条样式 */}
      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
          height: 8px;
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

