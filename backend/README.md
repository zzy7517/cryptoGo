# CryptoGo Backend

基于 FastAPI 的加密货币交易系统后端

## 安装

1. 创建虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 配置环境变量：
```bash
cp .env.example .env
# 编辑 .env 文件，填入实际配置
```

## 运行

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问：http://localhost:8000/docs

