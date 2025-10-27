'use client';

/**
 * 全局 Providers 配置 (Global Providers)
 * 
 * 文件作用：
 * - 配置应用级别的 Context Providers
 * - 管理全局的数据获取和缓存策略
 * 
 * 为什么需要这个文件？
 * - Next.js 13+ 的 app router 中，根 layout 是 Server Component
 * - Providers（如 React Query）需要在 Client Component 中初始化
 * - 这个文件使用 'use client' 指令，确保在客户端运行
 * 
 * 当前配置的 Providers：
 * 1. QueryClientProvider (React Query)
 *    - 管理所有异步数据的获取、缓存、同步
 *    - 提供全局的查询和变更功能
 * 
 * React Query 配置说明：
 * - refetchOnWindowFocus: false
 *   * 窗口重新获得焦点时不自动刷新数据
 *   * 避免频繁的网络请求
 * 
 * - retry: 1
 *   * 请求失败时重试 1 次
 *   * 平衡用户体验和服务器负载
 * 
 * 如何扩展？
 * 在这里添加其他需要的 Providers，例如：
 * - Theme Provider（主题切换）
 * - Auth Provider（用户认证）
 * - WebSocket Provider（实时通信）
 * 
 * 使用方式：
 * - 已在 layout.tsx 中自动包装所有页面
 * - 子组件可以直接使用 React Query 的 hooks
 */
import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}

