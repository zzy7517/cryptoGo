/**
 * Chat Panel Component
 * 展示AI决策的聊天记录，包括市场数据输入和AI分析输出
 * 创建时间: 2025-10-31
 */
'use client';

import React, { useEffect, useState, useRef } from 'react';
import { sessionApi } from '@/lib/api';

interface AIDecision {
  id: number;
  created_at: string;
  symbols: string[];
  decision_type: string;
  confidence: number | null;
  prompt_data: any;
  ai_response: string;
  reasoning: string;
  suggested_actions: any[];
  executed: boolean;
  execution_result: any;
}

interface ChatPanelProps {
  sessionId: number;
}

export default function ChatPanel({ sessionId }: ChatPanelProps) {
  const [decisions, setDecisions] = useState<AIDecision[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [hasNewMessages, setHasNewMessages] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const previousDecisionsLengthRef = useRef(0);

  // 获取AI决策记录
  const fetchDecisions = async () => {
    try {
      const response = await sessionApi.getAIDecisions(sessionId);
      if (response.success) {
        const newDecisions = response.data.reverse(); // 反转顺序，最新的在底部
        const hasNew = newDecisions.length > previousDecisionsLengthRef.current;
        
        setDecisions(newDecisions);
        previousDecisionsLengthRef.current = newDecisions.length;
        
        // 如果有新消息且用户正在浏览历史，显示新消息提示
        if (hasNew && isUserScrolling) {
          setHasNewMessages(true);
        }
      }
      setLoading(false);
    } catch (error) {
      console.error('获取AI决策记录失败:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDecisions();
    // 每10秒刷新一次
    const interval = setInterval(fetchDecisions, 10000);
    return () => clearInterval(interval);
  }, [sessionId]);

  // 检测用户是否在底部
  const checkIfAtBottom = () => {
    if (!chatContainerRef.current) return true;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    // 允许50px的误差范围
    return scrollHeight - scrollTop - clientHeight < 50;
  };

  // 滚动事件处理
  const handleScroll = () => {
    const isAtBottom = checkIfAtBottom();
    setIsUserScrolling(!isAtBottom);
    if (isAtBottom) {
      setHasNewMessages(false);
    }
  };

  // 智能自动滚动：只在有新消息且用户在底部时滚动
  useEffect(() => {
    const hasNewMessage = decisions.length > previousDecisionsLengthRef.current;
    
    if (hasNewMessage || decisions.length === previousDecisionsLengthRef.current) {
      // 首次加载或有新消息时
      if (!isUserScrolling) {
        // 用户在底部，平滑滚动到底部
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }
    }
  }, [decisions, isUserScrolling]);

  // 手动滚动到底部
  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    setHasNewMessages(false);
    setIsUserScrolling(false);
  };

  const toggleExpand = (id: number) => {
    const newSet = new Set(expandedIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setExpandedIds(newSet);
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  const getDecisionTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      buy: '买入',
      sell: '卖出',
      hold: '持有',
      rebalance: '再平衡',
      close: '平仓'
    };
    return labels[type] || type;
  };

  const getDecisionTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      buy: 'bg-green-100 text-green-700',
      sell: 'bg-red-100 text-red-700',
      hold: 'bg-gray-100 text-gray-700',
      rebalance: 'bg-blue-100 text-blue-700',
      close: 'bg-orange-100 text-orange-700'
    };
    return colors[type] || 'bg-gray-100 text-gray-700';
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  if (decisions.length === 0) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="text-gray-400 text-lg mb-2">💬</div>
          <div className="text-gray-500 text-sm">暂无AI决策记录</div>
          <div className="text-gray-400 text-xs mt-1">启动Agent后将在此显示</div>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-gray-50 to-white">
      {/* 标题栏 */}
      <div className="flex-shrink-0 bg-white/80 backdrop-blur-sm border-b border-gray-200 px-5 py-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-gray-800 flex items-center gap-2">
              <span className="text-lg">💬</span>
              AI 对话记录
            </h3>
            <p className="text-xs text-gray-500 mt-0.5">共 {decisions.length} 条决策</p>
          </div>
        </div>
      </div>

      {/* 消息列表 */}
      <div 
        ref={chatContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-5 space-y-6 custom-scrollbar relative"
      >
        {decisions.map((decision) => {
          const isExpanded = expandedIds.has(decision.id);

          return (
            <div key={decision.id} className="space-y-4">
              {/* 用户消息 - 用户输入的完整prompt */}
              <div className="flex justify-end">
                <div className="max-w-[85%]">
                  <div className="bg-gradient-to-br from-teal-500 to-teal-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-medium opacity-90">System</span>
                      <span className="text-xs opacity-75">{formatTime(decision.created_at)}</span>
                    </div>

                    <div className="space-y-2">
                      {decision.symbols && decision.symbols.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 mb-2">
                          {decision.symbols.map((symbol) => (
                            <span key={symbol} className="text-xs bg-white/20 backdrop-blur-sm px-2.5 py-1 rounded-full font-medium">
                              {symbol}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* 显示用户prompt的前200个字符 */}
                      {decision.prompt_data?.user_prompt && (
                        <div className="text-sm leading-relaxed">
                          {isExpanded
                            ? decision.prompt_data.user_prompt
                            : decision.prompt_data.user_prompt.substring(0, 150) + '...'}
                        </div>
                      )}

                      {/* 如果没有user_prompt，显示旧的prompt_data */}
                      {!decision.prompt_data?.user_prompt && decision.prompt_data && (
                        <div className="text-xs opacity-90">
                          {isExpanded
                            ? JSON.stringify(decision.prompt_data, null, 2)
                            : '📊 市场数据分析请求'}
                        </div>
                      )}

                      {decision.prompt_data && (
                        <button
                          onClick={() => toggleExpand(decision.id)}
                          className="text-xs underline opacity-80 hover:opacity-100 transition-opacity mt-1"
                        >
                          {isExpanded ? '收起' : '查看更多'}
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* AI 回复 */}
              <div className="flex justify-start">
                <div className="max-w-[85%]">
                  <div className="bg-white border border-gray-200/80 rounded-2xl rounded-tl-sm px-4 py-3.5 shadow-lg hover:shadow-xl transition-shadow">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-800 flex items-center gap-1.5">
                          <span className="text-base">🤖</span>
                          AI Assistant
                        </span>
                        {decision.confidence !== null && (
                          <span className="text-xs text-gray-500 bg-gray-50 px-2 py-0.5 rounded-full">
                            {(decision.confidence * 100).toFixed(0)}%
                          </span>
                        )}
                      </div>
                    </div>

                    {/* 决策类型标签 */}
                    <div className="mb-3 flex items-center gap-2">
                      <span className={`inline-block text-xs px-3 py-1.5 rounded-full font-semibold ${getDecisionTypeColor(decision.decision_type)}`}>
                        {getDecisionTypeLabel(decision.decision_type)}
                      </span>
                      {decision.executed && (
                        <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full bg-green-50 text-green-600 border border-green-200 font-medium">
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                          已执行
                        </span>
                      )}
                    </div>

                    {/* 推理过程 */}
                    {decision.reasoning && (
                      <div className="mb-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap bg-gradient-to-br from-gray-50 to-white p-3 rounded-lg border border-gray-100">
                        {decision.reasoning}
                      </div>
                    )}

                    {/* 建议操作 */}
                    {decision.suggested_actions && decision.suggested_actions.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                          <span>💡</span>
                          建议操作
                        </div>
                        <div className="space-y-2">
                          {decision.suggested_actions.map((action, idx) => (
                            <div key={idx} className="text-xs bg-gradient-to-r from-blue-50 to-teal-50 rounded-lg px-3 py-2 text-gray-700 border border-blue-100/50">
                              {typeof action === 'string' ? action : JSON.stringify(action)}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 执行结果 */}
                    {decision.execution_result && (
                      <div className="mt-3 pt-3 border-t border-gray-100">
                        <div className="text-xs font-semibold text-gray-600 mb-2 flex items-center gap-1">
                          <span>📋</span>
                          执行结果
                        </div>
                        <div className="text-xs bg-blue-50/50 rounded-lg px-3 py-2 text-gray-700 border border-blue-100">
                          <pre className="whitespace-pre-wrap break-words font-mono text-xs">
                            {JSON.stringify(decision.execution_result, null, 2)}
                          </pre>
                        </div>
                      </div>
                    )}

                    {/* 原始AI回复 */}
                    {decision.ai_response && !decision.reasoning && (
                      <div className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                        {decision.ai_response}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
        <div ref={chatEndRef} />

        {/* 新消息提示按钮 */}
        {hasNewMessages && (
          <div className="fixed bottom-24 left-1/2 transform -translate-x-1/2 z-10">
            <button
              onClick={scrollToBottom}
              className="bg-teal-500 hover:bg-teal-600 text-white px-4 py-2 rounded-full shadow-lg flex items-center gap-2 transition-all hover:scale-105 animate-bounce"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
              <span className="text-sm font-medium">有新消息</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
