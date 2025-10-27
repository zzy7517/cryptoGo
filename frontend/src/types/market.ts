/**
 * 市场数据类型定义 (Market Data Types)
 * 
 * 文件作用：
 * - 定义所有市场数据相关的 TypeScript 类型
 * - 确保前后端数据结构一致性
 * - 提供完整的类型安全和智能提示
 * 
 * 类型分类：
 * 
 * 1. K线数据 (Candlestick Data)
 *    - KlineData: 单根K线的OHLCV数据
 *    - KlineResponse: API返回的K线数据响应
 * 
 * 2. 实时行情 (Ticker Data)
 *    - TickerData: 实时价格、涨跌幅、成交量等
 * 
 * 3. 交易对信息 (Symbol Info)
 *    - SymbolInfo: 交易对的基本信息
 *    - SymbolListResponse: 交易对列表响应
 * 
 * 4. 合约数据 (Contract Data)
 *    - FundingRateData: 资金费率
 *    - OpenInterestData: 持仓量
 * 
 * 5. 技术指标 (Technical Indicators)
 *    - IndicatorLatestValues: 最新指标值（EMA、MACD、RSI、ATR）
 *    - IndicatorSeriesData: 指标时间序列数据
 *    - IndicatorsResponse: API返回的指标响应
 * 
 * 6. 时间周期 (Time Interval)
 *    - TimeInterval: 支持的K线时间周期类型
 * 
 * 数据字段说明：
 * - timestamp: Unix时间戳（毫秒）
 * - open/high/low/close: OHLC价格
 * - volume: 成交量
 * - bid/ask: 买一价/卖一价
 * - change: 价格变化量
 * - percentage: 涨跌幅百分比
 * - funding_rate: 资金费率（正数=多头付费，负数=空头付费）
 * - open_interest: 未平仓合约数量
 * 
 * null 值说明：
 * - 某些字段可能为 null（如现货市场没有资金费率）
 * - 使用时需要做 null 检查
 * 
 * 使用示例：
 * const kline: KlineData = {
 *   timestamp: 1698765432000,
 *   open: 43250.5,
 *   high: 43500.0,
 *   low: 43200.0,
 *   close: 43450.0,
 *   volume: 123.45
 * };
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

export interface FundingRateData {
  symbol: string;
  funding_rate: number | null;
  next_funding_time: number | null;
  timestamp: number;
}

export interface OpenInterestData {
  symbol: string;
  open_interest: number | null;
  timestamp: number;
}

export interface IndicatorLatestValues {
  ema20: number;
  ema50: number;
  macd: number;
  signal: number;
  histogram: number;
  rsi7: number;
  rsi14: number;
  atr3: number;
  atr14: number;
}

export interface IndicatorSeriesData {
  timestamps: number[];
  ema20: number[];
  ema50: number[];
  macd: number[];
  signal: number[];
  histogram: number[];
  rsi7: number[];
  rsi14: number[];
  atr3: number[];
  atr14: number[];
}

export interface IndicatorsResponse {
  symbol: string;
  interval: string;
  latest_values: IndicatorLatestValues;
  series_data?: IndicatorSeriesData;
}

export type TimeInterval = '1m' | '5m' | '15m' | '1h' | '4h' | '1d';

