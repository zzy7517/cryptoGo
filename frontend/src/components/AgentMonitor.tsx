/**
 * Agent Monitor Component
 * 实时监控交易代理状态
 * 创建时间: 2025-10-29
 */
'use client';

import React, { useEffect, useState } from 'react';
import { agentApi } from '@/lib/api';

interface AgentMonitorProps {
  sessionId?: number;
}

export default function AgentMonitor({ sessionId }: AgentMonitorProps) {
  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [recentDecisions, setRecentDecisions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!sessionId) {
      setLoading(false);
      return;
    }

    const fetchData = async () => {
      try {
        // 获取 Agent 状态
        const statusResponse = await agentApi.getAgentStatus(sessionId);
        setAgentStatus(statusResponse.data);
        
        setLoading(false);
      } catch (error) {
        console.error('获取 Agent 数据失败:', error);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000); // 每5秒刷新

    return () => clearInterval(interval);
  }, [sessionId]);

  if (loading) {
    return (
      <div className="bg-gray-900 rounded-lg p-4">
        <h3 className="text-sm text-gray-400 mb-3">Agent 监控</h3>
        <div className="text-center text-gray-500">加载中...</div>
      </div>
    );
  }

  if (!agentStatus) {
    return (
      <div className="bg-gray-900 rounded-lg p-4">
        <h3 className="text-sm text-gray-400 mb-3">Agent 监控</h3>
        <div className="text-center text-gray-500 text-sm">Agent 未运行</div>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 rounded-lg p-4">
      <h3 className="text-sm text-gray-400 mb-3">Agent 监控</h3>
      
      <div className="space-y-3">
        {/* 状态指示器 */}
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            agentStatus.status === 'running' ? 'bg-green-500 animate-pulse' :
            agentStatus.status === 'stopping' ? 'bg-yellow-500' :
            'bg-gray-500'
          }`}></div>
          <span className="text-sm font-semibold">
            {agentStatus.status === 'running' ? '运行中' :
             agentStatus.status === 'stopping' ? '停止中' :
             agentStatus.status}
          </span>
        </div>

        {/* 当前节点 */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">当前节点</span>
          <span className="font-mono text-blue-400">{agentStatus.current_node}</span>
        </div>

        {/* 循环次数 */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">循环次数</span>
          <span className="font-semibold">{agentStatus.loop_count}</span>
        </div>

        {/* 决策间隔 */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">决策间隔</span>
          <span className="font-semibold">{agentStatus.decision_interval}秒</span>
        </div>

        {/* 交易对 */}
        <div className="flex justify-between text-sm">
          <span className="text-gray-400">监控币种</span>
          <div className="flex flex-wrap gap-1 justify-end">
            {agentStatus.symbols?.map((symbol: string) => (
              <span key={symbol} className="text-xs bg-gray-800 px-2 py-1 rounded">
                {symbol}
              </span>
            ))}
          </div>
        </div>

        {/* 最后更新时间 */}
        {agentStatus.last_loop_time && (
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">最后循环</span>
            <span className="text-xs text-gray-500">
              {new Date(agentStatus.last_loop_time).toLocaleTimeString('zh-CN')}
            </span>
          </div>
        )}

        {/* 错误信息 */}
        {agentStatus.error_count > 0 && (
          <div className="mt-2 p-2 bg-red-900/30 border border-red-500 rounded">
            <div className="text-xs text-red-400 font-semibold mb-1">
              错误次数: {agentStatus.error_count}
            </div>
            {agentStatus.last_error && (
              <div className="text-xs text-gray-400 break-words">
                {agentStatus.last_error}
              </div>
            )}
          </div>
        )}

        {/* 运行时长 */}
        {agentStatus.started_at && (
          <div className="flex justify-between text-sm pt-2 border-t border-gray-700">
            <span className="text-gray-400">运行时长</span>
            <span className="text-xs text-gray-500">
              {Math.floor((new Date().getTime() - new Date(agentStatus.started_at).getTime()) / 60000)} 分钟
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

