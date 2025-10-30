/**
 * 首页组件 (Home Page)
 *
 * 文件作用：
 * - 项目首页/欢迎页面
 * - 展示项目品牌和标语
 * - 提供开始交易入口
 * - 检查活跃会话并自动跳转
 *
 * 路由：
 * - 访问路径: /
 *
 * 功能：
 * - 页面加载时检查是否有活跃的交易会话
 * - 如果有活跃会话，自动跳转到交易页面 (/trading)
 * - 如果没有活跃会话，展示首页并提供开始交易按钮
 * - 点击开始交易按钮，弹出会话配置对话框
 * - 创建会话后自动跳转到交易页面
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSessionStore } from '@/stores/sessionStore';
import { agentApi } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const { activeSession, startSession, isLoading: sessionLoading, fetchActiveSession } = useSessionStore();

  const [showSessionDialog, setShowSessionDialog] = useState(false);
  const [sessionName, setSessionName] = useState('');
  const [initialCapital, setInitialCapital] = useState('10000');
  const [autoStartAgent, setAutoStartAgent] = useState(true);
  const [decisionInterval, setDecisionInterval] = useState('60');
  const [isChecking, setIsChecking] = useState(true);

  // 页面加载时检查是否有活跃会话
  useEffect(() => {
    const checkActiveSession = async () => {
      try {
        await fetchActiveSession();
      } catch (error) {
        console.error('检查活跃会话失败:', error);
      } finally {
        setIsChecking(false);
      }
    };

    checkActiveSession();
  }, [fetchActiveSession]);

  // 如果有活跃会话，自动跳转到交易页面
  useEffect(() => {
    if (!isChecking && activeSession) {
      router.push('/trading');
    }
  }, [isChecking, activeSession, router]);

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

      // 跳转到交易页面
      router.push('/trading');
    } catch (error) {
      console.error('开始会话失败:', error);
      alert('开始会话失败: ' + (error as any).message);
    }
  };

  // 如果正在检查会话状态，显示加载提示
  if (isChecking) {
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
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <main className="flex flex-col items-center justify-center gap-10 text-center px-4">
        <div className="space-y-6">
          <h1 className="text-7xl font-bold bg-gradient-to-r from-teal-600 via-cyan-600 to-teal-500 bg-clip-text text-transparent">
            Crypto<span className="text-teal-600">Go</span>
          </h1>
          <p className="text-2xl text-gray-600 font-light max-w-2xl">
            基于大语言模型的智能加密货币交易系统
          </p>
        </div>

        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <button
            onClick={() => setShowSessionDialog(true)}
            className="px-10 py-4 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white rounded-lg font-semibold transition-all shadow-sm hover:shadow-md"
          >
            开始交易
          </button>
        </div>
      </main>

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
    </div>
  );
}
