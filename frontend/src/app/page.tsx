/**
 * 首页组件 (Home Page)
 * 
 * 文件作用：
 * - 项目首页/欢迎页面
 * - 展示项目介绍和核心特性
 * - 提供导航入口（市场看板、开始交易）
 * 
 * 路由：
 * - 访问路径: /
 * 
 * 功能：
 * - 展示 CryptoGo 品牌和标语
 * - 展示三大核心特性：实时数据、智能分析、可视化
 * - 提供市场看板和开始交易的按钮链接
 */
import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50">
      <main className="flex flex-col items-center justify-center gap-10 text-center px-4">
        <div className="space-y-6">
          <h1 className="text-7xl font-bold bg-gradient-to-r from-teal-600 via-cyan-600 to-teal-500 bg-clip-text text-transparent">
            Crypto<span className="text-teal-600">Go</span>
          </h1>
          <p className="text-2xl text-gray-600 font-light max-w-2xl">
            基于大语言模型的智能加密货币交易系统
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <Link
            href="/trading"
            className="px-10 py-4 bg-white hover:bg-gray-50 text-gray-700 rounded-lg font-semibold transition-all shadow-sm hover:shadow-md border border-gray-300"
          >
            市场看板
          </Link>
          <Link
            href="/trading?startSession=true"
            className="px-10 py-4 bg-gradient-to-r from-teal-500 to-cyan-600 hover:from-teal-600 hover:to-cyan-700 text-white rounded-lg font-semibold transition-all shadow-sm hover:shadow-md"
          >
            开始交易
          </Link>
        </div>

        <div className="mt-16 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-4xl">
          <div className="bg-white p-8 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200">
            <div className="w-12 h-12 bg-gradient-to-br from-teal-400 to-cyan-500 rounded-lg mb-4 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-800 mb-3">实时数据</h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              通过 CCXT 连接币安交易所，获取实时K线和价格数据
            </p>
          </div>
          <div className="bg-white p-8 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200">
            <div className="w-12 h-12 bg-gradient-to-br from-cyan-400 to-teal-500 rounded-lg mb-4 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-800 mb-3">智能分析</h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              集成大语言模型进行市场分析和交易决策
            </p>
          </div>
          <div className="bg-white p-8 rounded-lg shadow-sm hover:shadow-md transition-shadow border border-gray-200">
            <div className="w-12 h-12 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-lg mb-4 flex items-center justify-center">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
              </svg>
            </div>
            <h3 className="text-xl font-bold text-gray-800 mb-3">可视化</h3>
            <p className="text-gray-600 text-sm leading-relaxed">
              使用 Lightweight Charts 提供专业级K线图表
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
