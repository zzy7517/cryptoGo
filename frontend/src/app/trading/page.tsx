'use client';

/**
 * 交易终端页面 (Trading Terminal Page)
 * 
 * 核心页面：加密货币交易终端主界面，集成所有交易相关的数据展示和交互功能
 * 修改时间: 2025-10-29 (添加会话管理功能)
 * 
 * 路由：
 * - 访问路径: /trading
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
import CandlestickChart from '@/components/CandlestickChart';
import TechnicalIndicators from '@/components/TechnicalIndicators';
import ContractData from '@/components/ContractData';
import AgentMonitor from '@/components/AgentMonitor';
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

  // 页面加载时获取活跃会话
  useEffect(() => {
    fetchActiveSession();
  }, [fetchActiveSession]);

  // 轮询获取 Agent 状态
  useEffect(() => {
    if (!activeSession) {
      setAgentStatus(null);
      return;
    }

    const fetchAgentStatus = async () => {
      try {
        const response = await agentApi.getAgentStatus();
        setAgentStatus(response.data);
      } catch (error) {
        console.error('获取 Agent 状态失败:', error);
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
      if (autoStartAgent) {
        try {
          await agentApi.startAgent({
            decision_interval: parseInt(decisionInterval),
            symbols: [currentSymbol],
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
    try {
      await agentApi.startAgent({
        decision_interval: parseInt(decisionInterval),
        symbols: [currentSymbol],
      });
    } catch (error) {
      console.error('启动 Agent 失败:', error);
      alert('启动 Agent 失败: ' + (error as any).message);
    }
  };

  const handleStopAgent = async () => {
    if (!confirm('确定要停止交易代理吗？')) return;
    
    try {
      await agentApi.stopAgent();
      setAgentStatus(null);
    } catch (error) {
      console.error('停止 Agent 失败:', error);
      alert('停止 Agent 失败: ' + (error as any).message);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-4">
      <div className="max-w-[1920px] mx-auto">
        {/* 顶部标题栏 */}
        <div className="mb-4 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold mb-2">CryptoGo 交易终端</h1>
            <p className="text-gray-400">实时加密货币交易数据</p>
          </div>
          
          {/* 会话控制区域 */}
          <div className="flex items-center gap-4">
            {activeSession ? (
              <div className="bg-gray-900 rounded-lg p-4 border border-green-500">
                <div className="flex items-center gap-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                      <span className="text-sm font-semibold text-green-400">会话运行中</span>
                    </div>
                    <div className="text-xs text-gray-400">
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
                          <div className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-pulse"></div>
                          <span className="text-blue-400">Agent 运行中</span>
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
                        className="px-4 py-2 bg-orange-600 hover:bg-orange-700 rounded text-sm font-medium transition-colors"
                      >
                        停止 Agent
                      </button>
                    ) : (
                      <button
                        onClick={handleStartAgent}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded text-sm font-medium transition-colors"
                      >
                        启动 Agent
                      </button>
                    )}
                    <button
                      onClick={handleEndSession}
                      disabled={sessionLoading}
                      className="px-4 py-2 bg-red-600 hover:bg-red-700 rounded text-sm font-medium transition-colors disabled:opacity-50"
                    >
                      结束会话
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setShowSessionDialog(true)}
                disabled={sessionLoading}
                className="px-6 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-semibold transition-colors disabled:opacity-50 flex items-center gap-2"
              >
                <span className="text-xl">▶</span>
                开始新会话
              </button>
            )}
          </div>
        </div>

        {/* 会话错误提示 */}
        {sessionError && (
          <div className="mb-4 bg-red-900/30 border border-red-500 rounded-lg p-4 flex justify-between items-center">
            <span className="text-red-400">{sessionError}</span>
            <button
              onClick={clearError}
              className="text-red-400 hover:text-red-300"
            >
              ✕
            </button>
          </div>
        )}

        {/* 开始会话对话框 */}
        {showSessionDialog && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <div className="bg-gray-900 rounded-lg p-6 max-w-md w-full mx-4">
              <h2 className="text-xl font-bold mb-4">开始新的交易会话</h2>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    会话名称（可选）
                  </label>
                  <input
                    type="text"
                    value={sessionName}
                    onChange={(e) => setSessionName(e.target.value)}
                    placeholder="例如：BTC 策略测试"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-400 mb-2">
                    初始资金（USDT）
                  </label>
                  <input
                    type="number"
                    value={initialCapital}
                    onChange={(e) => setInitialCapital(e.target.value)}
                    placeholder="10000"
                    className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="border-t border-gray-700 pt-4">
                  <div className="flex items-center mb-3">
                    <input
                      type="checkbox"
                      id="autoStartAgent"
                      checked={autoStartAgent}
                      onChange={(e) => setAutoStartAgent(e.target.checked)}
                      className="mr-2"
                    />
                    <label htmlFor="autoStartAgent" className="text-sm text-gray-300">
                      自动启动交易代理
                    </label>
                  </div>

                  {autoStartAgent && (
                    <div className="space-y-3 pl-6">
                      <div>
                        <label className="block text-sm text-gray-400 mb-2">
                          决策间隔（秒）
                        </label>
                        <div className="flex gap-2 mb-2">
                          {[30, 60, 300, 600].map((seconds) => (
                            <button
                              key={seconds}
                              onClick={() => setDecisionInterval(seconds.toString())}
                              className={`px-3 py-1 rounded text-xs ${
                                decisionInterval === seconds.toString()
                                  ? 'bg-blue-600 text-white'
                                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
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
                          className="w-full bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-3 mt-6">
                <button
                  onClick={() => setShowSessionDialog(false)}
                  className="flex-1 px-4 py-2 bg-gray-800 hover:bg-gray-700 rounded transition-colors"
                >
                  取消
                </button>
                <button
                  onClick={handleStartSession}
                  disabled={sessionLoading}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors disabled:opacity-50"
                >
                  {sessionLoading ? '正在开始...' : '开始会话'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* 控制面板 */}
        <div className="bg-gray-900 rounded-lg p-4 mb-4">
          <div className="flex flex-wrap items-center gap-4">
            {/* 交易对选择 */}
            <div>
              <label className="block text-sm text-gray-400 mb-1">交易对</label>
              <select
                value={currentSymbol}
                onChange={handleSymbolChange}
                className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-blue-500 cursor-pointer min-w-[200px]"
              >
                {TRADING_PAIRS.map((pair) => (
                  <option key={pair.symbol} value={pair.symbol} className="bg-gray-800">
                    {pair.symbol} - {pair.name}
                  </option>
                ))}
              </select>
            </div>

            {/* 时间周期选择 */}
            <div className="flex-1">
              <label className="block text-sm text-gray-400 mb-1">时间周期</label>
              <div className="flex gap-2">
                {INTERVALS.map((interval) => (
                  <button
                    key={interval.value}
                    onClick={() => handleIntervalChange(interval.value)}
                    className={`px-4 py-2 rounded transition-colors ${
                      currentInterval === interval.value
                        ? 'bg-blue-600 text-white'
                        : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    {interval.label}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 主要内容区域 */}
        <div className="grid grid-cols-1 xl:grid-cols-4 gap-4">
          {/* K线图 - 占3列 */}
          <div className="xl:col-span-3 bg-gray-900 rounded-lg p-4">
            <CandlestickChart data={klineData} symbol={currentSymbol} />
          </div>

          {/* 右侧信息面板 - 占1列 */}
          <div className="space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto custom-scrollbar">
            {/* Agent 监控 */}
            {activeSession && (
              <AgentMonitor sessionId={activeSession.session_id} />
            )}

            {/* 实时价格 */}
            <div className="bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-3">实时价格</h3>
              <div
                className={`text-4xl font-bold mb-2 transition-colors duration-300 ${
                  priceAnimation === 'up'
                    ? 'text-green-400'
                    : priceAnimation === 'down'
                    ? 'text-red-400'
                    : 'text-white'
                }`}
              >
                ${formatNumber(tickerData?.last, 2)}
              </div>
              {tickerData && tickerData.percentage !== null && (
                <div
                  className={`text-lg font-semibold ${
                    tickerData.percentage >= 0 ? 'text-green-400' : 'text-red-400'
                  }`}
                >
                  {tickerData.percentage >= 0 ? '+' : ''}
                  {formatNumber(tickerData.percentage, 2)}%
                  <span className="text-sm ml-2">
                    ({tickerData.change && tickerData.change >= 0 ? '+' : ''}
                    {formatNumber(tickerData.change, 2)})
                  </span>
                </div>
              )}
            </div>

            {/* 24小时统计 */}
            <div className="bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-3">24小时统计</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">最高价</span>
                  <span className="font-semibold text-green-400">
                    ${formatNumber(tickerData?.high)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">最低价</span>
                  <span className="font-semibold text-red-400">
                    ${formatNumber(tickerData?.low)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">成交量</span>
                  <span className="font-semibold">{formatVolume(tickerData?.volume)}</span>
                </div>
              </div>
            </div>

            {/* 买卖价 */}
            <div className="bg-gray-900 rounded-lg p-4">
              <h3 className="text-sm text-gray-400 mb-3">订单簿</h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">买一价</span>
                  <span className="font-semibold text-green-400">
                    ${formatNumber(tickerData?.bid)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">卖一价</span>
                  <span className="font-semibold text-red-400">
                    ${formatNumber(tickerData?.ask)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">价差</span>
                  <span className="font-semibold">
                    ${formatNumber(
                      tickerData?.ask && tickerData?.bid
                        ? tickerData.ask - tickerData.bid
                        : 0,
                      2
                    )}
                  </span>
                </div>
              </div>
            </div>

            {/* 技术指标 */}
            <TechnicalIndicators
              indicators={indicators?.latest_values || null}
              loading={indicatorsLoading}
            />

            {/* 合约数据 */}
            <ContractData
              fundingRate={fundingRate || null}
              openInterest={openInterest || null}
              loading={fundingLoading || openInterestLoading}
            />
          </div>
        </div>
      </div>

      {/* 自定义滚动条样式 */}
      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #1a1a1a;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #4a4a4a;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #5a5a5a;
        }
      `}</style>
    </div>
  );
}

