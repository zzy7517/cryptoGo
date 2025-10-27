/**
 * 交易对配置 (Trading Pairs Configuration)
 * 
 * 文件作用：
 * - 配置前端展示的常用交易对列表
 * - 提供交易对的中文名称和描述信息
 * - 集中管理交易对配置，易于维护和扩展
 * 
 * 交易对格式说明：
 * - 格式：'BASE/QUOTE:SETTLE'
 * - 例如：'BTC/USDT:USDT'
 *   * BTC - 基础货币（Base Currency）
 *   * USDT - 报价货币（Quote Currency）
 *   * USDT - 结算货币（Settlement Currency）
 * - ':USDT' 表示这是永续合约（Perpetual Contract）
 * 
 * 当前配置的交易对：
 * - BTC/USDT:USDT - 比特币永续合约（最主流）
 * - ETH/USDT:USDT - 以太坊永续合约
 * - BNB/USDT:USDT - 币安币永续合约
 * - SOL/USDT:USDT - Solana永续合约
 * - XRP/USDT:USDT - 瑞波币永续合约
 * - DOGE/USDT:USDT - 狗狗币永续合约
 * - SUI/USDT:USDT - Sui永续合约
 * 
 * 如何添加新交易对？
 * 在 TRADING_PAIRS 数组中添加新对象即可：
 * { symbol: 'ADA/USDT:USDT', name: 'Cardano', description: 'Cardano 永续合约' }
 * 
 * 工具函数：
 * - getCoinName(symbol) - 根据交易对符号获取中文名称
 * - getTradingPairSymbols() - 获取所有交易对符号数组
 * 
 * 注意事项：
 * - 确保交易对在币安交易所存在
 * - 永续合约使用 ':USDT' 后缀
 * - 现货交易对使用 'BTC/USDT' 格式（无后缀）
 */

export interface TradingPairConfig {
  symbol: string;
  name: string;
  description?: string;
}

export const TRADING_PAIRS: TradingPairConfig[] = [
  { symbol: 'BTC/USDT:USDT', name: '比特币', description: 'Bitcoin 永续合约' },
  { symbol: 'ETH/USDT:USDT', name: '以太坊', description: 'Ethereum 永续合约' },
  { symbol: 'BNB/USDT:USDT', name: '币安币', description: 'Binance Coin 永续合约' },
  { symbol: 'SOL/USDT:USDT', name: 'Solana', description: 'Solana 永续合约' },
  { symbol: 'XRP/USDT:USDT', name: '瑞波币', description: 'Ripple 永续合约' },
  { symbol: 'DOGE/USDT:USDT', name: '狗狗币', description: 'Dogecoin 永续合约' },
  { symbol: 'SUI/USDT:USDT', name: 'Sui', description: 'Sui 永续合约' },
  // 可以根据需要添加更多合约交易对
  // { symbol: 'ADA/USDT:USDT', name: 'Cardano', description: 'Cardano 永续合约' },
  // { symbol: 'AVAX/USDT:USDT', name: 'Avalanche', description: 'Avalanche 永续合约' },
  // { symbol: 'DOT/USDT:USDT', name: 'Polkadot', description: 'Polkadot 永续合约' },
  // { symbol: 'MATIC/USDT:USDT', name: 'Polygon', description: 'Polygon 永续合约' },
  // { symbol: 'LINK/USDT:USDT', name: 'Chainlink', description: 'Chainlink 永续合约' },
];

/**
 * 获取币种中文名称
 */
export function getCoinName(symbol: string): string {
  const pair = TRADING_PAIRS.find(p => p.symbol === symbol);
  return pair?.name || '';
}

/**
 * 获取所有交易对符号列表
 */
export function getTradingPairSymbols(): string[] {
  return TRADING_PAIRS.map(p => p.symbol);
}

