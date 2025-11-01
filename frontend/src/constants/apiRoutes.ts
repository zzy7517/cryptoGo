/**
 * API 路由常量
 * 创建时间: 2025-11-01
 * 更新时间: 2025-11-01 - 清理未使用的路由
 *
 * 统一管理所有 API 路由，方便维护和修改
 * 使用常量的好处：
 * 1. 避免硬编码，减少拼写错误
 * 2. 便于全局搜索和替换
 * 3. 提供类型提示
 * 4. 方便 API 版本升级
 */

/**
 * API 基础配置
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:9527';
export const API_TIMEOUT = 10000; // 10秒

/**
 * API 版本前缀
 */
const API_V1 = '/api/v1';

/**
 * Agent 控制相关路由
 */
export const AGENT_ROUTES = {
  START_BACKGROUND: (sessionId: number) => `${API_V1}/agent/sessions/${sessionId}/start-background`,
  BACKGROUND_STATUS: (sessionId: number) => `${API_V1}/agent/sessions/${sessionId}/background-status`,
} as const;

/**
 * 会话管理相关路由
 */
export const SESSION_ROUTES = {
  DETAILS: (sessionId: number) => `${API_V1}/session/${sessionId}`,
  AI_DECISIONS: (sessionId: number) => `${API_V1}/session/${sessionId}/ai-decisions`,
} as const;

/**
 * 账户相关路由
 */
export const ACCOUNT_ROUTES = {
  SUMMARY: `${API_V1}/account/summary`,
} as const;

/**
 * 配置相关路由
 */
export const CONFIG_ROUTES = {
  TRADING_PAIRS: `${API_V1}/config/trading-pairs`,
} as const;

/**
 * 所有 API 路由（扁平化结构，方便查找）
 */
export const API_ROUTES = {
  AGENT: AGENT_ROUTES,
  SESSION: SESSION_ROUTES,
  ACCOUNT: ACCOUNT_ROUTES,
  CONFIG: CONFIG_ROUTES,
} as const;

/**
 * 类型导出（供 TypeScript 使用）
 */
export type ApiRoutes = typeof API_ROUTES;
