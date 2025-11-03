# CryptoGo

> 🚀 基于 LLM 的加密货币智能交易系统

一个专注于 LLM 驱动的智能交易决策和持仓管理的加密货币自动交易系统，采用大语言模型进行市场分析，实现自动化交易决策。

## 🎯 核心特性

### 🤖 AI 智能决策引擎
- **大语言模型集成**：采用 LLM 进行深度市场分析和交易决策
- **多维度数据分析**：综合技术指标（EMA、MACD、RSI、ATR）、市场情绪、资金费率等
- **智能决策输出**：AI 自动判断市场趋势，输出做多/做空/观望建议及置信度评分
- **自动循环执行**：后台 Agent 定时循环进行市场分析和交易决策

### 📊 交易会话管理
- **会话化运行**：通过前端界面创建和管理交易会话（Session）
- **自动化执行**：AI Agent 在会话期间持续监控市场，自动完成交易决策和执行
- **灵活控制**：支持随时启动/停止 Agent，或结束整个交易会话

### 💼 实时监控与追踪
- **持仓监控**：实时查看所有持仓情况，包括多空方向、盈亏状态
- **决策历史**：完整追踪 AI 决策记录，包括决策理由、置信度等详细信息
- **资金追踪**：监控账户资金变化，生成账户快照

## 🛠️ 技术栈

### 后端
- **框架**：FastAPI + Uvicorn
- **数据库**：SQLite（默认）/ PostgreSQL（可选）
- **交易所集成**：币安
- **LLM**：OpenAI SDK 

### 前端
- **框架**：Next.js 16 + React 19
- **状态管理**：Zustand
- **数据获取**：TanStack Query (React Query)
- **样式**：Tailwind CSS
- **HTTP 客户端**：Axios

## 🚀 快速开始

> 💡 **推荐使用 Docker 部署**：一键启动所有服务，环境隔离更安全！
> 📖 查看详细说明：[Docker 部署指南](./docker/README.md)

### 前置要求

- Python 3.11+
- Node.js 18+
- 币安账户 API Key (测试网或主网)
- DeepSeek API Key

> 💡 **零配置数据库**：默认使用 SQLite 文件数据库，无需安装 PostgreSQL！

### 后端设置

1. **进入后端目录并创建虚拟环境**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # Windows: venv\Scripts\activate
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **配置环境变量**
   ```bash
   cp .env.example .env
   ```

   编辑 `.env` 文件，配置以下关键参数：
   ```env
   # 数据库配置（可选，默认使用 SQLite）
   # DATABASE_URL=sqlite:///./data/trading.db  # 默认值，无需配置
   # DATABASE_URL=postgresql://user:password@host:port/dbname  # 如需使用 PostgreSQL

   # 币安 API
   BINANCE_API_KEY=your_api_key
   BINANCE_API_SECRET=your_api_secret
   BINANCE_TESTNET=true  # 测试网模式

   # AI 配置
   DEEPSEEK_API_KEY=your_deepseek_key
   ```

4. **启动后端服务**
   ```bash
   cd backend
   uvicorn app.main:app --reload --host 0.0.0.0 --port 9527
   ```

   访问 API 文档: http://localhost:9527/docs

### 前端设置

1. **进入前端目录**
   ```bash
   cd frontend
   ```

2. **安装依赖**
   ```bash
   npm install
   ```

3. **启动开发服务器**
   ```bash
   npm run dev
   ```

### 访问应用

- **前端界面**: http://localhost:3000

## 💾 数据库说明

### 为什么选择 SQLite？

本项目默认使用 **SQLite** 作为数据库，原因如下：

- ✅ **零配置**：无需安装数据库服务器，开箱即用
- ✅ **简单部署**：数据库文件随项目一起，方便备份和迁移
- ✅ **性能足够**：对于个人交易机器人的数据量完全够用
- ✅ **完全兼容**：SQLAlchemy ORM 完美支持，代码无差异
- ✅ **成本更低**：无需外部数据库服务，降低运维成本

### 数据库文件位置

- **SQLite 数据库**：`backend/data/trading.db`
- **Schema 文件**：`backend/schema.sqlite.sql`（参考用）

### 切换到 PostgreSQL（可选）

如果需要使用 PostgreSQL（适合多用户或高并发场景），只需修改环境变量：

```env
DATABASE_URL=postgresql://user:password@host:port/dbname
```

代码无需任何修改！

## 📁 项目结构

```
cryptoGo/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API 路由
│   │   ├── core/           # 核心配置
│   │   ├── db/             # 数据库模型和连接
│   │   ├── exchanges/      # 交易所集成 (工厂模式)
│   │   ├── repositories/   # 数据访问层
│   │   ├── schemas/        # Pydantic 模型
│   │   └── services/       # 业务逻辑层
│   ├── data/               # SQLite 数据库文件目录
│   ├── requirements.txt
│   └── .env.example
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── app/           # Next.js 页面
│   │   ├── components/    # React 组件
│   │   ├── lib/           # 工具库
│   │   └── stores/        # 状态管理
│   ├── package.json
│   └── .env.example
└── README.md
```

## 🎮 使用指南

1. **启动系统**：分别启动后端和前端服务
2. **创建会话**：在前端交易页面点击"开始交易"创建新会话
3. **启动 Agent**：点击"启动 Agent"开始 AI 自动交易
4. **监控运行**：实时查看持仓、决策历史和账户变化
5. **停止交易**：随时停止 Agent 或结束整个会话

## 🐳 Docker 部署

推荐使用 Docker 进行部署，一键启动所有服务：

```bash
cd docker
docker-compose up -d --build
```

**详细部署指南**：[Docker 部署文档](./docker/README.md)

部署文档包含：
- 完整的 Docker 配置说明
- 低成本服务器推荐（最低 ¥62/年）
- 生产环境优化建议
- 故障排查指南

## 📋 开发计划

详细的开发任务和进度请查看 [TODO.md](./TODO.md)

## ⚠️ 风险提示

- 本项目仅供学习和研究使用
- 加密货币交易存在高风险，请谨慎使用
- 建议先在测试网环境充分测试
- 使用真实资金前请确保理解所有风险
- 作者不对任何交易损失负责

## 🙏 致谢

感谢以下开源项目的启发和帮助：

- [nofx](https://github.com/tinkle-community/nofx) - 
- [AI-Trader](https://github.com/HKUDS/AI-Trader) - AI 驱动的金融市场交易系统

