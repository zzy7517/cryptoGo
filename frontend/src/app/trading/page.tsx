'use client';

/**
 * 交易终端页面 (Trading Terminal Page)
 *
 * 核心页面：AI自动交易监控界面，专注于交易决策和持仓管理
 * 修改时间: 2025-10-31 (移除市场看板，聚焦自动交易)
 *
 * 路由：
 * - 访问路径: /trading
 *
 * 主要功能：
 * 1. 交易会话管理 - 开始/结束交易会话
 * 2. AI代理控制 - 启动/停止自动交易代理
 * 3. 交易监控 - 查看AI决策、持仓、资金变化
 * 4. 会话配置 - 初始资金、决策间隔等参数设置
 *
 * 状态管理：
 * - 使用 Zustand 管理会话状态
 * - 定时轮询 Agent 运行状态
 */
import React, { useEffect, useState } from 'react';
import TradingMonitor from '@/components/TradingMonitor';
import { useSessionStore } from '@/stores/sessionStore';
import { agentApi } from '@/lib/api';

export default function TradingPage() {
  const {
    activeSession,
    isLoading: sessionLoading,
    error: sessionError,
    fetchActiveSession,
    startSession,
    endSession,
    clearError,
  } = useSessionStore();

  const [showSessionDialog, setShowSessionDialog] = useState(false);
  const [sessionName, setSessionName] = useState('');
  const [initialCapital, setInitialCapital] = useState('10000');
  const [autoStartAgent, setAutoStartAgent] = useState(true);
  const [decisionInterval, setDecisionInterval] = useState('60');
  const [agentStatus, setAgentStatus] = useState<any>(null);

  // 页面加载时获取活跃会话
  useEffect(() => {
    fetchActiveSession();
  }, [fetchActiveSession]);

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

  const handleStartSession = async () => {
    try {
      const session = await startSession(
        sessionName || undefined,
        initialCapital ? parseFloat(initialCapital) : undefined
      );

      // 如果勾选了自动启动 Agent
      if (autoStartAgent && session?.session_id) {
        try {
          await agentApi.startAgent(session.session_id, {
            symbols: ['BTC/USDT'],
            risk_params: {
              decision_interval: parseInt(decisionInterval),
            },
          });
        } catch (error) {
          console.error('启动 Agent 失败:', error);
        }
      }

      setShowSessionDialog(false);
      setSessionName('');
      setInitialCapital('10000');
      setDecisionInterval('60');
      setAutoStartAgent(true);
    } catch (error) {
      console.error('开始会话失败:', error);
    }
  };

  const handleEndSession = async () => {
    if (!confirm('确定要结束当前交易会话吗？')) return;
    
    try {
      await endSession();
      setAgentStatus(null);
    } catch (error) {
      console.error('结束会话失败:', error);
    }
  };


  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-[1920px] mx-auto">
        {/* 顶部标题栏 */}
        <div className="mb-6 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              CryptoGo 交易监控
            </h1>
            <p className="text-gray-500">AI自动交易决策与持仓监控</p>
          </div>

          {/* 会话控制区域 */}
          {activeSession ? (
            <div className="flex items-center gap-4">
              <div className="bg-white rounded-lg p-4 border border-green-300 shadow-sm">
                <div className="flex items-center gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-semibold text-green-600">会话运行中</span>
                    </div>
                    <div className="text-xs text-gray-600">
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
                          <span className="text-teal-600">Agent 运行中（定时循环）</span>
                        </div>
                        <div className="text-gray-500">
                          循环次数: {agentStatus.run_count || 0} | 间隔: {agentStatus.config?.decision_interval || '未知'}秒
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-2">
                    <button
                      onClick={handleEndSession}
                      disabled={sessionLoading}
                      className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 shadow-sm"
                    >
                      结束会话
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <button
              onClick={() => setShowSessionDialog(true)}
              className="px-6 py-3 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white rounded-lg font-semibold transition-all shadow-sm"
            >
              开始交易
            </button>
          )}
        </div>

        {/* 会话错误提示 */}
        {sessionError && (
          <div className="mb-4 bg-red-50 border border-red-300 rounded-lg p-4 flex justify-between items-center shadow-sm">
            <span className="text-red-600 font-medium">{sessionError}</span>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700 font-bold"
            >
              ✕
            </button>
          </div>
        )}

        {/* 开始交易对话框 */}
        {showSessionDialog && (
          <div className="fixed inset-0 bg-black/40 backdrop-blur-sm flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 shadow-lg">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">开始交易</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    会话名称（可选）
                  </label>
                  <input
                    type="text"
                    value={sessionName}
                    onChange={(e) => setSessionName(e.target.value)}
                    placeholder="例如：BTC 策略测试"
                    className="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-3 text-gray-800 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    初始资金（USDT）
                  </label>
                  <input
                    type="number"
                    value={initialCapital}
                    onChange={(e) => setInitialCapital(e.target.value)}
                    placeholder="10000"
                    className="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-3 text-gray-800 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
                  />
                </div>

                <div className="border-t border-gray-200 pt-4">
                  <div className="flex items-center mb-3">
                    <input
                      type="checkbox"
                      id="autoStartAgent"
                      checked={autoStartAgent}
                      onChange={(e) => setAutoStartAgent(e.target.checked)}
                      className="mr-3 w-4 h-4 text-teal-500 focus:ring-teal-400 rounded"
                    />
                    <label htmlFor="autoStartAgent" className="text-sm font-medium text-gray-700">
                      自动启动交易代理
                    </label>
                  </div>

                  {autoStartAgent && (
                    <div className="space-y-3 pl-7">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          决策间隔（秒）
                        </label>
                        <div className="flex gap-2 mb-2 flex-wrap">
                          {[30, 60, 300, 600].map((seconds) => (
                            <button
                              key={seconds}
                              onClick={() => setDecisionInterval(seconds.toString())}
                              className={`px-4 py-2 rounded-lg text-xs font-medium transition-all ${
                                decisionInterval === seconds.toString()
                                  ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-white shadow-sm'
                                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                              }`}
                            >
                              {seconds < 60 ? `${seconds}秒` : `${seconds / 60}分钟`}
                            </button>
                          ))}
                        </div>
                        <input
                          type="number"
                          value={decisionInterval}
                          onChange={(e) => setDecisionInterval(e.target.value)}
                          min="10"
                          max="3600"
                          className="w-full bg-gray-50 border border-gray-300 rounded-lg px-4 py-3 text-gray-800 text-sm focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 transition-colors"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-3 mt-8">
                <button
                  onClick={() => setShowSessionDialog(false)}
                  className="flex-1 px-6 py-3 bg-gray-100 hover:bg-gray-200 text-gray-800 rounded-lg font-semibold transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleStartSession}
                  disabled={sessionLoading}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white rounded-lg font-semibold transition-all shadow-sm disabled:opacity-50"
                >
                  {sessionLoading ? '正在开始...' : '开始交易'}
                </button>
              </div>
            </div>
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

