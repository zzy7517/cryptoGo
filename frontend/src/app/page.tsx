/**
 * 首页组件 (Home Page)
 *
 * 文件作用：
 * - 项目首页，直接展示交易配置面板
 * - 检查活跃会话并自动跳转
 *
 * 路由：
 * - 访问路径: /
 *
 * 功能：
 * - 页面加载时检查是否有活跃的交易会话
 * - 如果有活跃会话，自动跳转到交易页面 (/trading)
 * - 如果没有活跃会话，直接展示交易配置面板
 * - 配置完成后创建会话并跳转到交易页面
 */
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useSessionStore } from '@/stores/sessionStore';
import { agentApi } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const { activeSession, startSession, isLoading: sessionLoading, fetchActiveSession } = useSessionStore();

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
    <div className="min-h-screen bg-gradient-to-br from-gray-50 via-teal-50 to-cyan-50 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl">
        {/* 品牌标题 */}
        <div className="text-center mb-8">
          <h1 className="text-6xl md:text-7xl font-bold bg-gradient-to-r from-teal-600 via-cyan-600 to-teal-500 bg-clip-text text-transparent mb-4">
            Crypto<span className="text-teal-600">Go</span>
          </h1>
          <p className="text-xl text-gray-600 font-light">
            基于大语言模型的智能加密货币交易系统
          </p>
        </div>

        {/* 配置面板 */}
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl p-8 border border-gray-200">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-gray-800 mb-2">开始交易</h2>
            <p className="text-sm text-gray-600">配置您的交易参数，启动AI智能交易</p>
          </div>

          <div className="space-y-5">
            {/* 会话名称 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                会话名称 <span className="text-gray-400 font-normal">(可选)</span>
              </label>
              <input
                type="text"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                placeholder="例如：BTC 策略测试"
                className="w-full bg-white border-2 border-gray-200 rounded-lg px-4 py-3 text-gray-800 focus:outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-200 transition-all"
              />
            </div>

            {/* 初始资金 */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                初始资金 <span className="text-gray-500 font-normal">(USDT)</span>
              </label>
              <input
                type="number"
                value={initialCapital}
                onChange={(e) => setInitialCapital(e.target.value)}
                placeholder="10000"
                className="w-full bg-white border-2 border-gray-200 rounded-lg px-4 py-3 text-gray-800 focus:outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-200 transition-all"
              />
            </div>

            {/* 自动启动Agent */}
            <div className="border-t-2 border-gray-100 pt-5">
              <div className="flex items-center mb-4">
                <input
                  type="checkbox"
                  id="autoStartAgent"
                  checked={autoStartAgent}
                  onChange={(e) => setAutoStartAgent(e.target.checked)}
                  className="w-5 h-5 text-teal-500 focus:ring-teal-400 rounded"
                />
                <label htmlFor="autoStartAgent" className="ml-3 text-sm font-semibold text-gray-700">
                  自动启动交易代理
                </label>
              </div>

              {autoStartAgent && (
                <div className="ml-8 space-y-3">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      决策间隔
                    </label>
                    <div className="grid grid-cols-4 gap-2 mb-3">
                      {[30, 60, 300, 600].map((seconds) => (
                        <button
                          key={seconds}
                          onClick={() => setDecisionInterval(seconds.toString())}
                          className={`px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                            decisionInterval === seconds.toString()
                              ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-white shadow-md scale-105'
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
                      placeholder="自定义间隔（秒）"
                      className="w-full bg-white border-2 border-gray-200 rounded-lg px-4 py-2 text-gray-800 text-sm focus:outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-200 transition-all"
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 启动按钮 */}
          <button
            onClick={handleStartSession}
            disabled={sessionLoading}
            className="w-full mt-8 px-8 py-4 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white text-lg rounded-xl font-bold transition-all shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98]"
          >
            {sessionLoading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                正在启动...
              </span>
            ) : (
              '🚀 开始交易'
            )}
          </button>

          {/* 提示信息 */}
          <div className="mt-6 p-4 bg-teal-50 border border-teal-200 rounded-lg">
            <p className="text-xs text-teal-700 leading-relaxed">
              💡 <span className="font-semibold">提示：</span>启动后，AI将定时分析市场并自动执行交易决策。您可以在交易监控页面查看实时持仓和决策记录。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
