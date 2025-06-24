# JJCrawler 快速部署指南

## 🚀 一键部署

### 前提条件
- Ubuntu 22.04 服务器 (2C4G)
- 已安装 Docker 和 Docker Compose

### 快速部署命令

```bash
# 1. 上传项目到服务器
cd /opt
sudo mkdir jjcrawler && sudo chown $USER:$USER jjcrawler
cd jjcrawler

# 上传项目文件 (使用 scp 或 git clone)

# 2. 进入docker目录
cd backend/docker

# 3. 一键部署
./deploy.sh -m direct
```

## 📱 前端配置

### 微信小程序前端修改

修改 `frontend/utils/request.js` 文件：

```javascript
// 原配置 (本地开发)
const config = {
  baseURL: 'http://localhost:8000/api/v1',
  timeout: 10000
}

// 修改为服务器配置
const config = {
  baseURL: 'http://你的服务器IP:8000/api/v1',  // 替换为实际IP
  timeout: 10000
}
```

## 🔧 两种部署方式对比

| 特性 | 直接部署 | Nginx反向代理 |
|------|----------|----------------|
| **端口** | 8000 | 80 |
| **前端访问** | `http://IP:8000` | `http://IP` |
| **SSL支持** | ❌ | ✅ |
| **配置复杂度** | 简单 | 中等 |
| **适用场景** | 开发/内网 | 生产环境 |

### 直接部署 (推荐)
```bash
./deploy.sh -m direct
```
- ✅ 配置简单
- ✅ 已处理CORS跨域
- ✅ 前端可直接访问
- ❌ 需要指定端口8000

### Nginx反向代理
```bash
./deploy.sh -m nginx
```
- ✅ 标准80端口
- ✅ 支持SSL扩展
- ✅ 更好安全性
- ❌ 配置相对复杂

## 🔍 验证部署

### 检查服务状态
```bash
# 查看容器状态
./deploy.sh -s

# 查看日志
./deploy.sh -l

# 健康检查
curl http://localhost:8000/health  # 直接模式
curl http://localhost/health       # nginx模式
```

### 测试API
```bash
# 测试统计接口
curl http://localhost:8000/api/v1/stats/overview

# 查看API文档
# 浏览器访问: http://服务器IP:8000/docs
```

## 🐛 常见问题解决

### 1. 端口被占用
```bash
# 查看端口占用
sudo netstat -tlnp | grep 8000

# 停止占用进程
sudo kill -9 <PID>
```

### 2. 前端无法访问
```bash
# 检查防火墙
sudo ufw status
sudo ufw allow 8000

# 检查容器状态
docker ps
```

### 3. 微信小程序网络错误
- **开发阶段**: 在微信开发者工具中勾选"不校验合法域名"
- **生产环境**: 配置HTTPS并在微信后台添加合法域名

### 4. 服务重启
```bash
# 重启服务
./deploy.sh -r

# 完全重新部署
./deploy.sh -d  # 停止
./deploy.sh -m direct  # 重新部署
```

## 📊 监控和维护

### 查看资源使用
```bash
# 容器资源使用
docker stats jjcrawler-backend

# 系统资源
htop
df -h
```

### 定期维护
```bash
# 添加到 crontab
crontab -e

# 每天凌晨2点重启服务
0 2 * * * cd /opt/jjcrawler/backend/docker && ./deploy.sh -r

# 每周清理无用镜像
0 3 * * 0 docker system prune -f
```

## 🔒 安全建议

### 基础安全配置
```bash
# 防火墙配置
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 8000  # 或 80 for nginx

# 禁用root登录
sudo vim /etc/ssh/sshd_config
# PermitRootLogin no

# 重启SSH服务
sudo systemctl restart ssh
```

### 数据备份
```bash
# 创建备份脚本
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
tar -czf /opt/backups/jjcrawler_${DATE}.tar.gz /opt/jjcrawler/backend/data
find /opt/backups -name "jjcrawler_*.tar.gz" -mtime +7 -delete
EOF

chmod +x backup.sh

# 添加到定时任务
echo "0 1 * * * /opt/jjcrawler/backup.sh" | crontab -
```

## 📞 技术支持

如果遇到问题：

1. **查看日志**: `./deploy.sh -l`
2. **检查状态**: `./deploy.sh -s`
3. **环境检查**: `./deploy.sh -c`
4. **完整重部署**: `./deploy.sh -d && ./deploy.sh -m direct`

## 🎯 下一步

部署成功后：

1. ✅ 访问 API 文档: `http://服务器IP:8000/docs`
2. ✅ 配置前端访问地址
3. ✅ 测试爬虫功能
4. ✅ 配置监控和备份
5. ✅ (可选) 配置域名和SSL

---

**快速命令参考:**
```bash
./deploy.sh -m direct  # 部署
./deploy.sh -s         # 状态
./deploy.sh -l         # 日志  
./deploy.sh -r         # 重启
./deploy.sh -d         # 停止
```