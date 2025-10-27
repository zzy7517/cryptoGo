# CryptoGo

基于大语言模型的智能加密货币交易系统

## 🏗️ 技术栈

**后端**: Python 3.11+ | FastAPI | CCXT | PostgreSQL | Redis  
**前端**: Next.js 14 | TypeScript | TailwindCSS | Lightweight Charts  
**AI**: LLM 待定（可选 GPT-4/Claude/本地模型）| LangChain（二期）

## 📁 项目结构

```
cryptoGo/
├── backend/           # FastAPI 后端
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/    # API 路由
│   │   ├── services/  # 业务逻辑
│   │   ├── models/    # 数据库模型
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── utils/     # 工具函数
│   │   └── core/      # 核心配置
│   └── requirements.txt
│
├── frontend/          # Next.js 前端
│   ├── src/
│   │   ├── app/       # Next.js 页面
│   │   ├── components/# React 组件
│   │   ├── lib/       # 工具库
│   │   └── stores/    # Zustand 状态管理
│   └── package.json
│
└── TODO.md           # 开发计划
```

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
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 API 文档：http://localhost:8000/docs

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

访问应用：http://localhost:3000

## 📋 开发计划

详见 [TODO.md](./TODO.md)

当前进度：**Phase 1 已完成** ✅

下一步：Phase 2 - CCXT 数据采集

## 📄 License

MIT

