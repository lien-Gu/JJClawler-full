# JJCrawler Docker 部署指南

本文档详细说明如何在 Ubuntu 22 服务器（2C4G配置）上使用 Docker 部署 JJCrawler 后端服务。

## 目录

1. [服务器要求](#服务器要求)
2. [环境准备](#环境准备)
3. [Docker 配置](#docker-配置)
4. [构建和部署](#构建和部署)
5. [监控和维护](#监控和维护)
6. [故障排除](#故障排除)
7. [性能优化](#性能优化)

## 服务器要求

### 硬件配置
- **CPU**: 2 核心
- **内存**: 4GB RAM
- **存储**: 至少 20GB 可用空间
- **网络**: 稳定的网络连接

### 操作系统
- Ubuntu 22.04 LTS
- 内核版本 5.15 或更高

### 端口要求
- **8000**: JJCrawler API 服务端口
- **22**: SSH 端口（管理用）

## 环境准备

### 1. 更新系统

```bash
# 更新包列表
sudo apt update && sudo apt upgrade -y

# 安装必要的工具
sudo apt install -y curl wget git vim htop
```

### 2. 安装 Docker

```bash
# 安装 Docker 依赖
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG 密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker (包含 Docker Compose)
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 启动并设置开机自启
sudo systemctl start docker
sudo systemctl enable docker

# 将用户添加到 docker 组（可选，避免使用 sudo）
sudo usermod -aG docker $USER
```

**注意**: 从 Docker Desktop 和较新版本的 Docker Engine 开始，Docker Compose 已经作为插件集成到 Docker 中，无需单独安装。

### 3. 验证 Docker Compose 安装

```bash
# 验证 Docker Compose 插件安装（推荐方式）
docker compose version

# 如果上述命令失败，检查是否有独立的 docker-compose
docker-compose --version

# 注销并重新登录以使用户组更改生效
# 或者运行以下命令刷新用户组
newgrp docker
```

**说明**: Docker Compose 现在作为 Docker 的插件提供，使用 `docker compose` 命令。如果您的系统仍使用独立版本，可以继续使用 `docker-compose` 命令。

### 4. 创建应用目录

```bash
# 创建应用目录
sudo mkdir -p /opt/jjcrawler
sudo chown $USER:$USER /opt/jjcrawler
cd /opt/jjcrawler
```

## Docker 配置

### 1. 创建 Dockerfile

```dockerfile
# /opt/jjcrawler/Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY pyproject.toml poetry.lock* ./

# 安装 Poetry
RUN pip install poetry

# 配置 Poetry
RUN poetry config virtualenvs.create false

# 安装依赖
RUN poetry install --no-dev --no-interaction --no-ansi

# 复制应用代码
COPY app/ ./app/
COPY data/ ./data/

# 创建数据目录
RUN mkdir -p /app/data/failures /app/data/tasks/history

# 设置数据目录权限
RUN chmod -R 755 /app/data

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 创建 docker-compose.yml

```yaml
# /opt/jjcrawler/docker-compose.yml
version: '3.8'

services:
  jjcrawler:
    build: .
    container_name: jjcrawler-backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    volumes:
      # 数据持久化
      - ./data:/app/data
      # 日志挂载
      - ./logs:/app/logs
    environment:
      # 应用配置
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - MAX_RETRIES=3
      - REQUEST_TIMEOUT=30
      - CRAWL_DELAY=1.0
      # 数据库配置
      - DATABASE_URL=sqlite:///app/data/jjcrawler.db
      # 调度器配置
      - SCHEDULER_ENABLED=true
      - SCHEDULER_TIMEZONE=Asia/Shanghai
    labels:
      - "app=jjcrawler"
      - "version=1.0.0"
    networks:
      - jjcrawler-network
    
    # 资源限制（适用于 2C4G 服务器）
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

networks:
  jjcrawler-network:
    driver: bridge
```

### 3. 创建环境配置文件

```bash
# /opt/jjcrawler/.env
# 应用环境
ENVIRONMENT=production
LOG_LEVEL=INFO

# 服务器配置
HOST=0.0.0.0
PORT=8000

# 爬虫配置
MAX_RETRIES=3
REQUEST_TIMEOUT=30
CRAWL_DELAY=1.0

# 数据库配置
DATABASE_URL=sqlite:///app/data/jjcrawler.db

# 调度器配置
SCHEDULER_ENABLED=true
SCHEDULER_TIMEZONE=Asia/Shanghai

# 失败存储配置
FAILURE_STORAGE_DAYS=7
```

### 4. 创建 nginx 反向代理配置（可选）

```nginx
# /etc/nginx/sites-available/jjcrawler
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名

    # 访问日志
    access_log /var/log/nginx/jjcrawler_access.log;
    error_log /var/log/nginx/jjcrawler_error.log;

    # 反向代理到 Docker 容器
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API 文档路径
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

## 构建和部署

### 1. 获取源代码

```bash
# 克隆代码仓库（或上传文件）
cd /opt/jjcrawler

# 如果从 git 克隆
git clone <your-repo-url> .

# 或者手动上传并解压
# scp jjcrawler.tar.gz user@server:/opt/jjcrawler/
# tar -xzf jjcrawler.tar.gz
```

### 2. 准备数据目录

```bash
# 创建必要的目录
mkdir -p data/failures data/tasks/history logs

# 设置权限
chmod -R 755 data logs

# 检查 urls.json 配置文件
ls -la data/urls.json
```

### 3. 构建 Docker 镜像

```bash
# 构建镜像 (使用集成的 Docker Compose)
docker compose build

# 或者使用独立版本（如果需要）
# docker-compose build

# 查看构建结果
docker images | grep jjcrawler
```

### 4. 启动服务

```bash
# 启动服务 (使用集成的 Docker Compose)
docker compose up -d

# 查看容器状态
docker compose ps

# 查看日志
docker compose logs -f jjcrawler

# 注意：如果您的系统使用独立的 docker-compose，请将上述命令中的 'docker compose' 替换为 'docker-compose'
```

### 5. 验证部署

```bash
# 检查健康状态
curl http://localhost:8000/health

# 检查 API 文档
curl http://localhost:8000/docs

# 测试 API 接口
curl http://localhost:8000/api/v1/stats/overview
```

## 监控和维护

### 1. 创建监控脚本

```bash
# /opt/jjcrawler/scripts/monitor.sh
#!/bin/bash

# 监控脚本
CONTAINER_NAME="jjcrawler-backend"
LOG_FILE="/opt/jjcrawler/logs/monitor.log"

# 检查容器状态
check_container() {
    if ! docker ps | grep -q $CONTAINER_NAME; then
        echo "$(date): Container $CONTAINER_NAME is not running" >> $LOG_FILE
        docker compose restart jjcrawler
        echo "$(date): Container restarted" >> $LOG_FILE
    fi
}

# 检查内存使用
check_memory() {
    MEMORY_USAGE=$(docker stats --no-stream --format "table {{.MemUsage}}" $CONTAINER_NAME | tail -1 | cut -d'/' -f1)
    echo "$(date): Memory usage: $MEMORY_USAGE" >> $LOG_FILE
}

# 检查磁盘空间
check_disk() {
    DISK_USAGE=$(df -h /opt/jjcrawler | tail -1 | awk '{print $5}')
    echo "$(date): Disk usage: $DISK_USAGE" >> $LOG_FILE
    
    if [[ ${DISK_USAGE%?} -gt 80 ]]; then
        echo "$(date): WARNING: Disk usage above 80%" >> $LOG_FILE
        # 清理日志
        find /opt/jjcrawler/logs -name "*.log" -mtime +7 -delete
    fi
}

# 执行检查
check_container
check_memory
check_disk
```

```bash
# 设置执行权限
chmod +x /opt/jjcrawler/scripts/monitor.sh

# 添加到 crontab（每 5 分钟检查一次）
echo "*/5 * * * * /opt/jjcrawler/scripts/monitor.sh" | crontab -
```

### 2. 日志轮转配置

```bash
# /etc/logrotate.d/jjcrawler
/opt/jjcrawler/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
    postrotate
        docker compose exec jjcrawler kill -USR1 1
    endscript
}
```

### 3. 备份脚本

```bash
# /opt/jjcrawler/scripts/backup.sh
#!/bin/bash

BACKUP_DIR="/opt/backups/jjcrawler"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/jjcrawler/data/jjcrawler.db $BACKUP_DIR/jjcrawler_$DATE.db

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz \
    /opt/jjcrawler/docker-compose.yml \
    /opt/jjcrawler/.env \
    /opt/jjcrawler/data/urls.json

# 清理旧备份（保留 7 天）
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "$(date): Backup completed" >> /opt/jjcrawler/logs/backup.log
```

## 故障排除

### 1. 常见问题

#### 容器启动失败

```bash
# 查看详细日志
docker compose logs jjcrawler

# 检查配置文件
docker compose config

# 重新构建镜像
docker compose build --no-cache
```

#### 端口占用

```bash
# 查看端口占用
sudo netstat -tulpn | grep 8000

# 或使用 ss 命令
sudo ss -tulpn | grep 8000

# 停止占用端口的进程
sudo kill -9 <PID>
```

#### 内存不足

```bash
# 查看系统内存
free -h

# 查看容器内存使用
docker stats jjcrawler-backend

# 清理系统缓存
sudo sync && sudo echo 3 > /proc/sys/vm/drop_caches
```

#### 磁盘空间不足

```bash
# 查看磁盘使用
df -h

# 清理 Docker 缓存
docker system prune -f

# 清理日志文件
sudo journalctl --disk-usage
sudo journalctl --vacuum-time=7d
```

### 2. 性能优化

#### 数据库优化

```sql
-- 定期执行数据库优化（在容器内）
PRAGMA optimize;
VACUUM;
REINDEX;
```

#### 系统优化

```bash
# 调整系统参数
echo 'vm.swappiness=10' >> /etc/sysctl.conf
echo 'net.core.somaxconn=65535' >> /etc/sysctl.conf
sysctl -p
```

### 3. 应急处理

#### 服务重启

```bash
# 重启服务
docker compose restart jjcrawler

# 强制重启
docker compose down && docker compose up -d
```

#### 数据恢复

```bash
# 从备份恢复数据库
cp /opt/backups/jjcrawler/jjcrawler_YYYYMMDD_HHMMSS.db /opt/jjcrawler/data/jjcrawler.db

# 重启服务
docker compose restart jjcrawler
```

## 管理命令参考

### Docker 管理

```bash
# 查看容器状态
docker compose ps

# 查看实时日志
docker compose logs -f jjcrawler

# 进入容器
docker compose exec jjcrawler bash

# 查看资源使用
docker stats jjcrawler-backend

# 更新镜像
docker compose pull && docker compose up -d
```

### 数据管理

```bash
# 查看数据库大小
du -sh /opt/jjcrawler/data/jjcrawler.db

# 查看失败记录
ls -la /opt/jjcrawler/data/failures/

# 清理过期数据（在容器内执行）
# 可以通过 API 调用清理端点
curl -X POST http://localhost:8000/api/v1/admin/cleanup
```

### 服务控制

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看服务状态
systemctl status docker
```

## 安全建议

1. **防火墙配置**：只开放必要端口
2. **定期更新**：保持系统和 Docker 镜像更新
3. **访问控制**：使用 nginx 反向代理，添加访问控制
4. **监控告警**：设置资源使用监控和告警
5. **数据备份**：定期备份重要数据
6. **日志审计**：保留访问日志用于安全审计

## 联系支持

如果在部署过程中遇到问题，请：

1. 检查本文档的故障排除部分
2. 查看应用日志：`docker compose logs jjcrawler`
3. 检查系统资源使用情况
4. 提供详细的错误信息和环境信息

---

**注意事项**：
- 本部署指南基于 Ubuntu 22 和 2C4G 配置优化
- 生产环境建议使用 HTTPS 和域名
- 定期监控服务状态和资源使用
- 建立完善的备份和恢复策略