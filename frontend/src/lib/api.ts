/**
 * API 客户端 (API Client)
 *
 *  - 封装所有与后端的 HTTP 通信
 * - 提供类型安全的 API 调用方法
 * - 统一管理 API 配置（URL、超时、错误处理）
 *
 * 创建时间: 2025-10-27
 */
import axios from 'axios';

/**
 * API 基础配置
 */
export const API_BASE_URL = 'http://localhost:9527';
export const API_TIMEOUT = 10000; // 10秒

/**
 * API 版本前缀
 */
const API_V1 = '/api/v1';

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
      `${API_V1}/agent/sessions/${sessionId}/background-status`
    );
    return response.data;
  },
};

/**
 * Session API
 * 会话管理 API
 * 更新时间: 2025-11-02 - 添加完整的会话管理方法
 */
export const sessionApi = {
  /**
   * 获取当前活跃会话
   */
  getActiveSession: async (): Promise<any> => {
    const response = await apiClient.get(`${API_V1}/session/active`);
    return response.data;
  },

  /**
   * 开始新会话
   */
  startSession: async (params: {
    session_name?: string;
    initial_capital?: number;
    auto_start_agent?: boolean;
    symbols?: string[];
    decision_interval?: number;
    risk_params?: Record<string, any>;
  }): Promise<any> => {
    const response = await apiClient.post(`${API_V1}/session/start`, params);
    return response.data;
  },

  /**
   * 结束会话
   */
  endSession: async (params: {
    session_id?: number;
    status?: string;
    notes?: string;
  }): Promise<any> => {
    const response = await apiClient.post(`${API_V1}/session/end`, params);
    return response.data;
  },

  /**
   * 获取会话列表
   */
  getSessionList: async (params?: {
    status?: string;
    limit?: number;
  }): Promise<any> => {
    const response = await apiClient.get(`${API_V1}/session/list`, { params });
    return response.data;
  },

  /**
   * 获取会话详情（包括持仓、交易记录、决策记录）
   */
  getSessionDetails: async (sessionId: number): Promise<any> => {
    const response = await apiClient.get(`${API_V1}/session/${sessionId}`);
    return response.data;
  },

  /**
   * 获取会话的AI决策记录
   */
  getAIDecisions: async (
    sessionId: number,
    limit?: number
  ): Promise<any> => {
    const response = await apiClient.get(`${API_V1}/session/${sessionId}/ai-decisions`, {
      params: { limit }
    });
    return response.data;
  },
};

/**
 * Account API (通用账户API，支持多交易所)
 * 创建时间: 2025-10-31
 * 更新时间: 2025-11-02
 */
export const accountApi = {
  /**
   * 获取账户摘要（账户+持仓，自动根据配置使用对应交易所）
   */
  getAccountSummary: async (): Promise<any> => {
    const response = await apiClient.get(`${API_V1}/account/summary`);
    return response.data;
  },
};


