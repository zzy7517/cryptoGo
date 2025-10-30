# CryptoGo

vibe trading

## 项目介绍

**CryptoGo** 是一个基于 AI 的加密货币自动交易系统，

### 🎯 核心特性

#### 🤖 AI 智能决策引擎
- **集成 DeepSeek AI**：采用先进的大语言模型进行市场分析和交易决策
- **多维度数据分析**：综合技术指标（EMA、MACD、RSI、ATR）、市场情绪、资金费率等多维度数据
- **智能决策逻辑**：AI 自动判断市场趋势，给出做多/做空/观望建议，并评估交易置信度

#### 📊 交易会话管理
- **会话化运行**：用户通过前端页面点击"开始"按钮，创建一个新的交易会话（Session）
- **自动化执行**：会话期间，AI 持续监控市场，自动完成交易决策和执行
- **灵活控制**：用户可随时点击"结束"按钮终止当前会话，系统自动生成交易报告

#### 📈 实时市场监控
- **多交易对支持**：支持 BTC、ETH、SOL 等主流加密货币
- **实时行情数据**：集成 CCXT 获取 Binance 等交易所实时数据
- **技术指标计算**：自动计算并展示关键技术指标

## 🚀 快速开始

### 后端设置

1. 进入后端目录：
```bash
cd backend
```

2. 创建虚拟环境并安装依赖：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

4. 运行后端服务：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 9527
```

访问 API 文档：http://localhost:9527/docs

### 前端设置

1. 进入前端目录：
```bash
cd frontend
```

2. 安装依赖：
```bash
npm install
```

3. 配置环境变量：
```bash
cp .env.example .env.local
# 根据需要修改 API 地址
```

4. 运行开发服务器：
```bash
npm run dev
```

## 📦 启动服务

### 1. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 9527
```

### 2. 启动前端服务

新开终端窗口：

```bash
cd frontend
npm run dev
```

### 3. 访问地址

- **主页**: http://localhost:3000
- **交易终端**: http://localhost:3000/trading
- **API 文档**: http://localhost:9527/docs

## 📋 开发计划
[TODO.md](./TODO.md)


## 📄 License

MIT

