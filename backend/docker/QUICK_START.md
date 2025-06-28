# JJCrawler Debian12 快速部署

## 一键部署

### 1. 安装 Docker
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```
注销后重新登录。

### 2. 部署项目
```bash
git clone <项目地址>
cd JJClawler-full/backend/docker
./deploy.sh
```

### 3. 验证
- 健康检查: http://localhost:8000/health
- API 文档: http://localhost:8000/docs

## 前端配置

修改前端 API 地址：`http://你的服务器IP:8000/api/v1`

## 管理命令

```bash
# 查看状态
docker compose ps

# 查看日志
docker compose logs -f jjcrawler

# 重启服务
docker compose restart

# 停止服务
docker compose down
```

## 故障排除

1. **端口占用**: 修改 docker-compose.yml 中的端口
2. **权限错误**: 确保用户在 docker 组中
3. **启动失败**: 查看日志 `docker compose logs jjcrawler`

## 国内镜像加速

项目已配置腾讯云镜像源。