/**
 * 交易会话状态管理
 * 2025-10-29
 */
import { create } from 'zustand';

export interface TradingSession {
  session_id: number;
  session_name: string;
  status: 'running' | 'completed' | 'stopped' | 'crashed';
  initial_capital: number | null;
  created_at: string;
  config?: Record<string, any>;
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
  startSession: (sessionName?: string, initialCapital?: number, config?: Record<string, any>) => Promise<TradingSession>;
  endSession: (sessionId?: number, status?: string, notes?: string) => Promise<void>;
  fetchSessionList: (status?: string, limit?: number) => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

const API_BASE_URL = 'http://localhost:9527/api/v1';

export const useSessionStore = create<SessionState>((set, get) => ({
  activeSession: null,
  sessions: [],
  isLoading: false,
  error: null,

  fetchActiveSession: async () => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE_URL}/session/active`);
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || '获取活跃会话失败');
      }
      
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

  startSession: async (sessionName?: string, initialCapital?: number, config?: Record<string, any>) => {
    set({ isLoading: true, error: null });
    try {
      const response = await fetch(`${API_BASE_URL}/session/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_name: sessionName,
          initial_capital: initialCapital,
          config: config,
        }),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || '开始会话失败');
      }
      
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
      const response = await fetch(`${API_BASE_URL}/session/end`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          status: status,
          notes: notes,
        }),
      });
      
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || '结束会话失败');
      }
      
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
      const params = new URLSearchParams();
      if (status) params.append('status', status);
      params.append('limit', limit.toString());
      
      const response = await fetch(`${API_BASE_URL}/session/list?${params}`);
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.detail || '获取会话列表失败');
      }
      
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

