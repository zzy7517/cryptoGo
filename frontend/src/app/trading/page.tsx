'use client';

/**
 * 交易终端页面 (Trading Terminal Page)
 * 
 * 核心页面：加密货币交易终端主界面，集成所有交易相关的数据展示和交互功能
 * 修改时间: 2025-10-29 (优化UI布局和按钮命名，修复hydration错误)
 * 
 * 路由：
 * - 访问路径: /trading
 * - URL参数: ?startSession=true (自动打开开始交易对话框，仅客户端处理)
 * 
 * 主要功能：
 * 1. 交易对选择 - 支持多个币种永续合约
 * 2. 时间周期切换 - 1分钟、5分钟、15分钟、1小时、4小时、1天
 * 3. K线图表展示 - 使用 Lightweight Charts 渲染专业图表
 * 4. 实时价格监控 - 5秒刷新一次
 * 5. 24小时统计数据 - 最高价、最低价、成交量
 * 6. 订单簿信息 - 买一价、卖一价、价差
 * 7. 技术指标面板 - EMA、MACD、RSI、ATR
 * 8. 合约数据展示 - 资金费率、持仓量
 * 
 * 数据获取策略：
 * - K线数据：30秒自动刷新
 * - 实时价格：5秒自动刷新
 * - 技术指标：30秒自动刷新
 * - 资金费率/持仓量：60秒自动刷新
 * 
 * 状态管理：
 * - 使用 Zustand 管理全局状态（交易对、时间周期、数据）
 * - 使用 React Query 管理异步数据获取和缓存
 * 
 * UI特性：
 * - 响应式布局（桌面端4列网格，移动端单列）
 * - 价格变化动画（涨绿跌红）
 * - 自定义滚动条样式
 * - 暗色主题设计
 */
import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import TradingMonitor from '@/components/TradingMonitor';
import MarketView from '@/components/MarketView';
import { useMarketStore } from '@/stores/marketStore';
import { useSessionStore } from '@/stores/sessionStore';
import { marketApi, agentApi } from '@/lib/api';
import { TRADING_PAIRS, getCoinName } from '@/config/tradingPairs';
import type { TimeInterval } from '@/types/market';

const INTERVALS: { value: TimeInterval; label: string }[] = [
  { value: '1m', label: '1分钟' },
  { value: '5m', label: '5分钟' },
  { value: '15m', label: '15分钟' },
  { value: '1h', label: '1小时' },
  { value: '4h', label: '4小时' },
  { value: '1d', label: '1天' },
];

