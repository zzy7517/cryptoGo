# cryptoGo - 开发计划

基于大语言模型的智能加密货币交易系统

---

## 🏗️ 技术栈

**后端**: Python 3.11+ | FastAPI | CCXT | PostgreSQL | Redis  
**前端**: Next.js 14 | TypeScript | TailwindCSS | Lightweight Charts  
**AI**: LLM待定（可选GPT-4/Claude/本地模型）| LangChain（二期）

---

## 📁 项目结构

```
cryptoGo/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/         # API路由
│   │   ├── services/       # 业务逻辑（data_collector, ai_engine, trading_service）
│   │   ├── models/         # 数据库模型
│   │   ├── schemas/        # Pydantic schemas
│   │   └── utils/          # 工具函数
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js页面
│   │   ├── components/     # React组件
│   │   ├── lib/            # 工具库
│   │   └── stores/         # Zustand状态管理
│   └── package.json
│
└── docker-compose.yml
```

---

## 🎯 一期开发（MVP）

### 当前目标：CCXT数据 + K线图

**验收**: 能在前端看到BTC/USDT实时K线图，可切换时间周期

---

### Phase 1: 环境搭建

- [x] 创建项目结构
- [ ] Git仓库初始化
  ```bash
  git init
  git add .
  git commit -m "Initial commit"
  ```
- [ ] 创建 `.gitignore`
  ```
  __pycache__/
  *.pyc
  .env
  venv/
  node_modules/
  .next/
  ```
- [ ] 后端 `requirements.txt`
  ```
  fastapi==0.104.1
  uvicorn[standard]==0.24.0
  ccxt==4.1.0
  pandas==2.1.0
  python-dotenv==1.0.0
  sqlalchemy==2.0.0
  asyncpg==0.29.0
  redis==5.0.0
  apscheduler==3.10.4
  ```
- [ ] 前端 Next.js项目
  ```bash
  npx create-next-app@latest frontend --typescript --tailwind --app
  cd frontend
  npm install lightweight-charts axios @tanstack/react-query zustand
  ```

### Phase 2: CCXT数据采集 🔥

**2.1 环境配置**
- [ ] 创建 `backend/.env`
  ```bash
  # 交易所配置
  EXCHANGE=binance
  BINANCE_API_KEY=your_api_key_here
  BINANCE_SECRET=your_secret_here
  BINANCE_TESTNET=true  # 使用测试网
  
  # 默认交易对
  DEFAULT_SYMBOL=BTC/USDT
  ```

**2.2 交易所连接**
- [ ] 创建 `backend/app/services/data_collector.py`
- [ ] 实现 ExchangeConnector 类（币安）
- [ ] 测试连接

**2.3 K线数据获取**
- [ ] 获取历史K线（支持 1m/5m/15m/1h/4h/1d）
- [ ] 获取实时价格 ticker
- [ ] 数据标准化（OHLCV格式）

**2.4 后端API**
- [ ] 创建 `backend/app/api/v1/market.py`
- [ ] `GET /api/v1/market/klines?symbol=BTC/USDT&interval=1h&limit=100`
- [ ] `GET /api/v1/market/ticker/{symbol}` - 实时价格
- [ ] `GET /api/v1/market/symbols` - 交易对列表
- [ ] `GET /api/v1/market/stats/{symbol}` - 24h统计（可选）

**2.5 FastAPI基础**
- [ ] 创建 `backend/app/main.py`（CORS、路由注册、异常处理）
- [ ] 创建 `backend/app/core/config.py`（环境变量）
- [ ] 创建 Pydantic schemas（KlineResponse, TickerResponse）

### Phase 3: 前端K线图 🔥

**3.1 环境配置**
- [ ] 创建 `frontend/.env.local`
  ```bash
  NEXT_PUBLIC_API_URL=http://localhost:8000
  NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
  ```

**3.2 K线图组件**
- [ ] 创建 `CandlestickChart.tsx`（Lightweight Charts）
- [ ] 蜡烛图 + 成交量柱状图
- [ ] 实时K线更新（支持追加数据）
- [ ] 当前价格线（十字线）
- [ ] 缩放、拖拽、响应式

**3.3 状态管理**
- [ ] Market Store（Zustand）：klineData, currentSymbol, currentInterval
- [ ] React Query：自动刷新、错误处理

**3.4 交易页面**
- [ ] 创建 `frontend/src/app/trading/page.tsx`
- [ ] 交易对选择 + 时间周期切换
- [ ] 实时K线图展示
- [ ] 实时价格显示（大字体，醒目）
- [ ] 24h涨跌幅（百分比 + 绝对值）
- [ ] 实时成交量
- [ ] 最高价/最低价（24h）

**3.5 实时数据更新** 🔥
- [ ] 定时轮询（30秒或更短）更新K线数据
- [ ] 实时追加最新K线（不刷新整个图表）
- [ ] 当前价格线实时移动
- [ ] 价格闪烁动画（涨绿跌红）
- [ ] 最新成交量实时更新
- [ ] WebSocket推送（可选，后续优化）

### Phase 4: Docker环境（可选）

- [ ] 创建 docker-compose.yml
- [ ] PostgreSQL容器配置
- [ ] Redis容器配置
- [ ] 后端服务容器化（可选）
- [ ] 前端服务容器化（可选）

> 注：本地开发可直接用本机数据库，Docker可后续再配置

### Phase 5: 数据持久化

**5.1 数据库配置**
- [ ] 更新 `backend/.env`
  ```bash
  # 数据库配置
  DATABASE_URL=postgresql://postgres:password@localhost:5432/cryptogo
  REDIS_URL=redis://localhost:6379/0
  ```
