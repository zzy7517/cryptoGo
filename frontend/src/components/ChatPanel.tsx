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
  const chatEndRef = useRef<HTMLDivElement>(null);

  // 获取AI决策记录
  const fetchDecisions = async () => {
    try {
      const response = await sessionApi.getAIDecisions(sessionId);
      if (response.success) {
        setDecisions(response.data.reverse()); // 反转顺序，最新的在底部
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

  // 自动滚动到底部
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [decisions]);

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
    <div className="h-full flex flex-col bg-gray-50">
      {/* 标题栏 */}
      <div className="flex-shrink-0 bg-white border-b border-gray-200 px-6 py-4">
        <h3 className="text-lg font-semibold text-gray-800">AI 决策记录</h3>
        <p className="text-xs text-gray-500 mt-1">共 {decisions.length} 条决策</p>
      </div>

      {/* 消息列表 */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 custom-scrollbar">
        {decisions.map((decision) => {
          const isExpanded = expandedIds.has(decision.id);

          return (
            <div key={decision.id} className="space-y-3">
              {/* 用户消息 - 用户输入的完整prompt */}
              <div className="flex justify-end">
                <div className="max-w-[75%] bg-teal-500 text-white rounded-lg px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs opacity-90">👤 用户输入</span>
                    <span className="text-xs opacity-75">{formatTime(decision.created_at)}</span>
                  </div>

                  <div className="space-y-2">
                    {decision.symbols && decision.symbols.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {decision.symbols.map((symbol) => (
                          <span key={symbol} className="text-xs bg-teal-600 px-2 py-0.5 rounded">
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
                          : decision.prompt_data.user_prompt.substring(0, 200) + '...'}
                      </div>
                    )}

                    {/* 如果没有user_prompt，显示旧的prompt_data */}
                    {!decision.prompt_data?.user_prompt && decision.prompt_data && (
                      <div className="text-xs opacity-90">
                        {isExpanded
                          ? JSON.stringify(decision.prompt_data, null, 2)
                          : '市场数据分析请求'}
                      </div>
                    )}

                    {decision.prompt_data && (
                      <button
                        onClick={() => toggleExpand(decision.id)}
                        className="text-xs underline opacity-90 hover:opacity-100"
                      >
                        {isExpanded ? '收起' : '展开完整prompt'}
                      </button>
                    )}
                  </div>
                </div>
              </div>

              {/* AI 回复 */}
              <div className="flex justify-start">
                <div className="max-w-[75%] bg-white border border-gray-200 rounded-lg px-4 py-3 shadow-sm">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-semibold text-gray-700">🤖 LLM</span>
                    {decision.confidence !== null && (
                      <span className="text-xs text-gray-500">
                        置信度: {(decision.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  {/* 决策类型标签 */}
                  <div className="mb-3">
                    <span className={`inline-block text-xs px-3 py-1 rounded-full font-medium ${getDecisionTypeColor(decision.decision_type)}`}>
                      {getDecisionTypeLabel(decision.decision_type)}
                    </span>
                    {decision.executed && (
                      <span className="ml-2 inline-block text-xs px-2 py-0.5 rounded bg-green-50 text-green-600 border border-green-200">
                        ✓ 已执行
                      </span>
                    )}
                  </div>

                  {/* 推理过程 */}
                  {decision.reasoning && (
                    <div className="mb-3 text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {decision.reasoning}
                    </div>
                  )}

                  {/* 建议操作 */}
                  {decision.suggested_actions && decision.suggested_actions.length > 0 && (
                    <div className="mt-3 border-t border-gray-100 pt-3">
                      <div className="text-xs font-semibold text-gray-600 mb-2">建议操作:</div>
                      <div className="space-y-1">
                        {decision.suggested_actions.map((action, idx) => (
                          <div key={idx} className="text-xs bg-gray-50 rounded px-3 py-2 text-gray-700">
                            {typeof action === 'string' ? action : JSON.stringify(action)}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 执行结果 */}
                  {decision.execution_result && (
                    <div className="mt-3 border-t border-gray-100 pt-3">
                      <div className="text-xs font-semibold text-gray-600 mb-2">执行结果:</div>
                      <div className="text-xs bg-blue-50 rounded px-3 py-2 text-gray-700">
                        <pre className="whitespace-pre-wrap break-words">
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
          );
        })}
        <div ref={chatEndRef} />
      </div>
    </div>
  );
}
