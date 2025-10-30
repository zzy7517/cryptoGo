/**
 * API 客户端 (API Client)
 * 
 * 封装所有与后端的 HTTP 通信，提供类型安全的 API 调用方法
 * 创建时间: 2025-10-27
 * 
 * 文件作用：
 * - 封装所有与后端的 HTTP 通信
 * - 提供类型安全的 API 调用方法
 * - 统一管理 API 配置（URL、超时、错误处理）
 * 
 * 技术栈：
 * - Axios：HTTP 客户端库
 * - TypeScript：类型安全
 * 
 * 配置：
 * - 基础URL：从环境变量读取 NEXT_PUBLIC_API_URL，默认 http://localhost:9527
 * - 超时时间：10秒
 * - 自动序列化请求参数
 * 
 * API 方法列表：
 * 1. getKlines - 获取K线历史数据
 *    参数：symbol, interval, limit
 *    返回：KlineResponse（包含OHLCV数据）
 * 
 * 2. getTicker - 获取实时价格和24小时统计
 *    参数：symbol
 *    返回：TickerData（价格、涨跌幅、成交量等）
 * 
 * 3. getSymbols - 获取交易所支持的交易对列表
 *    参数：quote（报价币种，默认USDT）
 *    返回：SymbolListResponse
 * 
 * 4. getFundingRate - 获取合约资金费率
 *    参数：symbol
 *    返回：FundingRateData
 * 
 * 5. getOpenInterest - 获取合约持仓量
 *    参数：symbol
 *    返回：OpenInterestData
 * 
 * 6. getIndicators - 获取技术指标
 *    参数：symbol, interval, limit, includeSeries
 *    返回：IndicatorsResponse（EMA、MACD、RSI、ATR等）
 * 
 * 使用示例：
 * const klines = await marketApi.getKlines('BTC/USDT', '1h', 100);
 * const ticker = await marketApi.getTicker('BTC/USDT');
 * 
 * 错误处理：
 * - Axios 会自动抛出错误，由调用方（React Query）捕获
 * - 可以配合 React Query 的重试机制使用
 */
import axios from 'axios';
import type {
  KlineResponse,
  TickerData,
  SymbolListResponse,
  TimeInterval,
  FundingRateData,
  OpenInterestData,
  IndicatorsResponse,
} from '@/types/market';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9527';

const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
});

export const marketApi = {
  /**
   * 获取K线数据
   */
  getKlines: async (
    symbol: string,
    interval: TimeInterval,
    limit: number = 100
  ): Promise<KlineResponse> => {
    const response = await apiClient.get('/api/v1/market/klines', {
      params: { symbol, interval, limit },
    });
    return response.data;
  },

  /**
   * 获取实时价格
   */
  getTicker: async (symbol: string): Promise<TickerData> => {
    const response = await apiClient.get('/api/v1/market/ticker', {
      params: { symbol },
    });
    return response.data;
  },

  /**
   * 获取交易对列表（从交易所获取）
   */
  getSymbols: async (quote: string = 'USDT'): Promise<SymbolListResponse> => {
    const response = await apiClient.get('/api/v1/market/symbols', {
      params: { quote },
    });
    return response.data;
  },

  /**
   * 获取资金费率
   */
  getFundingRate: async (symbol: string): Promise<FundingRateData> => {
    const response = await apiClient.get('/api/v1/market/funding-rate', {
      params: { symbol },
    });
    return response.data;
  },

  /**
   * 获取持仓量
   */
  getOpenInterest: async (symbol: string): Promise<OpenInterestData> => {
    const response = await apiClient.get('/api/v1/market/open-interest', {
      params: { symbol },
    });
    return response.data;
  },

  /**
   * 获取技术指标
   */
  getIndicators: async (
    symbol: string,
    interval: TimeInterval,
    limit: number = 100,
    includeSeries: boolean = false
  ): Promise<IndicatorsResponse> => {
    const response = await apiClient.get('/api/v1/market/indicators', {
      params: { symbol, interval, limit, include_series: includeSeries },
    });
    return response.data;
  },
};

/**
 * Agent API
 * 交易代理控制 API (更新以匹配新的后端 API)
 */
export const agentApi = {
  /**
   * 运行一次决策周期（单次执行）
   */
  runOnce: async (
    sessionId: number,
    params: {
      symbols?: string[];
      risk_params?: Record<string, any>;
      max_iterations?: number;
      model?: string;
    }
  ): Promise<any> => {
    const response = await apiClient.post(
      `/api/v1/agent/sessions/${sessionId}/run-once`,
      params
    );
    return response.data;
  },

  /**
   * 启动后台挂机代理
   */
  startAgent: async (
    sessionId: number,
    params: {
      symbols?: string[];
      risk_params?: Record<string, any>;
      max_iterations?: number;
      model?: string;
    }
  ): Promise<any> => {
    const response = await apiClient.post(
      `/api/v1/agent/sessions/${sessionId}/start-background`,
      params
    );
    return response.data;
  },

  /**
   * 停止后台代理
   */
  stopAgent: async (sessionId: number): Promise<any> => {
    const response = await apiClient.post(
      `/api/v1/agent/sessions/${sessionId}/stop-background`
    );
    return response.data;
  },

  /**
   * 获取后台代理状态
   */
  getAgentStatus: async (sessionId: number): Promise<any> => {
    const response = await apiClient.get(
      `/api/v1/agent/sessions/${sessionId}/background-status`
    );
    return response.data;
  },

  /**
   * 列出所有运行中的代理
   */
  listRunningAgents: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/agent/background-agents/list');
    return response.data;
  },

  /**
   * 测试 Agent（不需要真实会话）
   */
  testAgent: async (params: {
    symbols?: string[];
    risk_params?: Record<string, any>;
    max_iterations?: number;
    model?: string;
  }): Promise<any> => {
    const response = await apiClient.post('/api/v1/agent/test', params);
    return response.data;
  },
};

/**
 * Session API
 * 会话管理 API
 */
export const sessionApi = {
  /**
   * 获取会话详情（包括持仓、交易记录、决策记录）
   */
  getSessionDetails: async (sessionId: number): Promise<any> => {
    const response = await apiClient.get(`/api/v1/session/${sessionId}`);
    return response.data;
  },

  /**
   * 获取活跃会话
   */
  getActiveSession: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/session/active');
    return response.data;
  },

  /**
   * 获取会话列表
   */
  getSessionList: async (params?: {
    status?: string;
    limit?: number;
  }): Promise<any> => {
    const response = await apiClient.get('/api/v1/session/list', { params });
    return response.data;
  },
};

