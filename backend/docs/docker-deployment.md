# Docker 部署指南

## 概述

本文档提供了 JJCrawler3 晋江文学城爬虫后端服务的完整 Docker 部署指南，包括 Linux 服务器生产环境部署。

## 目录

1. [Docker 环境准备](#docker-环境准备)
2. [创建 Dockerfile](#创建-dockerfile)
3. [Docker Compose 配置](#docker-compose-配置)
4. [构建和部署](#构建和部署)
5. [生产环境配置](#生产环境配置)
6. [监控和维护](#监控和维护)
7. [故障排除](#故障排除)

## Docker 环境准备

### 系统要求

- **操作系统**: Ubuntu 20.04+ / CentOS 7+ / Debian 10+
- **内存**: 最少 2GB，推荐 4GB+
- **存储**: 最少 10GB 可用空间
- **CPU**: 2 核心+

### 安装 Docker

#### Ubuntu/Debian 系统

```bash
# 更新包索引
sudo apt update

# 安装必要包
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker
```

#### CentOS/RHEL 系统

```bash
# 安装必要包
sudo yum install -y yum-utils

# 添加 Docker 仓库
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

# 安装 Docker
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker 服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 安装 Docker Compose

```bash
# 下载 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# 设置执行权限
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker-compose --version
```

### 配置用户权限

```bash
# 将当前用户添加到 docker 组
sudo usermod -aG docker $USER

# 重新登录或执行以下命令使权限生效
newgrp docker

# 验证权限
docker run hello-world
```

## 创建 Dockerfile

在项目根目录创建 `Dockerfile`：

```dockerfile
# 使用官方 Python 3.11 运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 Poetry
RUN pip install poetry==1.6.1

# 配置 Poetry
RUN poetry config virtualenvs.create false

# 复制项目依赖文件
COPY pyproject.toml poetry.lock ./

# 安装 Python 依赖
RUN poetry install --only=main --no-dev

# 复制应用代码
COPY app/ ./app/
COPY data/ ./data/

# 创建必要目录
RUN mkdir -p /app/data/tasks/history && \
    mkdir -p /app/logs

# 设置数据目录权限
RUN chmod -R 755 /app/data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

## Docker Compose 配置

创建 `docker-compose.yml` 文件：

```yaml
version: '3.8'

services:
  jjcrawler:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: jjcrawler
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      # 数据持久化
      - ./data:/app/data
      - ./logs:/app/logs
      # 配置文件挂载
      - ./.env:/app/.env:ro
    environment:
      # 基础配置
      - PROJECT_NAME=JJCrawler3
      - DEBUG=false
      - LOG_LEVEL=INFO
      
      # 数据库配置
      - DATABASE_URL=sqlite:///./data/jjcrawler.db
      
      # 爬虫配置
      - CRAWL_DELAY=1.0
      - REQUEST_TIMEOUT=30
      - MAX_RETRIES=3
      
      # 调度器配置
      - SCHEDULER_TIMEZONE=Asia/Shanghai
      - JIAZI_SCHEDULE=0 */1 * * *
      - RANKING_SCHEDULE=0 0 * * *
      
      # 文件路径配置
      - DATA_DIR=/app/data
      - TASKS_FILE=/app/data/tasks/tasks.json
      - URLS_CONFIG_FILE=/app/data/urls.json
    
    # 资源限制
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
    
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    # 日志配置
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  # Nginx 反向代理 (可选)
  nginx:
    image: nginx:alpine
    container_name: jjcrawler-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    depends_on:
      - jjcrawler
    profiles:
      - production

networks:
  default:
    name: jjcrawler-network
```

## 构建和部署

### 本地构建测试

```bash
# 构建镜像
docker build -t jjcrawler:latest .

# 查看镜像
docker images

# 运行容器 (开发模式)
docker run -d \
  --name jjcrawler-dev \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env:ro \
  jjcrawler:latest

# 查看日志
docker logs -f jjcrawler-dev

# 测试服务
curl http://localhost:8000/health
```

### 使用 Docker Compose 部署

```bash
# 创建环境变量文件
cp .env.example .env

# 编辑配置 (根据实际环境调整)
vim .env

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f jjcrawler

# 停止服务
docker-compose down
```

### 生产环境部署脚本

创建 `deploy.sh` 脚本：

```bash
#!/bin/bash

set -e

echo "开始部署 JJCrawler3..."

# 创建必要目录
mkdir -p data/tasks/history logs nginx/ssl

# 设置目录权限
chmod -R 755 data logs

# 检查配置文件
if [ ! -f .env ]; then
    echo "错误: .env 文件不存在，请先创建配置文件"
    exit 1
fi

# 构建镜像
echo "构建 Docker 镜像..."
docker-compose build --no-cache

# 停止旧容器
echo "停止现有服务..."
docker-compose down

# 启动新容器
echo "启动新服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 30

# 健康检查
echo "执行健康检查..."
if curl -f http://localhost:8000/health; then
    echo "✅ 部署成功！服务运行正常"
else
    echo "❌ 部署失败！服务健康检查未通过"
    docker-compose logs jjcrawler
    exit 1
fi

echo "部署完成！"
```

```bash
# 设置执行权限
chmod +x deploy.sh

# 执行部署
./deploy.sh
```

## 生产环境配置

### 环境变量配置

创建生产环境 `.env` 文件：

```env
# 生产环境配置
PROJECT_NAME=JJCrawler3
VERSION=1.0.0
DEBUG=false

# API 配置
API_V1_STR=/api/v1

# 数据库配置
DATABASE_URL=sqlite:///./data/jjcrawler.db

# 爬虫配置
CRAWL_DELAY=2.0
REQUEST_TIMEOUT=60
MAX_RETRIES=5

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# 任务调度配置
SCHEDULER_TIMEZONE=Asia/Shanghai
JIAZI_SCHEDULE=0 */1 * * *
RANKING_SCHEDULE=0 2 * * *

# 文件路径配置
DATA_DIR=/app/data
TASKS_FILE=/app/data/tasks/tasks.json
URLS_CONFIG_FILE=/app/data/urls.json
```

### Nginx 反向代理配置

创建 `nginx/nginx.conf`：

```nginx
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
    use epoll;
    multi_accept on;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # 日志格式
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    # 性能优化
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # 上游服务器
    upstream jjcrawler {
        server jjcrawler:8000;
        keepalive 32;
    }

    # HTTP 服务器配置
    server {
        listen 80;
        server_name localhost;

        # 安全头
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";

        # API 代理
        location / {
            proxy_pass http://jjcrawler;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # 超时设置
            proxy_connect_timeout 30s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # 缓冲设置
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 4k;
        }

        # 健康检查端点
        location /health {
            proxy_pass http://jjcrawler/health;
            access_log off;
        }

        # 静态文件缓存
        location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
```

### 系统服务配置

创建 systemd 服务文件 `/etc/systemd/system/jjcrawler.service`：

```ini
[Unit]
Description=JJCrawler3 Docker Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/jjcrawler
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
ExecReload=/usr/local/bin/docker-compose restart
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# 启用和启动服务
sudo systemctl daemon-reload
sudo systemctl enable jjcrawler.service
sudo systemctl start jjcrawler.service

# 检查服务状态
sudo systemctl status jjcrawler.service
```

## 监控和维护

### 容器监控脚本

创建 `monitor.sh`：

```bash
#!/bin/bash

# 容器健康检查
check_container_health() {
    local container_name=$1
    local status=$(docker inspect --format='{{.State.Health.Status}}' $container_name 2>/dev/null)
    
    if [ "$status" = "healthy" ]; then
        echo "✅ $container_name: 健康"
        return 0
    else
        echo "❌ $container_name: 不健康 ($status)"
        return 1
    fi
}

# 检查服务状态
check_service_status() {
    echo "=== JJCrawler3 服务状态检查 ==="
    echo "时间: $(date)"
    echo
    
    # 检查容器状态
    echo "📋 容器状态:"
    docker-compose ps
    echo
    
    # 健康检查
    echo "🏥 健康检查:"
    check_container_health "jjcrawler"
    
    # 资源使用情况
    echo
    echo "📊 资源使用:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
    
    # API 健康检查
    echo
    echo "🌐 API 健康检查:"
    if curl -s -f http://localhost:8000/health > /dev/null; then
        echo "✅ API 服务正常"
    else
        echo "❌ API 服务异常"
    fi
}

# 日志管理
manage_logs() {
    echo "📝 最近日志 (最后 50 行):"
    docker-compose logs --tail 50 jjcrawler
    
    # 清理旧日志
    docker system prune -f --filter "until=72h"
}

# 数据备份
backup_data() {
    local backup_dir="/backup/jjcrawler/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    echo "💾 创建数据备份: $backup_dir"
    cp -r data/ "$backup_dir/"
    tar -czf "$backup_dir.tar.gz" "$backup_dir/"
    rm -rf "$backup_dir"
    
    echo "✅ 备份完成: $backup_dir.tar.gz"
}

# 主函数
main() {
    case "$1" in
        "status")
            check_service_status
            ;;
        "logs")
            manage_logs
            ;;
        "backup")
            backup_data
            ;;
        "restart")
            echo "🔄 重启服务..."
            docker-compose restart
            sleep 10
            check_service_status
            ;;
        *)
            echo "用法: $0 {status|logs|backup|restart}"
            exit 1
            ;;
    esac
}

main "$@"
```

### 定时监控和备份

添加 crontab 任务：

```bash
# 编辑 crontab
crontab -e

# 添加以下任务
# 每 5 分钟检查服务状态
*/5 * * * * /opt/jjcrawler/monitor.sh status >> /var/log/jjcrawler-monitor.log 2>&1

# 每天凌晨 3 点备份数据
0 3 * * * /opt/jjcrawler/monitor.sh backup >> /var/log/jjcrawler-backup.log 2>&1

# 每周清理旧备份 (保留 30 天)
0 4 * * 0 find /backup/jjcrawler -name "*.tar.gz" -mtime +30 -delete
```

## 故障排除

### 常见问题解决

#### 1. 容器启动失败

```bash
# 查看详细错误信息
docker-compose logs jjcrawler

# 检查配置文件
docker-compose config

# 重新构建镜像
docker-compose build --no-cache
```

#### 2. 端口占用问题

```bash
# 检查端口占用
netstat -tulpn | grep 8000

# 停止占用端口的进程
sudo fuser -k 8000/tcp

# 或修改 docker-compose.yml 中的端口映射
```

#### 3. 权限问题

```bash
# 检查文件权限
ls -la data/

# 修复权限
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

#### 4. 内存不足

```bash
# 检查内存使用
free -h
docker stats

# 调整资源限制
# 编辑 docker-compose.yml 中的 deploy.resources 部分
```

#### 5. 网络连接问题

```bash
# 检查网络配置
docker network ls
docker network inspect jjcrawler-network

# 重建网络
docker-compose down
docker network prune
docker-compose up -d
```

### 日志分析

#### 查看实时日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f jjcrawler

# 查看最近的错误日志
docker-compose logs --tail 100 jjcrawler | grep ERROR
```

#### 日志级别配置

在 `.env` 文件中调整日志级别：

```env
# 调试模式
LOG_LEVEL=DEBUG

# 生产模式
LOG_LEVEL=INFO

# 仅错误日志
LOG_LEVEL=ERROR
```

### 性能优化

#### 1. 镜像优化

```dockerfile
# 使用多阶段构建减小镜像大小
FROM python:3.11-slim as builder
WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt > requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY data/ ./data/
```

#### 2. 资源限制调优

```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '2.0'
    reservations:
      memory: 1G
      cpus: '1.0'
```

#### 3. 数据库性能优化

```bash
# 定期清理和优化数据库
docker-compose exec jjcrawler python -c "
from app.modules.database import optimize_database
optimize_database()
"
```

### 安全加固

#### 1. 容器安全

```dockerfile
# 使用非 root 用户运行
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
```

#### 2. 网络安全

```yaml
# docker-compose.yml
networks:
  default:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

#### 3. 环境变量安全

```bash
# 使用 Docker secrets (Docker Swarm)
echo "your-secret-value" | docker secret create db_password -

# 或使用外部配置文件
docker-compose --env-file /secure/path/.env up -d
```

本部署指南提供了完整的 Docker 部署流程，包括开发、测试和生产环境的配置。按照这些步骤，您可以在 Linux 服务器上成功部署 JJCrawler3 服务，并确保其稳定运行。