export default function TradingPage() {
  const {
    currentSymbol,
    currentInterval,
    klineData,
    tickerData,
    previousPrice,
    setCurrentSymbol,
    setCurrentInterval,
    setKlineData,
    setTickerData,
  } = useMarketStore();

  const {
    activeSession,
    isLoading: sessionLoading,
    error: sessionError,
    fetchActiveSession,
    startSession,
    endSession,
    clearError,
  } = useSessionStore();

  const [priceAnimation, setPriceAnimation] = useState<'up' | 'down' | null>(null);
  const [showSessionDialog, setShowSessionDialog] = useState(false);
  const [sessionName, setSessionName] = useState('');
  const [initialCapital, setInitialCapital] = useState('10000');
  const [autoStartAgent, setAutoStartAgent] = useState(true);
  const [decisionInterval, setDecisionInterval] = useState('60');
  const [agentStatus, setAgentStatus] = useState<any>(null);
  
  // Tab切换状态：'monitor' - 交易监控, 'market' - 市场行情
  const [activeTab, setActiveTab] = useState<'monitor' | 'market'>('monitor');

  // 页面加载时获取活跃会话
  useEffect(() => {
    fetchActiveSession();
  }, [fetchActiveSession]);

  // 检测URL参数，如果有 startSession=true 则自动打开对话框（仅客户端）
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      if (urlParams.get('startSession') === 'true' && !activeSession) {
        setShowSessionDialog(true);
        // 清除 URL 参数，避免刷新页面时重复弹窗
        window.history.replaceState({}, '', window.location.pathname);
      }
    }
  }, [activeSession]);

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

  // 获取K线数据
  const { data: klineResponse, refetch: refetchKlines } = useQuery({
    queryKey: ['klines', currentSymbol, currentInterval],
    queryFn: () => marketApi.getKlines(currentSymbol, currentInterval, 100),
    refetchInterval: 30000, // 30秒自动刷新
  });

  // 获取实时价格
  const { data: ticker, refetch: refetchTicker } = useQuery({
    queryKey: ['ticker', currentSymbol],
    queryFn: () => marketApi.getTicker(currentSymbol),
    refetchInterval: 5000, // 5秒自动刷新
  });

  // 获取技术指标
  const { data: indicators, isLoading: indicatorsLoading } = useQuery({
    queryKey: ['indicators', currentSymbol, currentInterval],
    queryFn: () => marketApi.getIndicators(currentSymbol, currentInterval, 100, false),
    refetchInterval: 30000, // 30秒自动刷新
  });

  // 获取资金费率
  const { data: fundingRate, isLoading: fundingLoading } = useQuery({
    queryKey: ['fundingRate', currentSymbol],
    queryFn: () => marketApi.getFundingRate(currentSymbol),
    refetchInterval: 60000, // 60秒自动刷新
  });

  // 获取持仓量
  const { data: openInterest, isLoading: openInterestLoading } = useQuery({
    queryKey: ['openInterest', currentSymbol],
    queryFn: () => marketApi.getOpenInterest(currentSymbol),
    refetchInterval: 60000, // 60秒自动刷新
  });

  // 更新K线数据
  useEffect(() => {
    if (klineResponse?.data) {
      setKlineData(klineResponse.data);
    }
  }, [klineResponse, setKlineData]);

  // 更新实时价格
  useEffect(() => {
    if (ticker) {
      setTickerData(ticker);
    }
  }, [ticker, setTickerData]);

  // 价格变化动画
  useEffect(() => {
    if (tickerData && previousPrice !== null) {
      if (tickerData.last > previousPrice) {
        setPriceAnimation('up');
      } else if (tickerData.last < previousPrice) {
        setPriceAnimation('down');
      }
      
      const timer = setTimeout(() => setPriceAnimation(null), 500);
      return () => clearTimeout(timer);
    }
  }, [tickerData, previousPrice]);

  const handleSymbolChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setCurrentSymbol(e.target.value);
  };

  const handleIntervalChange = (interval: TimeInterval) => {
    setCurrentInterval(interval);
  };

  const formatNumber = (num: number | null | undefined, decimals: number = 2): string => {
    if (num === null || num === undefined) return '--';
    return num.toLocaleString('en-US', {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  const formatVolume = (num: number | null | undefined): string => {
    if (num === null || num === undefined) return '--';
    if (num >= 1000000) return `${(num / 1000000).toFixed(2)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(2)}K`;
    return num.toFixed(2);
  };

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
            symbols: [currentSymbol],
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

  const handleStartAgent = async () => {
    if (!activeSession?.session_id) {
      alert('请先开始交易会话');
      return;
    }
    
    try {
      await agentApi.startAgent(activeSession.session_id, {
        symbols: [currentSymbol],
        risk_params: {
          decision_interval: parseInt(decisionInterval),
        },
      });
    } catch (error) {
      console.error('启动 Agent 失败:', error);
      alert('启动 Agent 失败: ' + (error as any).message);
    }
  };

  const handleStopAgent = async () => {
    if (!activeSession?.session_id) {
      alert('请先开始交易会话');
      return;
    }
    
    if (!confirm('确定要停止交易代理吗？')) return;
    
    try {
      await agentApi.stopAgent(activeSession.session_id);
      setAgentStatus(null);
    } catch (error) {
      console.error('停止 Agent 失败:', error);
      alert('停止 Agent 失败: ' + (error as any).message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-[1920px] mx-auto">
        {/* 顶部标题栏 */}
        <div className="mb-6 flex justify-between items-start">
          <div>
            <h1 className="text-4xl font-bold text-gray-800 mb-2">
              CryptoGo 市场看板
            </h1>
            <p className="text-gray-500">实时加密货币交易数据与AI智能分析</p>
          </div>
          
          {/* 会话控制区域 */}
          {activeSession && (
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
                          <span className="text-teal-600">Agent 运行中</span>
                        </div>
                        <div className="text-gray-500">
                          循环次数: {agentStatus.loop_count} | 间隔: {agentStatus.decision_interval}秒
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex flex-col gap-2">
                    {agentStatus ? (
                      <button
                        onClick={handleStopAgent}
                        className="px-4 py-2 bg-teal-500 hover:bg-teal-600 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
                      >
                        停止 Agent
                      </button>
                    ) : (
                      <button
                        onClick={handleStartAgent}
                        className="px-4 py-2 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
                      >
                        启动 Agent
                      </button>
                    )}
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

        {/* Tab切换栏和控制面板 */}
        <div className="bg-white rounded-lg p-6 mb-6 shadow-sm border border-gray-200">
          {/* Tab 切换 */}
          {activeSession && (
            <div className="flex gap-3 mb-6 border-b border-gray-200">
              <button
                onClick={() => setActiveTab('monitor')}
                className={`px-6 py-3 font-semibold transition-all relative ${
                  activeTab === 'monitor'
                    ? 'text-teal-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                交易监控
                {activeTab === 'monitor' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-teal-500 to-cyan-600"></div>
                )}
              </button>
              <button
                onClick={() => setActiveTab('market')}
                className={`px-6 py-3 font-semibold transition-all relative ${
                  activeTab === 'market'
                    ? 'text-teal-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                市场行情
                {activeTab === 'market' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-teal-500 to-cyan-600"></div>
                )}
              </button>
            </div>
          )}
          
          {/* 控制面板 - 仅在市场行情Tab显示 */}
          {(activeTab === 'market' || !activeSession) && (
            <div className="flex flex-wrap items-center gap-6">
              {/* 交易对选择 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">交易对</label>
                <select
                  value={currentSymbol}
                  onChange={handleSymbolChange}
                  className="bg-gray-50 border border-gray-300 rounded-lg px-4 py-2 text-gray-800 focus:outline-none focus:border-teal-500 focus:ring-1 focus:ring-teal-500 cursor-pointer min-w-[200px] font-medium transition-colors"
                >
                  {TRADING_PAIRS.map((pair) => (
                    <option key={pair.symbol} value={pair.symbol} className="bg-white">
                      {pair.symbol} - {pair.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* 时间周期选择 */}
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-2">时间周期</label>
                <div className="flex gap-2 flex-wrap">
                  {INTERVALS.map((interval) => (
                    <button
                      key={interval.value}
                      onClick={() => handleIntervalChange(interval.value)}
                      className={`px-4 py-2 rounded-lg font-medium transition-all ${
                        currentInterval === interval.value
                          ? 'bg-gradient-to-r from-teal-500 to-cyan-600 text-white shadow-sm'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {interval.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 主要内容区域 - 根据Tab切换 */}
        {activeSession && activeTab === 'monitor' ? (
          // 交易监控视图
          <TradingMonitor sessionId={activeSession.session_id} />
        ) : (
          // 市场行情视图
          <MarketView
            klineData={klineData}
            currentSymbol={currentSymbol}
            tickerData={tickerData}
            priceAnimation={priceAnimation}
            indicators={indicators}
            indicatorsLoading={indicatorsLoading}
            fundingRate={fundingRate}
            openInterest={openInterest}
            fundingLoading={fundingLoading}
            openInterestLoading={openInterestLoading}
          />
        )}
      </div>

      {/* 自定义滚动条样式 */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
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

