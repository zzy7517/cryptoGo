/**
 * 市场数据类型定义
 */

export interface KlineData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface KlineResponse {
  symbol: string;
  interval: string;
  data: KlineData[];
  count: number;
}

export interface TickerData {
  symbol: string;
  last: number;
  bid: number | null;
  ask: number | null;
  high: number | null;
  low: number | null;
  volume: number | null;
  change: number | null;
  percentage: number | null;
  timestamp: number;
}

export interface SymbolInfo {
  symbol: string;
  base: string;
  quote: string;
  active: boolean;
}

export interface SymbolListResponse {
  symbols: SymbolInfo[];
  count: number;
}

export interface MarketStats {
  symbol: string;
  price: number;
  high_24h: number;
  low_24h: number;
  volume_24h: number;
  change_24h: number;
  change_percentage_24h: number;
  timestamp: number;
}

export type TimeInterval = '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

