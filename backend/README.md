# 晋江文学城爬虫后端项目

## 1. 项目概述

### 1.1 项目简介
JJCrawler 是一个基于 FastAPI 的现代化晋江文学城数据爬虫后端服务。项目采用简化的架构设计，专注于榜单数据采集、存储和API服务，为前端应用提供稳定可靠的数据接口。

### 1.2 核心特性
- **简化架构设计**：去除DAO层，Service层直接操作数据库，减少代码复杂性
- **高效数据处理**：基于SQLite + SQLModel的轻量级解决方案
- **自动化爬取**：支持APScheduler定时任务和手动触发
- **类型安全**：全面使用FastAPI + SQLModel实现类型检查
- **模块化设计**：功能模块独立，易于维护和扩展
- **容器化部署**：提供完整的Docker部署方案

### 1.3 技术栈
- **后端框架**：FastAPI ^0.115.0
- **数据库**：SQLite + SQLModel ^0.0.22
- **任务调度**：APScheduler ^3.10.4
- **HTTP客户端**：httpx ^0.28.0
- **异步支持**：aiosqlite ^0.21.0
- **依赖管理**：Poetry
- **容器化**：Docker + docker-compose

## 2. 项目结构

### 2.1 后端代码目录结构

```
backend/
├── app/                          # 主应用目录
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理
│   ├── api/                      # API接口模块
│   │   ├── __init__.py
│   │   ├── books.py              # 书籍相关接口
│   │   ├── rankings.py           # 榜单相关接口
│   │   └── crawl.py              # 爬虫管理接口
│   ├── crawl/                    # 爬虫模块
│   │   ├── __init__.py
│   │   ├── base.py               # 爬虫基础类
│   │   ├── crawl_flow.py         # 爬取流程管理
│   │   └── parser.py             # 数据解析器
│   ├── database/                 # 数据库模块
│   │   ├── __init__.py
│   │   ├── connection.py         # 数据库连接管理
│   │   ├── db/                   # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # 基础模型
│   │   │   ├── book.py           # 书籍模型
│   │   │   └── ranking.py        # 榜单模型
│   │   └── service/              # 业务逻辑层（简化架构）
│   │       ├── __init__.py
│   │       ├── book_service.py   # 书籍业务逻辑
│   │       └── ranking_service.py # 榜单业务逻辑
│   ├── models/                   # API模型
│   │   ├── __init__.py
│   │   ├── base.py               # 基础响应模型
│   │   ├── book.py               # 书籍API模型
│   │   ├── ranking.py            # 榜单API模型
│   │   ├── crawl.py              # 爬虫API模型
│   │   └── schedule.py           # 调度API模型
│   └── schedule/                 # 任务调度模块
│       ├── __init__.py
│       ├── scheduler.py          # 任务调度器
│       └── handlers.py           # 任务处理器
├── data/                         # 数据存储目录
│   ├── urls.json                 # 爬取配置
│   ├── tasks/                    # 任务状态存储
│   └── example/                  # 示例数据
├── tests/                        # 测试用例
├── Dockerfile                    # Docker镜像配置
├── docker-compose.yml            # Docker编排配置
├── deploy.sh                     # 一键部署脚本
├── pyproject.toml                # 项目依赖配置
├── .env.example                  # 环境变量模板
└── README.md                     # 项目文档
```

### 2.2 各模块功能说明

#### 2.2.1 API模块 (app/api/)
**功能职责**：提供RESTful API接口，处理HTTP请求和响应

**核心文件**：
- **books.py**：书籍相关接口
  - 书籍列表、搜索、详情查询
  - 书籍数据趋势分析（小时/天/周/月级聚合）
  - 书籍排名历史查询
- **rankings.py**：榜单相关接口
  - 榜单列表、详情、历史数据查询
  - 榜单统计信息、多榜单对比
- **crawl.py**：爬虫管理接口
  - 手动触发爬取（全部/指定页面）
  - 任务状态监控、调度器状态查询

#### 2.2.2 爬虫模块 (app/crawl/)
**功能职责**：实现网页数据爬取和解析

**核心文件**：
- **base.py**：爬虫基础类，提供HTTP客户端和配置管理
- **crawl_flow.py**：爬取流程管理器，整合爬取、解析、存储流程
- **parser.py**：数据解析器，支持多种页面类型的数据提取

#### 2.2.3 数据库模块 (app/database/)
**功能职责**：数据模型定义和业务逻辑处理（简化架构）

**架构特点**：
- **去除DAO层**：Service层直接操作数据库，减少代码层级
- **类型安全**：使用SQLModel实现ORM和API模型统一
- **异步支持**：全面支持异步数据库操作

**核心组件**：
- **db/模型定义**：Book、BookSnapshot、Ranking、RankingSnapshot
- **service/业务逻辑**：封装CRUD操作和复杂查询逻辑
- **connection.py**：数据库连接池管理

