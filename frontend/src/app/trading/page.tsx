'use client';

/**
 * 交易监控页面 (Trading Monitor Page)
 *
 * 核心页面：AI自动交易监控界面，专注于交易决策和持仓管理
 * 修改时间: 2025-10-31 (优化页面流程，分离配置和监控)
 *
 * 路由：
 * - 访问路径: /trading
 * - 前置条件: 必须有活跃的交易会话
 * - 如果没有活跃会话，自动跳转到首页(/)进行配置
 *
 * 主要功能：
 * 1. 会话状态显示 - 显示当前运行的交易会话信息
 * 2. 结束交易会话 - 手动结束当前会话
 * 3. Agent 状态监控 - 实时显示 Agent 运行状态和循环次数
 * 4. 交易监控 - 查看AI决策、持仓、资金变化
 *
 * 状态管理：
 * - 使用 Zustand 管理会话状态
 * - 定时轮询 Agent 运行状态
 * - 自动重定向：无活跃会话时跳转到首页
 */
import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import TradingMonitor from '@/components/TradingMonitor';
import { useSessionStore } from '@/stores/sessionStore';
import { agentApi } from '@/lib/api';

export default function TradingPage() {
  const router = useRouter();
  const {
    activeSession,
    isLoading: sessionLoading,
    error: sessionError,
    fetchActiveSession,
    endSession,
    clearError,
  } = useSessionStore();

  const [agentStatus, setAgentStatus] = useState<any>(null);
  const [isCheckingSession, setIsCheckingSession] = useState(true);

  // 页面加载时获取活跃会话
  useEffect(() => {
    const checkSession = async () => {
      try {
        await fetchActiveSession();
      } finally {
        setIsCheckingSession(false);
      }
    };
    checkSession();
  }, [fetchActiveSession]);

  // 如果没有活跃会话，跳转到首页
  useEffect(() => {
    if (!isCheckingSession && !activeSession) {
      router.push('/');
    }
  }, [isCheckingSession, activeSession, router]);

  // 轮询获取 Agent 状态
  useEffect(() => {
    if (!activeSession?.session_id) {
      setAgentStatus(null);
      return;
    }

    const fetchAgentStatus = async () => {
      try {
        const response = await agentApi.getAgentStatus(activeSession.session_id);
        setAgentStatus(response.data);
      } catch (error: any) {
        // 如果是404错误，说明Agent未运行
        if (error.response?.status === 404) {
          setAgentStatus(null);
        } else {
          console.error('获取 Agent 状态失败:', error);
        }
      }
    };

    fetchAgentStatus();
    const interval = setInterval(fetchAgentStatus, 5000); // 每5秒刷新

    return () => clearInterval(interval);
  }, [activeSession]);

  const handleEndSession = async () => {
    if (!confirm('确定要结束当前交易会话吗？')) return;
    
    try {
      await endSession();
      setAgentStatus(null);
    } catch (error) {
      console.error('结束会话失败:', error);
    }
  };


  // 如果正在检查会话状态，显示加载提示
  if (isCheckingSession) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">正在加载...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-[2000px] mx-auto px-6 py-6">
        {/* 顶部标题栏 */}
        <div className="mb-6 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-800 mb-1 flex items-center gap-3">
              <span className="text-4xl">📊</span>
              CryptoGo 交易监控
            </h1>
            <p className="text-gray-500 text-sm">AI自动交易决策与持仓监控</p>
          </div>

          {/* 会话控制区域 */}
          {activeSession && (
            <div className="flex items-center gap-4">
              <div className="bg-white/90 backdrop-blur-sm rounded-xl p-4 border border-green-200/50 shadow-lg">
                <div className="flex items-center gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse shadow-lg shadow-green-500/50"></div>
                      <span className="text-sm font-semibold text-green-600">会话运行中</span>
                    </div>
                    <div className="text-xs text-gray-700 font-medium">
                      {activeSession.session_name}
                    </div>
                    {activeSession.initial_capital && (
                      <div className="text-xs text-gray-500 mt-1">
                        初始资金: ${activeSession.initial_capital.toLocaleString()}
                      </div>
                    )}
                    {agentStatus && (
                      <div className="text-xs mt-2 space-y-1">
                        <div className="flex items-center gap-2">
                          <div className="w-1.5 h-1.5 bg-teal-500 rounded-full animate-pulse"></div>
                          <span className="text-teal-600 font-medium">Agent 运行中</span>
                        </div>
                        <div className="text-gray-500">
                          循环: {agentStatus.run_count || 0} 次 | 间隔: {agentStatus.config?.decision_interval || '?'}s
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={handleEndSession}
                      disabled={sessionLoading}
                      className="px-5 py-2 bg-gradient-to-r from-red-500 to-red-600 hover:from-red-600 hover:to-red-700 text-white rounded-lg text-sm font-semibold transition-all disabled:opacity-50 shadow-md hover:shadow-lg"
                    >
                      结束会话
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 会话错误提示 */}
        {sessionError && (
          <div className="mb-4 bg-red-50 border border-red-200 rounded-xl p-4 flex justify-between items-center shadow-md">
            <span className="text-red-600 font-medium">{sessionError}</span>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 font-bold transition-colors"
            >
              ✕
            </button>
          </div>
        )}

        {/* 主要内容区域 - 交易监控 */}
        {activeSession && (
          <TradingMonitor sessionId={activeSession.session_id} />
        )}
      </div>
    </div>
  );
}

