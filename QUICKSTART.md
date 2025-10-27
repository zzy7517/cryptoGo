# CryptoGo - 快速启动指南

## 🎉 Phase 2 & Phase 3 已完成！

恭喜！CryptoGo 的核心功能已经实现完成，现在可以查看实时加密货币K线图了。

---

## 🚀 快速启动

### 1. 启动后端服务

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端 API 文档：http://localhost:8000/docs

### 2. 启动前端服务

在新的终端窗口：

```bash
cd frontend
npm run dev
```

前端访问地址：http://localhost:3000

---

## 📊 功能演示

### 主页
- 访问：http://localhost:3000
- 点击 "进入交易终端" 按钮

### 交易终端
- 访问：http://localhost:3000/trading
- 功能：
  - ✅ 实时BTC/USDT K线图
  - ✅ 可切换时间周期（1m/5m/15m/1h/4h/1d）
  - ✅ 实时价格显示（涨绿跌红动画）
  - ✅ 24小时统计数据
  - ✅ 订单簿（买一/卖一价）
  - ✅ 自动数据刷新
    - K线：30秒
    - 价格：5秒

### API 文档
- 访问：http://localhost:8000/docs
- Swagger UI 交互式 API 文档

---

## 🧪 测试 API

运行后端测试脚本：

```bash
cd backend
source venv/bin/activate
python test_api.py
```

---

## 📁 项目结构

```
cryptoGo/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 主应用
│   │   ├── core/           # 核心配置
│   │   ├── api/v1/         # API 路由
│   │   ├── services/       # 业务逻辑（数据采集）
│   │   ├── schemas/        # Pydantic 模型
│   │   └── models/         # 数据库模型（待实现）
│   ├── requirements.txt
│   └── test_api.py         # API 测试脚本
│
└── frontend/               # Next.js 前端
    ├── src/
    │   ├── app/           # 页面
    │   │   ├── page.tsx           # 主页
    │   │   ├── trading/page.tsx   # 交易页面
    │   │   └── providers.tsx      # React Query
    │   ├── components/    # React 组件
    │   │   └── CandlestickChart.tsx
    │   ├── lib/          # API 客户端
    │   ├── stores/       # Zustand 状态管理
    │   └── types/        # TypeScript 类型
    └── package.json
```

---

## 🎯 已实现功能

### ✅ Phase 1: 环境搭建
- Git 仓库初始化
- 后端 Python 环境
- 前端 Next.js 项目
- 依赖包安装

### ✅ Phase 2: CCXT 数据采集
- 币安交易所连接
- K线数据获取（多时间周期）
- 实时价格获取
- 交易对列表
- 市场统计数据
- RESTful API 接口

### ✅ Phase 3: 前端K线图
- Lightweight Charts 集成
- 专业级蜡烛图 + 成交量图
- Zustand 状态管理
- React Query 数据管理
- 实时数据自动刷新
- 响应式设计
- 价格变化动画

---

## 🔜 下一步开发

根据 TODO.md，接下来可以实现：

- **Phase 4**: Docker 环境（可选）
- **Phase 5**: 数据持久化（PostgreSQL）
- **Phase 6**: 定时任务
- **Phase 7**: AI 决策（LLM 集成）
- **Phase 8**: 交易执行
- **Phase 9**: 前端完善

---

## 💡 技术栈

**后端**
- FastAPI - 高性能 Web 框架
- CCXT - 加密货币交易所统一API
- Pydantic - 数据验证
- Uvicorn - ASGI 服务器

**前端**
- Next.js 14 - React 框架
- TypeScript - 类型安全
- TailwindCSS - 样式框架
- Lightweight Charts - 专业图表库
- Zustand - 状态管理
- React Query - 数据管理

---

## 📝 注意事项

1. **后端端口**: 8000
2. **前端端口**: 3000
3. **数据源**: 币安交易所（Binance）
4. **默认交易对**: BTC/USDT
5. **环境配置**: 确保 `backend/.env` 存在

---

## 🐛 问题排查

### 后端无法启动
- 检查 Python 虚拟环境是否激活
- 检查依赖是否安装：`pip install -r requirements.txt`
- 检查端口 8000 是否被占用

### 前端无法连接后端
- 确保后端服务运行在 http://localhost:8000
- 检查 `frontend/.env.local` 配置
- 检查浏览器控制台错误信息

### K线图不显示
- 检查后端 API 是否正常：访问 http://localhost:8000/api/v1/market/health
- 检查浏览器控制台网络请求
- 刷新页面

---

**祝你开发愉快！** 🚀

