# JJCrawler Docker 部署文件

本目录包含JJCrawler后端服务的Docker部署相关文件。

## 文件说明

### 核心文件
- `Dockerfile` - Docker镜像构建文件
- `docker-compose.yml` - 直接部署配置（不使用反向代理）
- `docker-compose.nginx.yml` - 使用Nginx反向代理的部署配置
- `.env` - 环境变量配置文件
- `nginx.conf` - Nginx反向代理配置

## 部署方式选择

### 方式1：直接部署（推荐用于开发/内网环境）

**优点:**
- 配置简单，直接暴露8000端口
- 前端可以直接访问 `http://服务器IP:8000`
- 已配置CORS支持跨域访问

**缺点:**
- 没有SSL支持
- 没有负载均衡能力
- 直接暴露应用端口

**部署命令:**
```bash
cd /path/to/backend/docker
docker-compose up -d
```

**前端访问:**
```javascript
// 前端配置示例 (微信小程序)
const API_BASE_URL = 'http://你的服务器IP:8000'

// 或者在前端 utils/request.js 中
const baseURL = 'http://你的服务器IP:8000/api/v1'
```

### 方式2：使用Nginx反向代理（推荐用于生产环境）

**优点:**
- 支持SSL/HTTPS
- 更好的安全性
- 可以添加访问控制
- 标准的80端口访问
- 更好的性能和缓存

**缺点:**
- 配置相对复杂
- 需要额外的Nginx容器

**部署命令:**
```bash
cd /path/to/backend/docker
docker-compose -f docker-compose.nginx.yml up -d
```

**前端访问:**
```javascript
// 前端配置示例
const API_BASE_URL = 'http://你的服务器IP'  // 标准80端口

// 或者使用域名
const API_BASE_URL = 'http://your-domain.com'
```

## 详细部署步骤

### 1. 服务器准备
```bash
# 创建部署目录
sudo mkdir -p /opt/jjcrawler
sudo chown $USER:$USER /opt/jjcrawler
cd /opt/jjcrawler

# 上传项目文件
# 可以使用 git clone 或 scp 上传
```

### 2. 直接部署模式
```bash
# 进入docker目录
cd /opt/jjcrawler/docker

# 修改环境变量（可选）
vim .env

# 启动服务
docker-compose up -d

# 查看状态
docker-compose ps
docker-compose logs -f
```

### 3. Nginx反向代理模式
```bash
# 进入docker目录
cd /opt/jjcrawler/docker

# 修改nginx配置中的域名
vim nginx.conf
# 将 'your-domain.com' 替换为实际域名或IP

# 启动服务
docker-compose -f docker-compose.nginx.yml up -d

# 查看状态
docker-compose -f docker-compose.nginx.yml ps
```

## 前端配置

### 微信小程序前端配置

如果使用**直接部署模式**，前端需要修改 `frontend/utils/request.js`:

```javascript
// 直接访问模式
const config = {
  baseURL: 'http://你的服务器IP:8000/api/v1',
  timeout: 10000
}
```

如果使用**Nginx反向代理模式**，前端配置:

```javascript
// 反向代理模式
const config = {
  baseURL: 'http://你的服务器IP/api/v1',  // 注意没有端口号
  timeout: 10000
}
```

### CORS跨域处理

本项目已经在FastAPI中配置了CORS，支持跨域访问：

- **开发环境**: 允许所有来源 (`allow_origins=["*"]`)
- **生产环境**: 通过 `CORS_ORIGINS` 环境变量控制允许的来源

如果前端仍然遇到跨域问题，可以在 `.env` 文件中添加:
```bash
CORS_ORIGINS=http://localhost:3000,https://your-frontend-domain.com
```

## 健康检查和监控

### 检查服务状态
```bash
# 直接模式
curl http://localhost:8000/health

# 反向代理模式
curl http://localhost/health
```

### 查看API文档
```bash
# 直接模式
http://服务器IP:8000/docs

# 反向代理模式  
http://服务器IP/docs
```

### 查看日志
```bash
# 查看容器日志
docker-compose logs -f jjcrawler

# 查看nginx日志（如果使用反向代理）
docker-compose -f docker-compose.nginx.yml logs -f nginx
```

## 常见问题

### 1. 前端无法访问后端
**检查项:**
- 服务器防火墙是否开放相应端口
- Docker容器是否正常运行
- CORS配置是否正确

**解决方案:**
```bash
# 检查端口
sudo ufw allow 8000  # 直接模式
sudo ufw allow 80    # 反向代理模式

# 检查容器状态
docker-compose ps
```

### 2. 微信小程序网络请求失败
**原因:** 微信小程序要求HTTPS或配置合法域名

**解决方案:**
1. 开发阶段：在微信开发者工具中勾选"不校验合法域名"
2. 生产环境：配置HTTPS和在微信后台添加合法域名

### 3. 数据持久化
数据会自动保存在 `../data` 目录中，包括：
- SQLite数据库文件
- 失败记录
- 任务历史

## 性能优化建议

### 2C4G服务器优化
当前配置已针对2C4G服务器优化：
- CPU限制: 1.5核
- 内存限制: 2GB
- 保留资源: 0.5核CPU + 512MB内存

### 监控和维护
建议设置定期任务：
```bash
# 添加到crontab
0 2 * * * cd /opt/jjcrawler/docker && docker-compose restart jjcrawler
0 3 * * 0 docker system prune -f
```

## 安全建议

1. **防火墙配置**
   ```bash
   sudo ufw enable
   sudo ufw allow ssh
   sudo ufw allow 8000  # 或 80 for nginx
   ```

2. **定期备份**
   ```bash
   # 备份数据
   tar -czf backup-$(date +%Y%m%d).tar.gz ../data
   ```

3. **监控日志**
   ```bash
   # 定期查看访问日志
   docker-compose logs --tail=100 jjcrawler
   ```

## 下一步

部署完成后，可以：
1. 访问 `http://服务器IP:8000/docs` 查看API文档
2. 测试健康检查接口
3. 配置前端访问地址
4. 设置监控和备份策略