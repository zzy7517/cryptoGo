# CryptoGo - 快速启动指南

## 🚀 启动命令

### 1. 启动后端服务

```bash
cd backend
source venv/bin/activate
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

---

## 🧪 测试 API（可选）

```bash
cd backend
source venv/bin/activate
python test_api.py
```

