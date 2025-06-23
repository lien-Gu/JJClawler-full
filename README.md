# JJClawler - 晋江文学城爬虫项目

## 项目概述

JJClawler 是一个专为晋江文学城开发的数据爬虫项目，包含完整的后端数据采集服务和微信小程序前端界面。项目采用现代化的技术栈，提供稳定、高效的数据爬取和展示服务。

### 核心功能
- 🕷️ **自动化爬虫**: 定时爬取榜单数据和小说信息
- 📊 **数据分析**: 书籍点击量、收藏量趋势分析
- 📱 **小程序界面**: 直观的数据展示和检索功能
- 🔄 **实时更新**: 支持手动触发和定时自动更新
- 📈 **历史追踪**: 完整的排名变化和数据趋势记录

## 项目结构

```
JJClawler-full/
├── backend/                    # 后端服务 (Python FastAPI)
│   ├── app/                    # 应用核心代码
│   │   ├── api/               # API 路由层
│   │   ├── modules/           # 业务模块
│   │   └── utils/             # 工具函数
│   ├── data/                  # 数据存储
│   ├── docs/                  # 文档
│   └── tests/                 # 测试代码
├── frontend/                  # 前端小程序 (WeChat Mini-Program)
│   ├── pages/                 # 小程序页面
│   ├── components/            # 组件库
│   ├── utils/                 # 工具函数
│   └── styles/                # 样式文件
├── README.md                  # 项目说明
└── CLAUDE.md                  # 开发指南
```

## 技术栈

### 后端技术
- **框架**: FastAPI (Python 3.13+)
- **数据库**: SQLite with SQLModel ORM
- **爬虫**: httpx + Beautiful Soup
- **调度**: APScheduler
- **部署**: Docker + Poetry

### 前端技术
- **框架**: WeChat Mini-Program
- **UI**: Vue.js 语法
- **样式**: SCSS
- **状态管理**: 本地存储 + API 调用

## 快速开始

### 环境要求
- Python 3.13+
- Poetry (推荐)
- 微信开发者工具
- Git

### 后端部署

1. **克隆项目**
```bash
git clone https://github.com/lien-Gu/JJClawler-full.git
cd JJClawler-full/backend
```

2. **安装依赖**
```bash
poetry install
poetry shell
```

3. **启动服务**
```bash
poetry run uvicorn app.main:app --reload --port 8000
```

4. **验证部署**
```bash
curl http://localhost:8000/health
# 访问 API 文档: http://localhost:8000/docs
```

5. **停止服务**
```bash
# 方法1: 在运行uvicorn的终端中按 Ctrl+C
# 方法2: 查找并杀死进程
ps aux | grep uvicorn
kill <进程ID>

# 方法3: 强制杀死所有uvicorn进程
pkill -f uvicorn

# 方法4: 杀死占用8000端口的进程
lsof -i :8000
kill -9 <PID>
```

### 前端部署

1. **导入项目**
   - 打开微信开发者工具
   - 导入 `frontend/` 目录作为小程序项目

2. **配置后端地址**
   - 编辑 `frontend/utils/request.js` 中的 `baseURL`
   - 开发环境: `http://localhost:8000/api/v1`

3. **预览运行**
   - 在微信开发者工具中编译预览

## API 接口说明

### 核心接口

| 接口分类 | 端点 | 描述 |
|---------|------|------|
| **统计数据** | `GET /api/v1/stats/overview` | 首页统计概览 |
| **榜单数据** | `GET /api/v1/rankings` | 榜单列表 |
| | `GET /api/v1/rankings/hot` | 热门榜单 |
| | `GET /api/v1/rankings/{id}/books` | 榜单书籍列表 |
| **书籍数据** | `GET /api/v1/books/{id}` | 书籍详情 |
| | `GET /api/v1/books/{id}/rankings` | 书籍排名历史 |
| | `GET /api/v1/books/{id}/trends` | 书籍趋势数据 |
| **爬虫管理** | `POST /api/v1/crawl/jiazi` | 触发夹子榜爬取 |
| | `GET /api/v1/crawl/tasks` | 查看任务状态 |
| **页面配置** | `GET /api/v1/pages` | 获取页面配置 |

### 接口统一
经过分析和优化，前后端接口已完全统一，包括：
- ✅ 数据格式标准化
- ✅ 错误处理机制
- ✅ 分页参数统一
- ✅ 响应结构一致

## 部署说明

