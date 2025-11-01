# CryptoGo

vibe trading

## 项目介绍

**CryptoGo** 是一个基于 AI 的加密货币自动交易系统，专注于AI驱动的智能交易决策和持仓管理。

### 🎯 核心特性

#### 🤖 AI 智能决策引擎
- **集成 DeepSeek AI**：采用先进的大语言模型进行市场分析和交易决策
- **多维度数据分析**：综合技术指标（EMA、MACD、RSI、ATR）、市场情绪、资金费率等多维度数据
- **智能决策逻辑**：AI 自动判断市场趋势，给出做多/做空/观望建议，并评估交易置信度
- **定时循环执行**：后台Agent定时循环进行市场分析和交易决策

#### 📊 交易会话管理
- **会话化运行**：用户通过前端页面点击"开始交易"按钮，创建一个新的交易会话（Session）
- **自动化执行**：会话期间，AI Agent持续监控市场，自动完成交易决策和执行
- **灵活控制**：用户可随时启动/停止Agent，或结束整个交易会话

#### 💼 持仓与决策监控
- **实时持仓监控**：查看当前所有持仓情况，包括多空方向、盈亏状态
- **AI决策历史**：追踪所有AI决策记录，包括决策理由、置信度等
- **资金变化追踪**：监控账户资金的变化情况

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

## 📋 开发计划
[TODO.md](./TODO.md)


## 🙏 Acknowledgments

感谢以下开源项目对本项目的启发和帮助：

- [nofx](https://github.com/tinkle-community/nofx) - 
- [AI-Trader](https://github.com/HKUDS/AI-Trader) - AI驱动的金融市场交易系统


## 📄 License

MIT

