/**
 * Trading Monitor Component
 * 交易监控组件 - 显示Agent状态、持仓、交易历史、盈亏统计
 * 创建时间: 2025-10-29
 */
'use client';

import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { sessionApi, agentApi, accountApi } from '@/lib/api';
import AgentMonitor from './AgentMonitor';
import ChatPanel from './ChatPanel';
import AssetChart from './AssetChart';

interface TradingMonitorProps {
  sessionId: number;
}

export default function TradingMonitor({ sessionId }: TradingMonitorProps) {
  // 聊天面板显示/隐藏状态
  const [isChatPanelVisible, setIsChatPanelVisible] = useState(true);

  // 获取会话详情
  const { data: sessionDetails, isLoading, refetch } = useQuery({
    queryKey: ['sessionDetails', sessionId],
    queryFn: () => sessionApi.getSessionDetails(sessionId),
    refetchInterval: 10000, // 每10秒刷新
  });

  // 获取账户信息
  const { data: accountData } = useQuery({
    queryKey: ['accountSummary'],
    queryFn: () => accountApi.getAccountSummary(),
    refetchInterval: 15000, // 每15秒刷新
  });

  // 获取 Agent 状态
  const { data: agentStatusData } = useQuery({
    queryKey: ['agentStatus', sessionId],
    queryFn: () => agentApi.getAgentStatus(sessionId),
    refetchInterval: 5000, // 每5秒刷新
    retry: false, // Agent 未运行时不重试
  });

  const details = sessionDetails?.data;
  const exchangeData = accountData?.data;
  const holdTimes = details?.hold_times;
  const agentStatus = agentStatusData?.data;

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
    <div className="flex gap-6 h-[calc(100vh-200px)]">
      {/* 左侧主内容区 */}
      <div className="flex-1 space-y-4 overflow-y-auto pr-2">
        {/* Agent 状态通知栏 */}
        {agentStatus && (
          <div className="bg-gradient-to-r from-teal-50 to-cyan-50 border border-teal-200 rounded-lg px-4 py-2.5 flex items-center justify-between text-sm">
            <div className="flex items-center gap-6">
              {/* 运行状态 */}
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${
                  agentStatus.status === 'running' ? 'bg-green-500 animate-pulse' :
                  agentStatus.status === 'stopping' ? 'bg-yellow-500' :
                  agentStatus.status === 'starting' ? 'bg-blue-500 animate-pulse' :
                  'bg-gray-500'
                }`}></div>
                <span className="font-semibold text-gray-800">
                  {agentStatus.status === 'running' ? '运行中' :
                   agentStatus.status === 'stopping' ? '停止中' :
                   agentStatus.status === 'starting' ? '启动中' :
                   agentStatus.status === 'crashed' ? '已崩溃' :
                   agentStatus.status}
                </span>
              </div>

              {/* 循环次数 */}
              <div className="flex items-center gap-1.5 text-gray-700">
                <span className="text-gray-600">循环:</span>
                <span className="font-bold">{agentStatus.run_count || 0}</span>
              </div>

              {/* 决策间隔 */}
              {agentStatus.config?.decision_interval && (
                <div className="flex items-center gap-1.5 text-gray-700">
                  <span className="text-gray-600">间隔:</span>
                  <span className="font-bold">{agentStatus.config.decision_interval}秒</span>
                </div>
              )}

              {/* 监控币种 */}
              {agentStatus.config?.symbols && agentStatus.config.symbols.length > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-gray-600">监控:</span>
                  <div className="flex gap-1.5">
                    {agentStatus.config.symbols.slice(0, 3).map((symbol: string) => (
                      <span key={symbol} className="text-xs bg-teal-100 text-teal-700 px-2 py-0.5 rounded font-medium">
                        {symbol}
                      </span>
                    ))}
                    {agentStatus.config.symbols.length > 3 && (
                      <span className="text-xs text-gray-500">+{agentStatus.config.symbols.length - 3}</span>
                    )}
                  </div>
                </div>
              )}

              {/* 最后运行时间 */}
              {agentStatus.last_run_time && (
                <div className="flex items-center gap-1.5 text-gray-700">
                  <span className="text-gray-600">最后运行:</span>
                  <span className="text-xs font-medium">
                    {new Date(agentStatus.last_run_time).toLocaleTimeString('zh-CN')}
                  </span>
                </div>
              )}
            </div>

            {/* 错误提示 */}
            {agentStatus.last_error && (
              <div className="text-xs text-red-600 font-medium max-w-md truncate" title={agentStatus.last_error}>
                ⚠️ {agentStatus.last_error}
              </div>
            )}
          </div>
        )}

        {/* 账户总览 - 参考 Alpha Arena 风格 */}
        <div className="grid grid-cols-3 gap-4">
          {/* 可用资金 */}
          <div className="bg-white rounded-lg p-5 border border-gray-200">
            <div className="text-sm text-gray-600 mb-2">Available Cash:</div>
            <div className="text-3xl font-bold text-gray-900">
              ${formatNumber(exchangeData?.account?.availableBalance || session?.final_capital || session?.initial_capital, 2)}
            </div>
          </div>

          {/* 总盈亏 */}
          <div className="bg-white rounded-lg p-5 border border-gray-200">
            <div className="flex justify-between items-start mb-2">
              <div className="text-sm text-gray-600">Total P&L:</div>
              <div className="text-sm text-gray-600">Unrealized:</div>
            </div>
            <div className="flex justify-between items-center">
              <div className={`text-3xl font-bold ${
                ((session?.total_pnl || 0) + (exchangeData?.account?.totalUnrealizedProfit || 0)) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {((session?.total_pnl || 0) + (exchangeData?.account?.totalUnrealizedProfit || 0)) >= 0 ? '+' : ''}${formatNumber((session?.total_pnl || 0) + (exchangeData?.account?.totalUnrealizedProfit || 0), 2)}
              </div>
              <div className={`text-2xl font-bold ${
                (exchangeData?.account?.totalUnrealizedProfit || 0) >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {(exchangeData?.account?.totalUnrealizedProfit || 0) >= 0 ? '+' : ''}${formatNumber(exchangeData?.account?.totalUnrealizedProfit, 2)}
              </div>
            </div>
            <div className="mt-2 pt-2 border-t border-gray-100">
              <div className="flex justify-between items-center text-sm">
                <span className="text-gray-600">Realized:</span>
                <span className={`font-semibold ${
                  (session?.total_pnl || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(session?.total_pnl || 0) >= 0 ? '+' : ''}${formatNumber(session?.total_pnl, 2)}
                </span>
              </div>
            </div>
          </div>

          {/* 统计信息 */}
          <div className="bg-white rounded-lg p-5 border border-gray-200">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="text-sm text-gray-600 mb-1">Total Fees:</div>
                <div className="text-xl font-semibold text-gray-900">$0.00</div>
              </div>
              <div>
                <div className="text-sm text-gray-600 mb-1">Return:</div>
                <div className={`text-xl font-semibold ${
                  (session?.total_return_pct || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(session?.total_return_pct || 0) >= 0 ? '+' : ''}{formatNumber(session?.total_return_pct, 2)}%
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 资产变化趋势图 - 全宽显示 */}
        <div>
          <AssetChart sessionId={sessionId} />
        </div>

        {/* 实时持仓 - Active Positions */}
        {exchangeData?.positions && exchangeData.positions.length > 0 && (
          <div className="bg-white rounded-lg border border-gray-200">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
                ACTIVE POSITIONS
              </h3>
              <span className="text-sm text-gray-600">
                Total Unrealized P&L: <span className={`font-bold ${
                  (exchangeData.account?.totalUnrealizedProfit || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {(exchangeData.account?.totalUnrealizedProfit || 0) >= 0 ? '+' : ''}
                  ${formatNumber(exchangeData.account?.totalUnrealizedProfit, 2)}
                </span>
              </span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="text-left py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Coin</th>
                    <th className="text-left py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Side</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Entry Price</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Mark Price</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Quantity</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Leverage</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Margin</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Unrealized P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {exchangeData.positions.map((position: any, index: number) => {
                    const pnl = position.unrealizedProfit || 0;
                    return (
                      <tr key={index} className="border-b border-gray-100 hover:bg-gray-50/50 transition-colors">
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-orange-100 rounded-full flex items-center justify-center text-xs font-bold text-orange-600">
                              {position.symbol.split('/')[0][0]}
                            </div>
                            <span className="font-semibold text-gray-900">{position.symbol.split('/')[0]}</span>
                          </div>
                        </td>
                        <td className="py-4 px-6">
                          <span className={`text-sm font-bold uppercase ${
                            position.side === 'long' ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {position.side}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          ${formatNumber(position.entryPrice, 2)}
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          ${formatNumber(position.markPrice, 2)}
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          {formatNumber(position.quantity, 4)}
                        </td>
                        <td className="py-4 px-6 text-right">
                          <span className="text-sm font-semibold text-gray-900">{position.leverage}X</span>
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          ${formatNumber((position.entryPrice * position.quantity) / position.leverage, 2)}
                        </td>
                        <td className={`py-4 px-6 text-right font-bold text-sm ${
                          pnl >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {pnl >= 0 ? '+' : ''}${formatNumber(pnl, 2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 交易统计和持仓时间 */}
        <div className="grid grid-cols-2 gap-4">
          {/* 交易统计 */}
          <div className="bg-white rounded-lg p-5 border border-gray-200">
            <div className="grid grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-gray-600 mb-1">Confidence:</div>
                <div className="font-bold text-gray-900">--</div>
              </div>
              <div>
                <div className="text-gray-600 mb-1">Biggest Win:</div>
                <div className="font-bold text-green-600">$0</div>
              </div>
              <div>
                <div className="text-gray-600 mb-1">Biggest Loss:</div>
                <div className="font-bold text-red-600">$0</div>
              </div>
              <div>
                <div className="text-gray-600 mb-1">Trades:</div>
                <div className="font-bold text-gray-900">{trades.length}</div>
              </div>
            </div>
          </div>

          {/* 持仓时间分布 */}
          <div className="bg-white rounded-lg p-5 border border-gray-200">
            <div className="text-sm font-semibold text-gray-900 mb-3">HOLD TIMES</div>
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">Long:</span>
                <span className="font-bold text-green-600">
                  {holdTimes?.long_pct !== undefined ? `${holdTimes.long_pct}%` : '--'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Short:</span>
                <span className="font-bold text-red-600">
                  {holdTimes?.short_pct !== undefined ? `${holdTimes.short_pct}%` : '--'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Flat:</span>
                <span className="font-bold text-gray-900">
                  {holdTimes?.flat_pct !== undefined ? `${holdTimes.flat_pct}%` : '--'}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 交易历史 - Last Trades */}
        <div className="bg-white rounded-lg border border-gray-200">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wide">
              LAST {Math.min(trades.length, 25)} TRADES
            </h3>
          </div>
          {trades.length > 0 ? (
            <div className="overflow-x-auto max-h-[500px] overflow-y-auto custom-scrollbar">
              <table className="w-full">
                <thead className="sticky top-0 bg-gray-50 border-b border-gray-200">
                  <tr>
                    <th className="text-left py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Side</th>
                    <th className="text-left py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Coin</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Entry Price</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Exit Price</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Quantity</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Holding Time</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Notional Entry</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Notional Exit</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Total Fees</th>
                    <th className="text-right py-3 px-6 text-xs font-semibold text-gray-700 uppercase tracking-wider">Net P&L</th>
                  </tr>
                </thead>
                <tbody>
                  {trades.slice(0, 25).map((trade: any) => {
                    // 格式化持仓时间
                    const formatHoldingTime = (duration: string | null) => {
                      if (!duration) return '--';
                      // duration 格式类似 "0:05:23.123456" 或 "1 day, 2:30:45"
                      const match = duration.match(/(?:(\d+) day[s]?, )?(\d+):(\d+):(\d+)/);
                      if (!match) return duration;
                      const [, days, hours, minutes] = match;
                      if (days) return `${days}D ${hours}H ${minutes}M`;
                      if (parseInt(hours) > 0) return `${parseInt(hours)}H ${minutes}M`;
                      return `${parseInt(minutes)}M`;
                    };

                    const pnl = trade.pnl || 0;
                    const isLong = trade.side === 'long';

                    return (
                      <tr key={trade.id} className="border-b border-gray-100 hover:bg-gray-50/50 transition-colors">
                        <td className="py-4 px-6">
                          <span className={`text-sm font-bold uppercase ${
                            isLong ? 'text-green-600' : 'text-red-600'
                          }`}>
                            {trade.side}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          <div className="flex items-center gap-2">
                            <div className="w-6 h-6 bg-orange-100 rounded-full flex items-center justify-center text-xs font-bold text-orange-600">
                              {trade.symbol.split('/')[0][0]}
                            </div>
                            <span className="font-semibold text-gray-900">{trade.symbol.split('/')[0]}</span>
                          </div>
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          ${formatNumber(trade.entry_price || trade.price, 2)}
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          ${formatNumber(trade.exit_price || trade.price, 2)}
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          {formatNumber(trade.quantity, 4)}
                        </td>
                        <td className="py-4 px-6 text-right text-sm text-gray-600">
                          {formatHoldingTime(trade.holding_duration)}
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          ${formatNumber(trade.notional_entry || trade.total_value, 2)}
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-900">
                          ${formatNumber(trade.notional_exit || trade.total_value, 2)}
                        </td>
                        <td className="py-4 px-6 text-right font-mono text-sm text-gray-600">
                          ${formatNumber(trade.total_fees || trade.fee || 0, 2)}
                        </td>
                        <td className={`py-4 px-6 text-right font-bold text-sm ${
                          pnl >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {pnl >= 0 ? '+' : ''}${formatNumber(pnl, 2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-400">
              No trades yet
            </div>
          )}
        </div>
      </div>

      {/* 右侧侧边栏 - AI 对话 */}
      <div
        className={`flex-shrink-0 transition-all duration-300 ease-in-out ${
          isChatPanelVisible ? 'w-[420px] opacity-100' : 'w-0 opacity-0'
        }`}
      >
        {isChatPanelVisible && (
          <div className="sticky top-0 h-[calc(100vh-180px)] bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
            <ChatPanel sessionId={sessionId} />
          </div>
        )}
      </div>

      {/* 切换按钮 - 固定在右侧 */}
      <button
        onClick={() => setIsChatPanelVisible(!isChatPanelVisible)}
        className={`fixed right-0 top-1/2 -translate-y-1/2 bg-teal-500 hover:bg-teal-600 text-white p-3 shadow-lg transition-all duration-300 z-50 ${
          isChatPanelVisible ? 'rounded-l-lg' : 'rounded-l-lg mr-0'
        }`}
        title={isChatPanelVisible ? '收起对话面板' : '展开对话面板'}
        style={{
          right: isChatPanelVisible ? '420px' : '0px',
        }}
      >
        <svg
          className={`w-5 h-5 transition-transform duration-300 ${
            isChatPanelVisible ? 'rotate-0' : 'rotate-180'
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </button>

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

