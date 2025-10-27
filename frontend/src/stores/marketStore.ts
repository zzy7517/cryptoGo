/**
 * 市场数据状态管理
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

