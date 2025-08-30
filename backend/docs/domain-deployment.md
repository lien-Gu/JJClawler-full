# 域名部署配置指南

本文档详细说明如何将 JJCrawler 项目配置为使用域名 `work.guliyu.top` 访问，而不是直接使用 IP 地址。

## 前提条件

- 项目已通过 Docker 部署到 Linux 服务器
- 拥有域名 `guliyu.top` 的管理权限
- 服务器已安装 Docker 和 docker-compose
- 服务器具有公网 IP 地址

## 配置步骤

### 1. 配置域名 DNS 解析

在你的域名提供商（如阿里云、腾讯云、Cloudflare 等）的 DNS 控制台进行配置：

#### DNS 记录设置
- **记录类型**: A
- **主机记录**: work
- **记录值**: 你的服务器公网IP地址
- **TTL**: 600（10分钟）

#### 验证 DNS 解析
```bash
# 等待 DNS 生效（通常 5-10 分钟）
nslookup work.guliyu.top
# 或使用 dig 命令
dig work.guliyu.top
```

### 2. 安装和配置 Nginx 反向代理

#### 2.1 安装 Nginx

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install nginx -y
```

**CentOS/RHEL:**
```bash
sudo yum install epel-release -y
sudo yum install nginx -y
```

#### 2.2 启动并设置开机自启
```bash
sudo systemctl start nginx
sudo systemctl enable nginx
sudo systemctl status nginx
```

#### 2.3 创建站点配置文件

创建 Nginx 配置文件：
```bash
sudo nano /etc/nginx/sites-available/work.guliyu.top
```

配置内容：
```nginx
server {
    listen 80;
    server_name work.guliyu.top;

    # 日志配置
    access_log /var/log/nginx/work.guliyu.top.access.log;
    error_log /var/log/nginx/work.guliyu.top.error.log;

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

        # WebSocket 支持（如果需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API 文档路由
    location /docs {
        proxy_pass http://127.0.0.1:8000/docs;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /redoc {
        proxy_pass http://127.0.0.1:8000/redoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件缓存优化
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 2.4 启用站点配置
```bash
# 创建软链接启用站点
sudo ln -s /etc/nginx/sites-available/work.guliyu.top /etc/nginx/sites-enabled/

# 测试 Nginx 配置
sudo nginx -t

# 如果配置正确，重载 Nginx
sudo systemctl reload nginx
```

### 3. 配置 SSL 证书（推荐）

使用 Let's Encrypt 免费 SSL 证书实现 HTTPS 访问：

#### 3.1 安装 Certbot

**Ubuntu/Debian:**
```bash
sudo apt install certbot python3-certbot-nginx -y
```

**CentOS/RHEL:**
```bash
sudo yum install certbot python3-certbot-nginx -y
```

#### 3.2 获取并配置 SSL 证书
```bash
# 自动获取证书并配置 Nginx
sudo certbot --nginx -d work.guliyu.top

# 按照提示输入邮箱地址
# 同意服务条款
# 选择是否共享邮箱（可选择 N）
```

#### 3.3 验证 SSL 证书
```bash
# 测试自动续期
sudo certbot renew --dry-run

# 查看证书状态
sudo certbot certificates

# 设置自动续期（通常已自动配置）
sudo crontab -l | grep certbot
```

### 4. 修改 Docker 配置（提高安全性）

#### 4.1 修改 docker-compose.yml

将端口绑定改为仅本地访问，编辑 `docker-compose.yml` 文件：

**修改前:**
```yaml
ports:
  - "8000:8000"
```

**修改后:**
```yaml
ports:
  - "127.0.0.1:8000:8000"
```

这样配置的好处：
- Docker 容器只监听本地 127.0.0.1:8000
- 外部无法直接访问 Docker 容器端口
- 所有外部访问必须通过 Nginx 反向代理

#### 4.2 应用配置更改
```bash
# 进入项目目录
cd /path/to/your/jjcrawler-backend

# 停止当前容器
docker-compose down

# 重新构建并启动（如果修改了配置）
docker-compose up -d

# 检查容器状态
docker-compose ps
docker-compose logs jjcrawler

# 验证端口监听（应该只监听 127.0.0.1:8000）
sudo netstat -tlnp | grep :8000
```

### 5. 配置防火墙

确保服务器防火墙开放必要端口：

#### Ubuntu/Debian (ufw)
```bash
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw reload
sudo ufw status
```

#### CentOS/RHEL (firewalld)
```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
sudo firewall-cmd --list-all
```

### 6. 测试验证

#### 6.1 基础连通性测试
```bash
# 测试 HTTP 访问（配置 SSL 前）
curl -H 'Host: work.guliyu.top' http://work.guliyu.top/health

# 测试 HTTPS 访问（配置 SSL 后）
curl https://work.guliyu.top/health

# 测试 API 接口
curl https://work.guliyu.top/api/v1/schedule/status
```

#### 6.2 浏览器测试
在浏览器中访问以下地址：

- **健康检查**: https://work.guliyu.top/health
- **API 接口**: https://work.guliyu.top/api/v1/schedule/status
- **API 文档**: https://work.guliyu.top/docs
- **ReDoc 文档**: https://work.guliyu.top/redoc

#### 6.3 API 功能测试
```bash
# 测试调度器状态
curl -X GET "https://work.guliyu.top/api/v1/schedule/status"

# 测试创建爬取任务
curl -X POST "https://work.guliyu.top/api/v1/schedule/task/create"

# 测试书籍列表
curl -X GET "https://work.guliyu.top/api/v1/books/?limit=10"
```

## 常见问题和解决方案

### 1. DNS 解析问题
**问题**: 域名无法解析到服务器 IP
**解决**: 
- 检查 DNS 记录配置是否正确
- 等待 DNS 生效（最多 24 小时）
- 使用 `nslookup` 或 `dig` 验证解析

### 2. Nginx 502 Bad Gateway
**问题**: Nginx 返回 502 错误
**解决**:
```bash
# 检查 Docker 容器是否正常运行
docker-compose ps
docker-compose logs jjcrawler

# 检查端口监听
sudo netstat -tlnp | grep :8000

# 检查 Nginx 错误日志
sudo tail -f /var/log/nginx/work.guliyu.top.error.log
```

### 3. SSL 证书问题
**问题**: HTTPS 访问失败或证书错误
**解决**:
```bash
# 检查证书状态
sudo certbot certificates

# 手动续期证书
sudo certbot renew

# 检查 Nginx SSL 配置
sudo nginx -t
```

### 4. 防火墙阻挡
**问题**: 外部无法访问服务
**解决**:
```bash
# 检查防火墙状态
sudo ufw status       # Ubuntu
sudo firewall-cmd --list-all  # CentOS

# 检查云服务器安全组设置（阿里云/腾讯云/AWS等）
```

### 5. Docker 网络问题
**问题**: Nginx 无法连接到 Docker 容器
**解决**:
```bash
# 检查 Docker 网络
docker network ls
docker network inspect jjcrawler_jjcrawler-network

# 重启 Docker 网络
docker-compose down
docker-compose up -d
```

## 维护和监控

### 1. 日志监控
```bash
# Nginx 访问日志
sudo tail -f /var/log/nginx/work.guliyu.top.access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/work.guliyu.top.error.log

# Docker 容器日志
docker-compose logs -f jjcrawler
```

### 2. 性能监控
```bash
# 检查系统资源
htop
df -h
free -h

# 检查 Nginx 状态
sudo systemctl status nginx

# 检查 Docker 容器资源使用
docker stats jjcrawler
```

### 3. 定期维护
```bash
# 更新系统
sudo apt update && sudo apt upgrade  # Ubuntu
sudo yum update                       # CentOS

# SSL 证书自动续期验证
sudo certbot renew --dry-run

# Docker 镜像更新
docker-compose pull
docker-compose up -d
```

## 安全建议

1. **端口安全**: 使用 `127.0.0.1:8000:8000` 绑定，避免直接暴露 Docker 端口
2. **HTTPS 强制**: 配置 SSL 证书，强制使用 HTTPS 访问
3. **防火墙配置**: 只开放必要端口 80 和 443
4. **访问限制**: 可在 Nginx 配置中添加 IP 白名单或访问频率限制
5. **日志监控**: 定期检查访问日志，发现异常访问模式

## 最终访问地址

配置完成后，可以通过以下地址访问 JJCrawler 项目：

- **健康检查**: https://work.guliyu.top/health
- **API 基础路径**: https://work.guliyu.top/api/v1/
- **调度器状态**: https://work.guliyu.top/api/v1/schedule/status
- **书籍列表**: https://work.guliyu.top/api/v1/books/
- **API 文档**: https://work.guliyu.top/docs
- **ReDoc 文档**: https://work.guliyu.top/redoc

---

**注意**: 完成所有配置后，建议重启服务器确保所有配置生效：
```bash
sudo reboot
```

重启后验证所有服务是否正常启动：
```bash
sudo systemctl status nginx
docker-compose ps
curl https://work.guliyu.top/health
```