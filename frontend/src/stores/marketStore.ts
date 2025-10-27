/**
 * 市场数据状态管理 (Market Data Store)
 * 
 * 文件作用：
 * - 使用 Zustand 管理全局市场数据状态
 * - 提供轻量级、响应式的状态管理方案
 * - 跨组件共享交易相关状态
 * 
 * 为什么使用 Zustand？
 * - 比 Redux 更简单，无需样板代码
 * - 比 Context API 性能更好，避免不必要的重渲染
 * - 自动类型推导，TypeScript 支持优秀
 * - 体积小（~1KB），无依赖
 * 
 * 管理的状态：
 * 1. currentSymbol - 当前选中的交易对（如 'BTC/USDT'）
 * 2. currentInterval - 当前时间周期（如 '1h'）
 * 3. klineData - K线数据数组（OHLCV）
 * 4. tickerData - 实时价格数据（最新价、涨跌幅等）
 * 5. previousPrice - 上一次的价格（用于价格变化动画）
 * 
 * 主要 Actions：
 * - setCurrentSymbol - 切换交易对
 * - setCurrentInterval - 切换时间周期
 * - setKlineData - 完整替换K线数据
 * - appendKlineData - 智能追加/更新K线数据
 *   * 如果时间戳相同：更新最后一根K线（实时更新）
 *   * 如果时间戳不同：追加新K线
 *   * 自动维护最多1000根K线（防止内存溢出）
 * - setTickerData - 更新实时价格（同时记录上一次价格）
 * 
 * 使用示例：
 * // 在组件中
 * const { currentSymbol, setCurrentSymbol } = useMarketStore();
 * 
 * // 切换交易对
 * setCurrentSymbol('ETH/USDT');
 * 
 * // 读取K线数据
 * const { klineData } = useMarketStore();
 * 
 * 特点：
 * - 状态变化自动触发组件重渲染
 * - 支持选择性订阅（只订阅需要的状态）
 * - 无需 Provider 包裹
 */
import { create } from 'zustand';
import type { KlineData, TickerData, TimeInterval } from '@/types/market';

interface MarketState {
  // 当前选中的交易对
  currentSymbol: string;
  setCurrentSymbol: (symbol: string) => void;

  // 当前时间周期
  currentInterval: TimeInterval;
  setCurrentInterval: (interval: TimeInterval) => void;

  // K线数据
  klineData: KlineData[];
  setKlineData: (data: KlineData[]) => void;
  appendKlineData: (data: KlineData) => void;

  // 实时价格数据
  tickerData: TickerData | null;
  setTickerData: (data: TickerData) => void;

  // 上一次的价格（用于价格变化动画）
  previousPrice: number | null;
  setPreviousPrice: (price: number) => void;
}

export const useMarketStore = create<MarketState>((set) => ({
  // 默认值
  currentSymbol: 'BTC/USDT',
  currentInterval: '1h',
  klineData: [],
  tickerData: null,
  previousPrice: null,

  // Actions
  setCurrentSymbol: (symbol) => set({ currentSymbol: symbol }),
  
  setCurrentInterval: (interval) => set({ currentInterval: interval }),
  
  setKlineData: (data) => set({ klineData: data }),
  
  appendKlineData: (data) =>
    set((state) => {
      const newData = [...state.klineData];
      const lastIndex = newData.length - 1;
      
      // 如果时间戳相同，更新最后一根K线
      if (lastIndex >= 0 && newData[lastIndex].timestamp === data.timestamp) {
        newData[lastIndex] = data;
      } else {
        // 否则追加新K线
        newData.push(data);
        // 保持最多1000根K线
        if (newData.length > 1000) {
          newData.shift();
        }
      }
      
      return { klineData: newData };
    }),
  
  setTickerData: (data) =>
    set((state) => ({
      tickerData: data,
      previousPrice: state.tickerData?.last || null,
    })),
  
  setPreviousPrice: (price) => set({ previousPrice: price }),
}));

