/**
 * 交易会话状态管理
 * 创建时间: 2025-10-29
 * 更新时间: 2025-11-02 - 使用统一的 API 客户端，移除直接 fetch 调用
 */
import { create } from 'zustand';
import { sessionApi } from '@/lib/api';

export interface TradingSession {
  session_id: number;
  session_name: string;
  status: 'running' | 'completed' | 'stopped' | 'crashed';
  initial_capital: number | null;
  created_at: string;
  config?: Record<string, any>;
  // Agent 状态
  agent_started?: boolean;
  agent_error?: string;
  agent_status?: Record<string, any>;
}

interface SessionState {
  // 当前活跃会话
  activeSession: TradingSession | null;
  
  // 会话列表
  sessions: TradingSession[];
  
  // 加载状态
  isLoading: boolean;
  
  // 错误信息
  error: string | null;
  
  // Actions
  fetchActiveSession: () => Promise<void>;
  startSession: (
    sessionName?: string,
    initialCapital?: number,
    agentConfig?: {
      auto_start_agent?: boolean;
      symbols?: string[];
      decision_interval?: number;
      risk_params?: Record<string, any>;
    }
  ) => Promise<TradingSession>;
  endSession: (sessionId?: number, status?: string, notes?: string) => Promise<void>;
  fetchSessionList: (status?: string, limit?: number) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useSessionStore = create<SessionState>((set, get) => ({
  activeSession: null,
  sessions: [],
  isLoading: false,
  error: null,

  fetchActiveSession: async () => {
    set({ isLoading: true, error: null });
    try {
      const result = await sessionApi.getActiveSession();

      set({
        activeSession: result.data,
        isLoading: false
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      set({
        error: errorMessage,
        isLoading: false,
        activeSession: null
      });
      throw error;
    }
  },

  startSession: async (
    sessionName?: string,
    initialCapital?: number,
    agentConfig?: {
      auto_start_agent?: boolean;
      symbols?: string[];
      decision_interval?: number;
      risk_params?: Record<string, any>;
    }
  ) => {
    set({ isLoading: true, error: null });
    try {
      const result = await sessionApi.startSession({
        session_name: sessionName,
        initial_capital: initialCapital,
        auto_start_agent: agentConfig?.auto_start_agent ?? true,
        symbols: agentConfig?.symbols,
        decision_interval: agentConfig?.decision_interval,
        risk_params: agentConfig?.risk_params,
      });

      const newSession: TradingSession = result.data;

      set({
        activeSession: newSession,
        isLoading: false
      });

      return newSession;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      set({
        error: errorMessage,
        isLoading: false
      });
      throw error;
    }
  },

  endSession: async (sessionId?: number, status: string = 'completed', notes?: string) => {
    set({ isLoading: true, error: null });
    try {
      await sessionApi.endSession({
        session_id: sessionId,
        status: status,
        notes: notes,
      });

      // 清空活跃会话
      set({
        activeSession: null,
        isLoading: false
      });

      // 刷新会话列表
      await get().fetchSessionList();
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      set({
        error: errorMessage,
        isLoading: false
      });
      throw error;
    }
  },

  fetchSessionList: async (status?: string, limit: number = 20) => {
    set({ isLoading: true, error: null });
    try {
      const result = await sessionApi.getSessionList({
        status,
        limit
      });

      set({
        sessions: result.data || [],
        isLoading: false
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : '未知错误';
      set({
        error: errorMessage,
        isLoading: false,
        sessions: []
      });
      throw error;
    }
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set({
      activeSession: null,
      sessions: [],
      isLoading: false,
      error: null,
    });
  },
}));

