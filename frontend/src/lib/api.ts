/**
 * API 客户端
 */
import axios from 'axios';
import type {
  KlineResponse,
  TickerData,
  SymbolListResponse,
  MarketStats,
  TimeInterval,
} from '@/types/market';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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
   * 获取交易对列表
   */
  getSymbols: async (quote: string = 'USDT'): Promise<SymbolListResponse> => {
    const response = await apiClient.get('/api/v1/market/symbols', {
      params: { quote },
    });
    return response.data;
  },

  /**
   * 获取市场统计数据
   */
  getStats: async (symbol: string): Promise<MarketStats> => {
    const response = await apiClient.get('/api/v1/market/stats', {
      params: { symbol },
    });
    return response.data;
  },

  /**
   * 健康检查
   */
  healthCheck: async (): Promise<{ status: string; exchange: string; message: string }> => {
    const response = await apiClient.get('/api/v1/market/health');
    return response.data;
  },
};

