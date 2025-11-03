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
    <div className="min-h-screen bg-[#f8f9fa]">
      {/* 顶部导航栏 - 参考 Alpha Arena */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1920px] mx-auto px-8 py-4">
          <div className="flex justify-between items-center">
            {/* Logo 和标题 */}
            <div className="flex items-center gap-8">
              <h1 className="text-2xl font-bold text-gray-900">
                CryptoGo
                <span className="ml-3 text-sm font-normal text-gray-500">by AI</span>
              </h1>
            </div>

            {/* 右侧控制按钮 */}
            <div className="flex items-center gap-4">
              {activeSession && (
                <>
                  {agentStatus && (
                    <div className="flex items-center gap-2 px-4 py-2 bg-green-50 border border-green-200 rounded-lg">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-medium text-green-700">
                        Agent Running · Loop {agentStatus.run_count || 0}
                      </span>
                    </div>
                  )}
                  <button
                    onClick={handleEndSession}
                    disabled={sessionLoading}
                    className="px-5 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-all disabled:opacity-50"
                  >
                    End Session
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 会话错误提示 */}
      {sessionError && (
        <div className="max-w-[1920px] mx-auto px-8 pt-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex justify-between items-center">
            <span className="text-red-600 font-medium">{sessionError}</span>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 font-bold transition-colors"
            >
              ✕
            </button>
          </div>
        </div>
      )}

      {/* 主要内容区域 */}
      <div className="max-w-[1920px] mx-auto px-8 py-6">
        {activeSession && (
          <TradingMonitor sessionId={activeSession.session_id} />
        )}
      </div>
    </div>
  );
}