- [ ] 本地安装PostgreSQL和Redis（或使用Docker）

**5.2 数据库设计**
- [ ] PostgreSQL Schema（klines, symbols, accounts, orders, positions, ai_decisions）
- [ ] Alembic迁移脚本
- [ ] K线数据入库
- [ ] 数据查询优化（索引）

### Phase 6: 定时任务

- [ ] APScheduler配置
- [ ] 定时采集K线（5分钟）
- [ ] 账户数据同步（1分钟）

### Phase 7: 简单AI决策（待定）

**7.1 LLM配置**
- [ ] 更新 `backend/.env`（根据选择的LLM）
  ```bash
  # AI配置 (选择一种)
  
  # 选项1: OpenAI
  # OPENAI_API_KEY=sk-xxx
  # OPENAI_MODEL=gpt-4-turbo
  
  # 选项2: Anthropic Claude
  # ANTHROPIC_API_KEY=sk-ant-xxx
  # ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
  
  # 选项3: 本地模型 (Ollama)
  # OLLAMA_BASE_URL=http://localhost:11434
  # OLLAMA_MODEL=llama2
  
  # 交易参数
  MAX_POSITION_SIZE=1000
  MAX_DAILY_TRADES=10
  RISK_PER_TRADE=0.02
  ```

**7.2 AI集成**
- [ ] LLM API配置（待选择：GPT-4/Claude/本地模型）
- [ ] 基础Prompt模板
- [ ] 结构化输出解析

**7.3 分析功能**
- [ ] 技术指标计算（MA, RSI, MACD）
- [ ] K线数据文本化（OHLCV数据 + 技术指标）
- [ ] LLM分析市场数据
- [ ] 生成交易信号（BUY/SELL/HOLD + 置信度 + 止损止盈）

**7.4 决策记录**
- [ ] 保存AI决策到数据库
- [ ] API查询历史决策
- [ ] 前端展示AI决策

**7.5 市场数据输入格式示例**
```
当前指标:
- Price: 113472.5
- EMA20: 113505.722
- MACD: -64.346
- RSI(7): 50.147

持仓数据:
- Open Interest: 29869.61 (均值: 29844.27)
- Funding Rate: 1.25e-05

分钟级时序数据 (最近10分钟):
- Mid Prices: [113554.5, 113574.5, 113543.5, 113418.0, 113354.5, 113401.5, 113428.0, 113474.0, 113387.0, 113472.5]
- EMA20: [113615.674, 113610.277, 113602.631, 113578.857, 113559.252, 113543.228, 113532.444, 113526.973, 113509.166, 113505.722]
- MACD: [-30.059, -31.082, -33.842, -49.739, -60.031, -65.975, -66.769, -63.04, -70.17, -64.346]
- RSI(7): [39.841, 44.766, 41.299, 26.62, 29.904, 33.051, 39.873, 47.126, 33.136, 50.147]
- RSI(14): [43.609, 46.15, 44.262, 34.885, 36.521, 38.031, 41.289, 44.889, 37.466, 46.799]

4小时级别背景:
- EMA20: 111283.106 vs EMA50: 110627.658
- ATR(3): 653.296 vs ATR(14): 685.181
- Volume: 8.04 vs Avg Volume: 4789.257
- MACD: [490.958, 552.679, 598.567, 613.498, 638.946, 650.006, 620.233, 631.799, 761.455, 879.887]
- RSI(14): [57.967, 60.329, 60.572, 59.128, 60.605, 60.424, 56.868, 60.273, 68.443, 69.78]
```

> 注：LLM选型待定，可根据需求选择不同模型

### Phase 8: 交易执行

**8.1 订单管理**
- [ ] 创建订单（市价/限价）
- [ ] 取消订单
- [ ] 订单状态追踪

**8.2 风控**
- [ ] 余额检查
- [ ] 单笔限额
- [ ] 日交易次数限制

**8.3 交易模式**
- [ ] 手动确认模式
- [ ] 模拟交易（Paper Trading）

### Phase 9: 前端完善

- [ ] Dashboard页面（资产、持仓、AI决策）
- [ ] History页面（交易历史、AI决策历史）
- [ ] Header/Sidebar布局
- [ ] shadcn/ui组件

### Phase 10: 测试部署

- [ ] 功能测试（数据采集、AI分析、交易）
- [ ] Docker Compose本地部署
- [ ] 测试网验证

---

## 🚀 二期开发

### Phase 11: 多智能体系统 ⭐（二期 - 需先确定LLM）

- [ ] 确定LLM选型和API
- [ ] LangChain Agent框架集成
- [ ] AnalystAgent（技术分析）
- [ ] SentimentAgent（新闻/社交媒体情绪）
- [ ] TraderAgent（综合决策）
- [ ] RiskAgent（风险管理）
- [ ] Multi-Agent协作机制

### Phase 12: 高级功能

- [ ] 自动交易模式
- [ ] 多币种支持
- [ ] 策略回测系统
- [ ] 网格交易
- [ ] TimescaleDB升级
- [ ] WebSocket实时推送
- [ ] Celery任务队列

### Phase 13: 生产优化

- [ ] 性能优化（数据库、Redis、CDN）
- [ ] 安全加固（API加密、签名验证、XSS/CSRF）
- [ ] 高可用（主从复制、负载均衡）
- [ ] 监控告警（Prometheus、Grafana、Sentry）
- [ ] 完整文档

---

**最后更新**: 2025-10-26
