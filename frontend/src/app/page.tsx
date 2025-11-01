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
import { configApi } from '@/lib/api';

export default function Home() {
  const router = useRouter();
  const { activeSession, startSession, isLoading: sessionLoading, fetchActiveSession } = useSessionStore();

  const [sessionName, setSessionName] = useState('');
  const [initialCapital, setInitialCapital] = useState('5000');
  const [autoStartAgent, setAutoStartAgent] = useState(true);
  const [decisionInterval, setDecisionInterval] = useState('60');
  const [isChecking, setIsChecking] = useState(true);
  const [tradingPairs, setTradingPairs] = useState<Array<{ symbol: string; name: string; description?: string }>>([]);
  const [tradingPairsLoading, setTradingPairsLoading] = useState(true);
  const [selectedSymbols, setSelectedSymbols] = useState<string[]>([]);

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

  // 获取后端配置的交易对
  useEffect(() => {
    const fetchTradingPairs = async () => {
      try {
        const response = await configApi.getTradingPairs();
        if (response.success && response.data) {
          setTradingPairs(response.data);
          // 默认全选
          setSelectedSymbols(response.data.map((pair: any) => pair.symbol));
        }
      } catch (error) {
        console.error('获取交易对配置失败:', error);
        // 使用默认配置作为 fallback
        const defaultPairs = [
          { symbol: 'BTC/USDT:USDT', name: '比特币', description: 'Bitcoin 永续合约' },
          { symbol: 'ETH/USDT:USDT', name: '以太坊', description: 'Ethereum 永续合约' },
          { symbol: 'DOGE/USDT:USDT', name: '狗狗币', description: 'Dogecoin 永续合约' }
        ];
        setTradingPairs(defaultPairs);
        // 默认全选
        setSelectedSymbols(defaultPairs.map(pair => pair.symbol));
      } finally {
        setTradingPairsLoading(false);
      }
    };

    fetchTradingPairs();
  }, []);

  // 如果有活跃会话，自动跳转到交易页面
  useEffect(() => {
    if (!isChecking && activeSession) {
      router.push('/trading');
    }
  }, [isChecking, activeSession, router]);

  const handleStartSession = async () => {
    try {
      // 检查是否至少选择了一个币种（如果启用了自动启动）
      if (autoStartAgent && selectedSymbols.length === 0) {
        alert('请至少选择一个交易币种');
        return;
      }

      // 一次性创建会话并启动 Agent（由后端统一处理）
      const session = await startSession(
        sessionName || undefined,
        initialCapital ? parseFloat(initialCapital) : undefined,
        {
          auto_start_agent: autoStartAgent,
          symbols: autoStartAgent ? selectedSymbols : undefined,
          decision_interval: autoStartAgent ? parseInt(decisionInterval) : undefined,
        }
      );

      // 如果 Agent 启动失败，给出提示（但不阻止跳转）
      if (autoStartAgent && session && !session.agent_started && session.agent_error) {
        console.warn('Agent 启动失败:', session.agent_error);
        alert(`会话创建成功，但 Agent 启动失败: ${session.agent_error}`);
      }

      // 跳转到交易页面
      router.push('/trading');
    } catch (error) {
      console.error('开始会话失败:', error);
      alert('开始会话失败: ' + (error as any).message);
    }
  };

  // 切换币种选择
  const toggleSymbolSelection = (symbol: string) => {
    setSelectedSymbols(prev => {
      if (prev.includes(symbol)) {
        return prev.filter(s => s !== symbol);
      } else {
        return [...prev, symbol];
      }
    });
  };

  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedSymbols.length === tradingPairs.length) {
      setSelectedSymbols([]);
    } else {
      setSelectedSymbols(tradingPairs.map(pair => pair.symbol));
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-teal-900 to-cyan-900 flex items-center justify-center p-4 relative overflow-hidden">
      {/* 背景装饰元素 */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-teal-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-cyan-500 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-teal-400 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="w-full max-w-2xl relative z-10">
        {/* 品牌标题 */}
        <div className="text-center mb-10">
          <h1 className="text-6xl md:text-7xl font-extrabold mb-4 animate-fade-in">
            <span className="bg-gradient-to-r from-teal-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
              CryptoGo
            </span>
          </h1>
        </div>

        {/* 配置面板 */}
        <div className="bg-white/95 backdrop-blur-md rounded-3xl shadow-2xl p-8 md:p-10 border border-gray-200/50 animate-slide-up">
          <div className="mb-8">
            <h2 className="text-3xl font-bold text-gray-800 mb-3 flex items-center gap-3">
              <span className="text-3xl">🚀</span>
              开始交易
            </h2>
            <p className="text-gray-600">配置您的交易参数，让AI为您工作</p>
          </div>

          <div className="space-y-6">
            {/* 会话名称 */}
            <div className="group">
              <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <span className="text-lg">📝</span>
                会话名称 <span className="text-gray-400 font-normal text-xs">(可选)</span>
              </label>
              <input
                type="text"
                value={sessionName}
                onChange={(e) => setSessionName(e.target.value)}
                placeholder="例如：BTC 波段交易策略"
                className="w-full bg-gray-50/80 border-2 border-gray-200 rounded-xl px-5 py-4 text-gray-800 placeholder:text-gray-400 focus:outline-none focus:border-teal-500 focus:bg-white focus:ring-4 focus:ring-teal-100 transition-all duration-200"
              />
            </div>

            {/* 初始资金 */}
            <div className="group">
              <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <span className="text-lg">💰</span>
                初始资金 <span className="text-gray-500 font-normal text-xs">(USDT)</span>
              </label>
              <div className="relative">
                <input
                  type="number"
                  value={initialCapital}
                  onChange={(e) => setInitialCapital(e.target.value)}
                  placeholder="10000"
                  className="w-full bg-gray-50/80 border-2 border-gray-200 rounded-xl px-5 py-4 text-gray-800 placeholder:text-gray-400 focus:outline-none focus:border-teal-500 focus:bg-white focus:ring-4 focus:ring-teal-100 transition-all duration-200"
                />
                <div className="absolute right-5 top-1/2 -translate-y-1/2 text-gray-400 font-medium">
                  USDT
                </div>
              </div>
            </div>

            {/* 自动启动Agent */}
            <div className="bg-gradient-to-br from-teal-50 to-cyan-50 border-2 border-teal-100 rounded-2xl p-6 transition-all duration-300">
              <div className="flex items-center mb-5">
                <input
                  type="checkbox"
                  id="autoStartAgent"
                  checked={autoStartAgent}
                  onChange={(e) => setAutoStartAgent(e.target.checked)}
                  className="w-5 h-5 text-teal-600 focus:ring-teal-500 rounded cursor-pointer"
                />
                <label htmlFor="autoStartAgent" className="ml-3 text-sm font-semibold text-gray-800 cursor-pointer flex items-center gap-2">
                  <span className="text-lg">🤖</span>
                  自动启动交易代理
                </label>
              </div>

              {autoStartAgent && (
                <div className="space-y-4 animate-fade-in">
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                      <span className="text-base">⏱️</span>
                      决策间隔
                    </label>
                    <div className="grid grid-cols-4 gap-2 mb-4">
                      {[30, 60, 300, 600].map((seconds) => (
                        <button
                          key={seconds}
                          type="button"
                          onClick={() => setDecisionInterval(seconds.toString())}
                          className={`px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-200 ${
                            decisionInterval === seconds.toString()
                              ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-white shadow-lg shadow-teal-500/50 scale-105 ring-2 ring-teal-400'
                              : 'bg-white text-gray-700 hover:bg-gray-100 border-2 border-gray-200 hover:border-teal-300'
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
                      className="w-full bg-white border-2 border-gray-200 rounded-xl px-5 py-3 text-gray-800 text-sm placeholder:text-gray-400 focus:outline-none focus:border-teal-500 focus:ring-4 focus:ring-teal-100 transition-all duration-200"
                    />
                  </div>

                  {/* 交易币种选择 */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2 justify-between">
                      <span className="flex items-center gap-2">
                        <span className="text-base">💹</span>
                        交易币种
                      </span>
                      <button
                        type="button"
                        onClick={toggleSelectAll}
                        className="text-xs text-teal-600 hover:text-teal-700 font-semibold"
                      >
                        {selectedSymbols.length === tradingPairs.length ? '取消全选' : '全选'}
                      </button>
                    </label>
                    {tradingPairsLoading ? (
                      <div className="bg-white rounded-xl px-4 py-3 border-2 border-gray-200">
                        <p className="text-sm text-gray-500">加载中...</p>
                      </div>
                    ) : (
                      <div className="bg-white rounded-xl px-4 py-3 border-2 border-gray-200">
                        <div className="flex flex-wrap gap-2">
                          {tradingPairs.map((pair) => {
                            const isSelected = selectedSymbols.includes(pair.symbol);
                            return (
                              <button
                                key={pair.symbol}
                                type="button"
                                onClick={() => toggleSymbolSelection(pair.symbol)}
                                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-semibold transition-all ${
                                  isSelected
                                    ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-white shadow-md'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                }`}
                                title={pair.description}
                              >
                                {isSelected && <span>✓</span>}
                                {pair.name}
                              </button>
                            );
                          })}
                        </div>
                        <p className="text-xs text-gray-500 mt-2">
                          已选择 {selectedSymbols.length} 个币种 · AI 将监控并自动交易选中的币种
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* 启动按钮 */}
          <button
            onClick={handleStartSession}
            disabled={sessionLoading}
            className="w-full mt-8 px-8 py-5 bg-gradient-to-r from-teal-500 via-cyan-600 to-teal-500 bg-size-200 hover:bg-right text-white text-lg rounded-2xl font-bold transition-all duration-300 shadow-xl shadow-teal-500/50 hover:shadow-2xl hover:shadow-teal-500/60 disabled:opacity-50 disabled:cursor-not-allowed transform hover:scale-[1.02] active:scale-[0.98] relative overflow-hidden group"
          >
            <span className="relative z-10 flex items-center justify-center gap-3">
              {sessionLoading ? (
                <>
                  <div className="w-6 h-6 border-3 border-white border-t-transparent rounded-full animate-spin"></div>
                  正在开始交易...
                </>
              ) : (
                <>
                  <span className="text-2xl">🚀</span>
                  开始交易
                </>
              )}
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-teal-600 to-cyan-600 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          </button>
        </div>
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0, 0) scale(1); }
          25% { transform: translate(20px, -50px) scale(1.1); }
          50% { transform: translate(-20px, 20px) scale(0.9); }
          75% { transform: translate(50px, 50px) scale(1.05); }
        }
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes slide-up {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        .animate-fade-in {
          animation: fade-in 0.6s ease-out;
        }
        .animate-slide-up {
          animation: slide-up 0.8s ease-out;
        }
        .bg-size-200 {
          background-size: 200%;
        }
        .bg-right {
          background-position: right;
        }
      `}</style>
    </div>
  );
}