#### 2.2.4 调度模块 (app/schedule/)
**功能职责**：任务调度和定时爬取

**核心文件**：
- **scheduler.py**：基于APScheduler的任务调度器
- **handlers.py**：任务处理器，定义具体的爬取任务

#### 2.2.5 数据模型 (app/models/)
**功能职责**：API请求响应模型定义

**核心特点**：
- 使用Pydantic进行数据验证
- 统一的响应格式（DataResponse、ListResponse）
- 类型安全的API接口定义

## 3. 数据库设计

### 3.1 数据库架构

采用SQLite + SQLModel的轻量级解决方案，设计四个核心表：

#### 3.1.1 核心表结构

**books表 - 书籍基础信息**
```sql
- id: 主键
- novel_id: 小说ID（晋江站内ID）
- title: 书籍标题
- author_name: 作者名称
- created_at: 创建时间
- updated_at: 更新时间
```

**book_snapshots表 - 书籍动态统计快照**
```sql
- id: 主键
- book_id: 关联books表
- clicks: 点击数
- favorites: 收藏数
- comments: 评论数
- recommendations: 推荐数
- word_count: 字数
- status: 状态
- snapshot_time: 快照时间
```

**rankings表 - 榜单配置信息**
```sql
- id: 主键
- rank_id: 榜单ID
- name: 榜单名称
- page_id: 页面ID
- rank_group_type: 榜单分组类型
- created_at: 创建时间
- updated_at: 更新时间
```

**ranking_snapshots表 - 榜单排名快照**
```sql
- id: 主键
- ranking_id: 关联rankings表
- book_id: 关联books表
- position: 排名位置
- score: 评分
- snapshot_time: 快照时间
```

### 3.2 设计特点

- **数据分离**：静态信息与动态统计分表存储
- **时间序列**：快照表支持历史数据查询和趋势分析
- **索引优化**：基于查询模式设计复合索引
- **轻量级**：SQLite适合中小型项目需求

## 4. API接口文档

### 4.1 书籍相关接口 (GET /api/v1/books/)

