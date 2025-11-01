/**
 * API 客户端 (API Client)
 *
 * 封装所有与后端的 HTTP 通信，提供类型安全的 API 调用方法
 * 创建时间: 2025-10-27
 * 更新时间: 2025-11-01 - 清理未使用的 API
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
 */
import axios from 'axios';
import {
  API_BASE_URL,
  API_TIMEOUT,
  API_ROUTES,
} from '@/constants/apiRoutes';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
});

/**
 * Agent API
 * 交易代理控制 API
 */
export const agentApi = {
  /**
   * 获取后台代理状态
   */
  getAgentStatus: async (sessionId: number): Promise<any> => {
    const response = await apiClient.get(
      API_ROUTES.AGENT.BACKGROUND_STATUS(sessionId)
    );
    return response.data;
  },
};

/**
 * Session API
 * 会话管理 API
 * 更新时间: 2025-11-01
 *
 * 注意：会话的创建、结束、列表查询等操作由 sessionStore 直接使用 fetch 调用
 */
export const sessionApi = {
  /**
   * 获取会话详情（包括持仓、交易记录、决策记录）
   */
  getSessionDetails: async (sessionId: number): Promise<any> => {
    const response = await apiClient.get(API_ROUTES.SESSION.DETAILS(sessionId));
    return response.data;
  },

  /**
   * 获取会话的AI决策记录
   */
  getAIDecisions: async (
    sessionId: number,
    limit?: number
  ): Promise<any> => {
    const response = await apiClient.get(API_ROUTES.SESSION.AI_DECISIONS(sessionId), {
      params: { limit }
    });
    return response.data;
  },
};

/**
 * Account API (通用账户API，支持多交易所)
 * 创建时间: 2025-10-31
 * 更新时间: 2025-11-01
 */
export const accountApi = {
  /**
   * 获取账户摘要（账户+持仓，自动根据配置使用对应交易所）
   */
  getAccountSummary: async (): Promise<any> => {
    const response = await apiClient.get(API_ROUTES.ACCOUNT.SUMMARY);
    return response.data;
  },
};

/**
 * Config API
 * 系统配置 API
 * 创建时间: 2025-11-01
 */
export const configApi = {
  /**
   * 获取默认交易对配置
   */
  getTradingPairs: async (): Promise<{
    success: boolean;
    data: Array<{
      symbol: string;
      name: string;
      description?: string;
    }>;
  }> => {
    const response = await apiClient.get(API_ROUTES.CONFIG.TRADING_PAIRS);
    return response.data;
  },
};

