# CryptoGo Docker 部署指南

## 📋 目录结构

```
docker/
├── backend.Dockerfile         # 后端镜像构建文件
├── frontend.Dockerfile        # 前端镜像构建文件
├── docker-compose.yml         # Docker Compose 编排文件
├── PUBLIC_ACCESS_GUIDE.md     # 公网访问配置指南
└── README.md                  # 本文档
```

## 🚀 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 1. 配置环境变量

在项目根目录创建 `.env` 文件：

```bash
# 数据库配置（可选，默认使用 SQLite）
# DATABASE_URL=sqlite:///./data/trading.db  # 默认值，无需配置
# DATABASE_URL=postgresql://user:password@host:port/dbname  # 如需使用 PostgreSQL

# 币安 API 配置
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
BINANCE_TESTNET=true

# AI 配置
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_BASE=https://api.deepseek.com

# 前端配置
NEXT_PUBLIC_API_URL=http://localhost:9527
```

> 💡 **零配置数据库**：默认使用 SQLite，数据存储在 `backend/data/trading.db`，无需外部数据库！

### 2. 构建并启动服务

```bash
cd docker
docker-compose up -d --build
```

### 3. 查看服务状态

```bash
docker-compose ps
docker-compose logs -f
```

### 4. 访问应用

- 前端: http://localhost:3000
- 后端 API: http://localhost:9527
- API 文档: http://localhost:9527/docs

## 🛠️ 常用命令

### 启动服务
```bash
docker-compose up -d
```

### 停止服务
```bash
docker-compose down
```

### 重启服务
```bash
docker-compose restart
```

### 查看日志
```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 重新构建镜像
```bash
docker-compose up -d --build
```

### 进入容器
```bash
# 进入后端容器
docker exec -it cryptogo-backend /bin/bash

# 进入前端容器
docker exec -it cryptogo-frontend /bin/sh
```

## 🔧 服务器部署步骤

### 1. 连接服务器
```bash
ssh root@your-server-ip
```

### 2. 安装 Docker
```bash
# 使用官方脚本安装
curl -fsSL https://get.docker.com | sh

# 启动 Docker
systemctl start docker
systemctl enable docker

# 安装 Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

### 3. 上传项目
```bash
# 方式 1: 使用 Git
git clone https://github.com/your-repo/cryptoGo.git
cd cryptoGo

# 方式 2: 使用 scp
scp -r /path/to/cryptoGo root@your-server-ip:/root/
```

### 4. 配置环境变量
```bash
cd cryptoGo
nano .env  # 或使用 vim 编辑
```

### 5. 启动服务
```bash
cd docker
docker-compose up -d --build
```

### 6. 配置防火墙 (如需要)
```bash
# 允许端口访问
firewall-cmd --permanent --add-port=3000/tcp
firewall-cmd --permanent --add-port=9527/tcp
firewall-cmd --reload
```

## 🔒 生产环境优化建议

### 1. 使用 Nginx 反向代理

```bash
# 安装 Nginx
apt install nginx -y

# 配置示例 /etc/nginx/sites-available/cryptogo
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:9527;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. 配置 HTTPS (Let's Encrypt)

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx -y

# 获取证书
certbot --nginx -d your-domain.com
```

### 3. 设置自动重启

在 `docker-compose.yml` 中已配置 `restart: unless-stopped`

### 4. 日志管理

```bash
# 限制日志大小
docker-compose down
# 编辑 docker-compose.yml 添加日志配置
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🐛 故障排查

### 问题 1: 容器无法启动
```bash
# 查看容器日志
docker-compose logs backend
docker-compose logs frontend
```

### 问题 2: 数据库连接失败
- **SQLite** (默认)：检查 `backend/data` 目录是否可写
- **PostgreSQL** (可选)：检查 `.env` 中的 `DATABASE_URL` 配置

### 问题 3: 前端无法访问后端
- 检查 `NEXT_PUBLIC_API_URL` 配置
- 生产环境应使用公网 IP 或域名

### 问题 4: 端口被占用
```bash
# 查看端口占用
lsof -i :3000
lsof -i :9527

# 修改 docker-compose.yml 中的端口映射
```

## 📈 性能监控

### 查看容器资源使用
```bash
docker stats
```

### 使用 Portainer 可视化管理
```bash
docker run -d -p 9000:9000 \
  --name=portainer \
  --restart=always \
  -v /var/run/docker.sock:/var/run/docker.sock \
  portainer/portainer-ce
```