#### 基础查询
- **GET /books/** - 分页获取书籍列表
- **GET /books/search** - 搜索书籍（支持标题、作者）
- **GET /books/{book_id}** - 获取书籍详细信息

#### 趋势分析
- **GET /books/{book_id}/trend** - 获取原始趋势数据
- **GET /books/{book_id}/trend/hourly** - 小时级聚合趋势
- **GET /books/{book_id}/trend/daily** - 日级聚合趋势  
- **GET /books/{book_id}/trend/weekly** - 周级聚合趋势
- **GET /books/{book_id}/trend/monthly** - 月级聚合趋势
- **GET /books/{book_id}/trend/aggregated** - 自定义时间间隔聚合

#### 排名历史
- **GET /books/{book_id}/rankings** - 获取书籍在各榜单的排名历史

### 4.2 榜单相关接口 (GET /api/v1/rankings/)

#### 基础查询
- **GET /rankings/** - 分页获取榜单列表（支持分组筛选）
- **GET /rankings/{ranking_id}** - 获取榜单详情和书籍列表

#### 历史与统计
- **GET /rankings/{ranking_id}/history** - 获取榜单历史数据
- **GET /rankings/{ranking_id}/stats** - 获取榜单统计信息

#### 对比分析
- **POST /rankings/compare** - 多榜单对比分析

### 4.3 爬虫管理接口 (POST /api/v1/crawl/)

#### 任务触发
- **POST /crawl/all** - 爬取所有配置页面
- **POST /crawl/pages** - 批量爬取指定页面
- **POST /crawl/page/{page_id}** - 爬取单个页面

#### 状态监控
- **GET /crawl/status** - 获取调度器状态和任务统计
- **GET /crawl/batch/{batch_id}/status** - 获取批量任务执行状态

### 4.4 系统接口
- **GET /health** - 健康检查
- **GET /docs** - API文档（Swagger UI）
- **GET /redoc** - API文档（ReDoc）

## 5. Docker部署指南

### 5.1 环境要求

**系统要求**：
- Docker 20.0+
- Docker Compose 2.0+
- 可用内存：2GB+
- 可用存储：5GB+

### 5.2 快速部署

#### 方式一：使用部署脚本（推荐）

```bash
# 克隆项目
git clone https://github.com/lien-Gu/JJClawler-full.git
cd JJClawler-full/backend

# 一键部署
chmod +x deploy.sh
./deploy.sh
```

#### 方式二：手动Docker Compose部署

```bash
# 克隆项目
git clone https://github.com/lien-Gu/JJClawler-full.git
cd JJClawler-full/backend

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 方式三：Docker直接部署

```bash
# 构建镜像
docker build -t jjcrawler:latest .

# 运行容器
docker run -d \
  --name jjcrawler \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  jjcrawler:latest
```

### 5.3 部署验证

```bash
# 健康检查
curl http://localhost:8000/health
# 预期响应: {"status": "healthy", "timestamp": "..."}

# 查看API文档
# 浏览器访问: http://localhost:8000/docs

# 测试API接口
curl -X POST http://localhost:8000/api/v1/crawl/all
curl http://localhost:8000/api/v1/crawl/status
```

### 5.4 环境配置

项目提供了完整的环境变量配置：

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（可选）
vim .env
```

**主要配置项**：
- 数据库路径配置
- CORS设置
- 爬虫参数（延迟、超时、重试）
- 调度器配置

### 5.5 生产环境部署

#### Nginx反向代理配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 系统服务配置

```bash
# 创建systemd服务文件
sudo vim /etc/systemd/system/jjcrawler.service
```

```ini
[Unit]
Description=JJ Crawler Backend Service
After=network.target

[Service]
Type=exec
User=www-data
WorkingDirectory=/path/to/JJClawler-full/backend
ExecStart=/usr/local/bin/docker-compose up
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

## 6. 开发指南

### 6.1 开发环境搭建

#### 使用Poetry（推荐）

```bash
# 安装Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 激活环境
poetry shell

# 启动开发服务器
poetry run uvicorn app.main:app --reload --port 8000
```

#### 使用pip

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000
```

### 6.2 代码规范

```bash
# 代码格式化
poetry run black .
poetry run isort .
poetry run ruff check . --fix

# 运行测试
poetry run pytest

# 生成覆盖率报告
poetry run pytest --cov=app tests/
```

### 6.3 项目特点

#### 简化架构优势
1. **减少代码层级**：去除DAO层，Service直接操作数据库
2. **降低维护成本**：更少的抽象层级，更直观的代码逻辑
3. **提高开发效率**：减少样板代码，专注业务实现
4. **易于理解**：新开发者更容易理解代码结构

#### 类型安全特性
1. **SQLModel集成**：数据库模型和API模型统一
2. **FastAPI验证**：自动参数验证和文档生成
3. **全面类型提示**：提高代码质量和IDE支持

## 7. 监控与维护

### 7.1 健康检查

系统提供多层级的健康检查：

- **应用级**：`GET /health` - 基础健康状态
- **数据库级**：连接状态和查询性能
- **调度器级**：任务执行状态和队列状态
- **Docker级**：容器健康检查配置

### 7.2 日志管理

```bash
# 查看容器日志
docker-compose logs -f jjcrawler

# 查看特定时间段日志
docker-compose logs --since="2024-01-01T00:00:00" jjcrawler

# 系统服务日志
sudo journalctl -u jjcrawler -f
```

### 7.3 数据备份

```bash
# 备份数据目录
tar -czf backup-$(date +%Y%m%d).tar.gz data/

# 恢复数据
tar -xzf backup-20240101.tar.gz
```

## 8. 常见问题

### 8.1 部署相关

**Q: Docker容器启动失败？**
```bash
# 检查日志
docker-compose logs jjcrawler

# 检查端口占用
lsof -i :8000

# 重新构建镜像
docker-compose build --no-cache
```

**Q: 数据库权限问题？**
```bash
# 确保数据目录权限
chmod 755 data/
chown -R 1000:1000 data/  # Docker用户
```

### 8.2 功能相关

**Q: 爬虫任务不执行？**
- 检查调度器状态：`GET /api/v1/crawl/status`
- 查看任务日志：`docker-compose logs -f jjcrawler`
- 手动触发测试：`POST /api/v1/crawl/all`

**Q: API响应慢？**
- 检查数据库查询性能
- 考虑添加适当的索引
- 调整查询参数（如limit大小）

## 9. 技术架构优势

### 9.1 简化架构的益处

1. **开发效率**：更少的抽象层级，更快的功能实现
2. **维护成本**：代码结构清晰，故障排查简单
3. **学习成本**：新开发者容易理解和上手
4. **性能优化**：减少中间层，提高执行效率

### 9.2 现代化技术栈

1. **FastAPI**：高性能、自动文档、类型安全
2. **SQLModel**：SQLAlchemy + Pydantic的完美结合
3. **Docker**：标准化部署，环境一致性
4. **异步支持**：全面的async/await实现

## 10. 后续发展规划

### 10.1 功能增强
- 数据分析报告生成
- 实时数据推送
- 用户个性化推荐
- 多数据源支持

### 10.2 技术升级
- 引入缓存层（Redis）
- 数据库迁移方案（PostgreSQL）
- 微服务拆分
- 监控告警系统

## 11. 联系方式

- **项目负责人**：Lien Gu
- **技术支持**：guliyu0216@163.com
- **项目仓库**：https://github.com/lien-Gu/JJClawler-full.git
- **问题反馈**：GitHub Issues

---

*本文档最后更新时间：2024年*