import Link from "next/link";

export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-950">
      <main className="flex flex-col items-center justify-center gap-8 text-center px-4">
        <div className="space-y-4">
          <h1 className="text-6xl font-bold text-white">
            Crypto<span className="text-blue-500">Go</span>
          </h1>
          <p className="text-xl text-gray-400">
            基于大语言模型的智能加密货币交易系统
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <Link
            href="/trading"
            className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
          >
            进入交易终端
          </Link>
          <a
            href="http://localhost:9527/docs"
            target="_blank"
            rel="noopener noreferrer"
            className="px-8 py-3 bg-gray-800 hover:bg-gray-700 text-white rounded-lg font-semibold transition-colors"
          >
            查看 API 文档
          </a>
        </div>

        <div className="mt-12 grid grid-cols-1 sm:grid-cols-3 gap-6 max-w-3xl">
          <div className="bg-gray-900 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-white mb-2">实时数据</h3>
            <p className="text-gray-400 text-sm">
              通过 CCXT 连接币安交易所，获取实时K线和价格数据
            </p>
          </div>
          <div className="bg-gray-900 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-white mb-2">智能分析</h3>
            <p className="text-gray-400 text-sm">
              集成大语言模型进行市场分析和交易决策（即将推出）
            </p>
          </div>
          <div className="bg-gray-900 p-6 rounded-lg">
            <h3 className="text-lg font-semibold text-white mb-2">可视化</h3>
            <p className="text-gray-400 text-sm">
              使用 Lightweight Charts 提供专业级K线图表
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