### Docker 部署（推荐）

1. **构建镜像**
```bash
cd backend
docker build -t jjcrawler:latest .
```

2. **运行容器**
```bash
docker run -d \
  --name jjcrawler \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  jjcrawler:latest
```

3. **配置反向代理**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 生产环境部署

详细的生产环境部署指南请参考：
- [Docker 部署文档](backend/docs/docker-deployment.md)
- [生产运维指南](backend/docs/production-operations.md)
- [调度器运维指南](backend/docs/scheduler-operations.md)

## 定时任务说明

### 自动调度策略
- **夹子榜**: 每小时更新一次 (高频榜单)
- **分类榜单**: 每天更新一次 (上午6点到下午6点分散执行)
- **错误重试**: 指数退避算法，最多重试3次
- **限流机制**: 请求间隔1秒，避免对目标站点造成压力

### 手动管理
```bash
# 查看调度器状态
curl http://localhost:8000/api/v1/crawl/scheduler/status

# 手动触发夹子榜爬取
curl -X POST http://localhost:8000/api/v1/crawl/jiazi

# 查看任务历史
curl http://localhost:8000/api/v1/crawl/tasks
```

### 任务监控
- 实时任务状态查看
- 任务执行历史记录
- 异常告警和自动恢复
- 性能指标监控

## 开发指南

### 后端开发
```bash
# 格式化代码
poetry run black .
poetry run isort .

# 运行测试
poetry run pytest

# 启动开发服务器
poetry run uvicorn app.main:app --reload
```

### 前端开发
- 使用微信开发者工具进行开发
- 遵循微信小程序开发规范
- 组件化开发，提高代码重用性

### API 测试
- 使用 `backend/test_main.http` 进行接口测试
- 访问 `http://localhost:8000/docs` 查看交互式文档

## 数据库设计

### 核心数据表
```sql
-- 书籍基础信息
books: book_id, title, author_id, author_name, novel_class, tags

-- 书籍动态数据快照
book_snapshots: book_id, total_clicks, total_favorites, snapshot_time

-- 榜单排名快照
ranking_snapshots: ranking_id, book_id, position, snapshot_time

-- 榜单配置
rankings: ranking_id, name, channel, frequency, update_interval
```

### 设计特点
- **静态与动态分离**: 基础信息与统计数据分表存储
- **时间序列设计**: 支持趋势分析和历史查询
- **混合存储**: 数据库 + JSON 文件，各司其职
- **性能优化**: SQLite WAL 模式，复合索引

## 监控与运维

### 健康检查
```bash
# 系统健康状态
curl http://localhost:8000/health

# 数据库状态
curl http://localhost:8000/stats

# 调度器状态
curl http://localhost:8000/api/v1/crawl/scheduler/status
```

### 日志管理
- 结构化日志记录
- 错误等级分类
- 日志轮转和归档
- 实时日志监控

### 数据备份
```bash
# 数据库备份
cp data/*.db backup/

# 配置文件备份
cp data/urls.json backup/
cp data/tasks/*.json backup/
```

## 故障排除

### 常见问题

**Q: 端口被占用怎么办？**
```bash
# 检查端口占用
lsof -i :8000
# 使用其他端口
uvicorn app.main:app --reload --port 8001
```

**Q: 爬虫任务失败怎么办？**
```bash
# 查看任务状态
curl http://localhost:8000/api/v1/crawl/tasks
# 手动重试
curl -X POST http://localhost:8000/api/v1/crawl/jiazi
```

**Q: 数据库锁定怎么办？**
```bash
# 检查数据库状态
# 确保 WAL 模式启用
# 重启应用服务
```

## 贡献指南

### 开发流程
1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 代码规范
- Python: 遵循 PEP 8 规范
- 前端: 遵循微信小程序开发规范
- 提交信息: 使用清晰的描述性消息
- 文档: 更新相关文档

## 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

## 联系方式

- **项目负责人**: Lien Gu
- **邮箱**: guliyu0216@163.com
- **项目地址**: https://github.com/lien-Gu/JJClawler-full

## 更新日志

### v1.0.0 (2024-06-23)
- ✅ 完成后端 API 接口统一
- ✅ 前端小程序界面完成
- ✅ Docker 部署方案
- ✅ 定时任务调度系统
- ✅ 完整的监控和运维方案

---

**注意**: 本项目仅用于学习和研究目的，请遵守相关法律法规和网站使用条款。