# 晋江文学城爬虫后端项目

## 1. 项目概述

### 1.1 项目简介
JJCrawler 是一个基于 FastAPI 的现代化晋江文学城数据爬虫后端服务。项目采用简化的架构设计，专注于榜单数据采集、存储和API服务，为前端应用提供稳定可靠的数据接口。

### 1.2 核心特性
- **简化架构设计**：去除DAO层，Service层直接操作数据库，减少代码复杂性
- **高效数据处理**：基于SQLite + SQLAlchemy的轻量级解决方案
- **自动化爬取**：支持APScheduler定时任务和手动触发
- **类型安全**：全面使用FastAPI实现类型检查
- **模块化设计**：功能模块独立，易于维护和扩展
- **容器化部署**：提供完整的Docker部署方案

### 1.3 技术栈
- **后端框架**：FastAPI ^0.115.0
- **数据库**：SQLite + SQLAlchemy ^0.0.22
- **任务调度**：APScheduler ^3.10.4
- **HTTP客户端**：httpx ^0.28.0
- **异步支持**：aiosqlite ^0.21.0
- **依赖管理**：uv
- **容器化**：Docker + docker-compose

## 2. 项目结构

### 2.1 后端代码目录结构

```
backend/
├── app/                          # 主应用目录
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理
│   ├── logger.py                 # 日志配置
│   ├── utils.py                  # 通用工具函数
│   ├── api/                      # API接口模块
│   │   ├── __init__.py
│   │   ├── books.py              # 书籍相关接口
│   │   ├── rankings.py           # 榜单相关接口
│   │   └── schedule.py           # 任务调度接口
│   ├── crawl/                    # 爬虫模块
│   │   ├── __init__.py
│   │   ├── crawl_config.py       # 爬虫配置管理
│   │   ├── crawl_flow.py         # 并发爬取流程管理
│   │   ├── http.py               # HTTP客户端
│   │   ├── parser.py             # 数据解析器
│   │   ├── data/                 # 爬取数据存储
│   │   └── logs/                 # 爬取日志
│   ├── database/                 # 数据库模块
│   │   ├── __init__.py
│   │   ├── connection.py         # 数据库连接管理
│   │   ├── db/                   # 数据模型定义
│   │   │   ├── __init__.py
│   │   │   ├── base.py           # 基础模型类
│   │   │   ├── book.py           # 书籍数据模型
│   │   │   └── ranking.py        # 榜单数据模型
│   │   ├── service/              # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── Base.py           # 基础服务类
│   │   │   ├── book_service.py   # 书籍业务逻辑
│   │   │   └── ranking_service.py # 榜单业务逻辑
│   │   └── sql/                  # SQL查询模块
│   │       ├── __init__.py
│   │       ├── book_queries.py   # 书籍查询语句
│   │       └── ranking_queries.py # 榜单查询语句
│   ├── models/                   # API数据模型
│   │   ├── __init__.py
│   │   ├── base.py               # 基础响应模型
│   │   ├── book.py               # 书籍API模型
│   │   ├── ranking.py            # 榜单API模型
│   │   ├── error.py              # 错误响应模型
│   │   └── schedule.py           # 调度API模型
│   ├── schedule/                 # 任务调度模块
│   │   ├── __init__.py
│   │   ├── scheduler.py          # 任务调度器
│   │   └── listener.py           # 任务事件监听器
│   └── middleware/               # 中间件模块
│       ├── __init__.py
│       └── exception_middleware.py # 异常处理中间件
├── data/                         # 数据存储目录
│   └── urls.json                 # 爬取配置文件
├── tests/                        # 测试用例目录
│   ├── conftest.py               # 测试配置
│   ├── test_api/                 # API接口测试
│   ├── test_crawl/               # 爬虫模块测试
│   ├── test_database/            # 数据库模块测试
│   └── test_schedule/            # 调度模块测试
├── docs/                         # 项目文档
│   ├── API.md                    # API接口文档
│   └── issues.md                 # 问题记录文档
├── scripts/                      # 脚本文件
├── Dockerfile                    # Docker镜像配置
├── docker-compose.yml            # Docker编排配置
├── pyproject.toml                # 项目依赖配置（uv管理）
└── README.md                     # 项目文档
```

### 2.2 各模块功能说明

#### 2.2.1 API模块 (app/api/)
**功能职责**：提供RESTful API接口，处理HTTP请求和响应

**核心文件**：
- **books.py**：书籍相关接口
  - 书籍列表查询、详情获取
  - 书籍数据趋势分析
  - 书籍排名历史查询
- **rankings.py**：榜单相关接口
  - 榜单列表查询、详情获取
  - 榜单历史数据查询
- **schedule.py**：任务调度接口
  - 创建爬取任务
  - 获取调度器状态

#### 2.2.2 爬虫模块 (app/crawl/)
**功能职责**：实现网页数据爬取和解析

**核心文件**：
- **crawl_config.py**：爬虫配置管理，包括URL配置和请求参数
- **crawl_flow.py**：并发爬取流程管理器，实现两阶段处理架构
  - 阶段1：并发获取页面内容
  - 阶段2：并发获取书籍详情
  - 阶段3：批量保存数据
- **http.py**：HTTP客户端，支持连接池和请求控制
- **parser.py**：数据解析器，支持多种页面类型的数据提取

**技术特点**：
- **统一并发控制**：使用信号量控制全局最大并发请求数
- **智能重试策略**：根据错误类型调整重试延迟
- **两阶段处理**：分离页面获取和书籍获取，优化资源利用

#### 2.2.3 数据库模块 (app/database/)
**功能职责**：数据模型定义和业务逻辑处理

**架构特点**：
- **SQLAlchemy + SQLite**：轻量级数据库解决方案
- **类型安全**：完整的类型注解和Mapped类型支持
- **异步支持**：全面支持异步数据库操作

**核心组件**：
- **db/模型定义**：
  - `base.py`：基础模型类，包含通用时间戳字段
  - `book.py`：书籍基础信息表和动态统计快照表
  - `ranking.py`：榜单配置表和排名快照表
- **service/业务逻辑**：封装CRUD操作和复杂查询逻辑
- **dao/数据访问层**：数据访问对象接口
- **sql/查询模块**：复杂SQL查询语句封装
- **connection.py**：数据库连接池管理

#### 2.2.4 调度模块 (app/schedule/)
**功能职责**：任务调度和自动化爬取

**核心文件**：
- **scheduler.py**：基于APScheduler 3.x的任务调度器
  - 支持定时任务和手动任务
  - 事件驱动的任务监控
  - 智能任务清理机制
- **listener.py**：任务事件监听器
  - 专注任务失败日志记录
  - 详细的错误信息收集

**技术特点**：
- **简化架构**：移除metadata存储，专注任务执行
- **事件驱动**：使用APScheduler事件系统监控任务状态
- **自动清理**：定期清理已完成的一次性任务

#### 2.2.5 数据模型 (app/models/)
**功能职责**：API请求响应模型定义

**核心特点**：
- 使用Pydantic进行数据验证和类型检查
- 统一的响应格式（DataResponse、ListResponse）
- 类型安全的API接口定义

**核心文件**：
- **base.py**：基础响应模型和通用数据结构
- **book.py**：书籍API模型和请求响应类型
- **ranking.py**：榜单API模型和查询参数类型
- **schedule.py**：任务调度API模型
- **error.py**：错误响应模型和异常处理类型

#### 2.2.6 中间件模块 (app/middleware/)
**功能职责**：请求响应处理和异常管理

**核心文件**：
- **exception_middleware.py**：全局异常处理中间件
  - 统一异常响应格式
  - 详细错误日志记录
  - 友好的用户错误提示

## 3. 数据库设计

### 3.1 数据库架构

采用SQLite + SQLAlchemy的轻量级解决方案，设计四个核心表实现完整的数据存储：

#### 3.1.1 核心表结构

**books表 - 书籍基础信息**
```sql
CREATE TABLE books (
    novel_id INTEGER PRIMARY KEY,           -- 书籍唯一标识ID（晋江文学城小说ID）
    title VARCHAR(200) NOT NULL,            -- 书籍标题
    author_id INTEGER NOT NULL,             -- 作者唯一标识ID（晋江文学城作者ID）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_book_title ON books(title);
CREATE INDEX idx_book_author ON books(author_id);
```

**book_snapshots表 - 书籍动态统计快照**
```sql
CREATE TABLE book_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER NOT NULL,             -- 关联books.novel_id
    favorites INTEGER DEFAULT 0,           -- 收藏数量
    clicks INTEGER DEFAULT 0,              -- 非V章点击量
    comments INTEGER DEFAULT 0,            -- 评论数量
    nutrition INTEGER DEFAULT 0,           -- 营养液数量
    word_counts INTEGER,                   -- 字数统计
    chapter_counts INTEGER,                -- 章节统计
    vip_chapter_id INTEGER,                -- 入V章节ID（0表示未入V）
    status VARCHAR(50),                    -- 书籍状态（连载中/已完结等）
    snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (novel_id) REFERENCES books(novel_id)
);

-- 复合索引优化查询性能
CREATE INDEX idx_book_snapshot_time ON book_snapshots(novel_id, snapshot_time);
CREATE INDEX idx_book_snapshot_novel ON book_snapshots(novel_id, snapshot_time);
```

**rankings表 - 榜单配置信息**
```sql
CREATE TABLE rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rank_id VARCHAR(100) NOT NULL,         -- 榜单唯一标识ID
    channel_name VARCHAR(100) NOT NULL,    -- 榜单中文名称
    rank_group_type VARCHAR(50),           -- 榜单分组类型
    channel_id VARCHAR(50),                -- 频道ID
    page_id VARCHAR(50) NOT NULL,          -- 页面标识ID
    sub_channel_name VARCHAR(100),         -- 子榜单名称
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 多字段索引优化
CREATE INDEX idx_ranking_rank_id ON rankings(rank_id);
CREATE INDEX idx_ranking_channel_name ON rankings(channel_name);
CREATE INDEX idx_ranking_page_id ON rankings(page_id);
CREATE INDEX idx_ranking_group_type ON rankings(rank_group_type);
```

**ranking_snapshots表 - 榜单排名快照**
```sql
CREATE TABLE ranking_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ranking_id INTEGER NOT NULL,           -- 关联rankings.id
    novel_id INTEGER NOT NULL,             -- 关联books.novel_id
    batch_id VARCHAR(36) NOT NULL,         -- 批次ID（UUID）
    position INTEGER NOT NULL,             -- 排名位置（从1开始）
    snapshot_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ranking_id) REFERENCES rankings(id),
    FOREIGN KEY (novel_id) REFERENCES books(novel_id),
    
    -- 唯一约束：同一批次中同一榜单每本书只有一个排名
    UNIQUE(ranking_id, novel_id, batch_id)
);

-- 复合索引和约束优化
CREATE INDEX idx_ranking_snapshot_time ON ranking_snapshots(ranking_id, snapshot_time);
CREATE INDEX idx_ranking_snapshot_position ON ranking_snapshots(ranking_id, position, snapshot_time);
CREATE INDEX idx_book_ranking_snapshot ON ranking_snapshots(novel_id, ranking_id, snapshot_time);
CREATE INDEX idx_ranking_batch_id ON ranking_snapshots(batch_id);
```

### 3.2 数据模型特点

#### 3.2.1 设计原则
- **数据分离**：静态基础信息与动态统计数据分表存储
- **时间序列**：快照表支持历史数据查询和趋势分析
- **批次控制**：使用batch_id确保同一时间点数据的一致性
- **索引优化**：基于实际查询模式设计复合索引

#### 3.2.2 技术实现
- **SQLAlchemy ORM**：使用现代化的ORM框架
- **类型安全**：完整的Mapped类型注解
- **约束完整**：外键约束和唯一约束保证数据完整性
- **性能优化**：合理的索引设计提升查询性能

#### 3.2.3 扩展性设计
- **灵活的榜单结构**：支持多种榜单类型和分组
- **完整的快照机制**：支持任意时间点的数据回溯
- **批次数据管理**：确保同一爬取任务数据的时间一致性
- **轻量级部署**：SQLite适合中小型项目快速部署

### 3.3 数据关系图

```
books (书籍基础信息)
├── novel_id (PK) → book_snapshots.novel_id (FK)
├── title            ranking_snapshots.novel_id (FK)
├── author_id    
└── timestamps   

book_snapshots (书籍统计快照)     rankings (榜单配置)
├── novel_id (FK)              ├── id (PK) → ranking_snapshots.ranking_id (FK)
├── favorites                  ├── rank_id
├── clicks                     ├── channel_name
├── comments                   ├── page_id
├── nutrition                  └── timestamps
├── word_counts                
├── status                     ranking_snapshots (榜单排名快照)
└── snapshot_time              ├── ranking_id (FK)
                               ├── novel_id (FK)
                               ├── batch_id
                               ├── position
                               └── snapshot_time
```

## 4. 部署和运行指导

项目提供了完整的本地开发和生产部署解决方案，支持Windows本地部署和Docker容器化部署。

### 4.1 本地Windows部署运行

#### 4.1.1 环境要求
- **Python**: 3.12+
- **包管理器**: uv（推荐）或 Poetry
- **操作系统**: Windows 10/11

#### 4.1.2 使用uv快速部署（推荐）

```bash
# 1. 安装uv包管理器
pip install uv

# 2. 克隆项目
git clone https://github.com/lien-Gu/JJClawler-full.git
cd JJClawler-full/backend

# 3. 安装依赖
uv sync

# 4. 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000

# 5. 验证部署
# 浏览器访问: http://localhost:8000/docs
curl http://localhost:8000/health
```


### 4.2 Docker部署指南

#### 4.2.1 环境要求

**系统要求**：
- Docker 20.0+
- Docker Compose 2.0+
- 可用内存：2GB+
- 可用存储：5GB+
- Linux

#### 4.2.2 快速部署

**Docker Compose部署（推荐）**

```bash
# 1. 克隆项目
git clone https://github.com/lien-Gu/JJClawler-full.git
cd JJClawler-full/backend

# 2. 启动服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f jjcrawler

# 5. 停止服务
docker-compose down
```


#### 4.2.3 部署验证

```bash
# 1. 健康检查
curl http://localhost:8000/health
# 预期响应: {"status": "ok"}

# 2. 查看API文档
# 浏览器访问: http://localhost:8000/docs

# 3. 测试调度接口
curl -X POST "http://localhost:8000/api/v1/schedule/task/create?page_ids=jiazi"
curl http://localhost:8000/api/v1/schedule/status
```

#### 4.2.4 环境配置

```bash
# 查看当前环境变量
docker exec jjcrawler env | grep -E "(DEBUG|DATABASE|CORS)"

# 自定义环境变量（可选）
cat > .env.local << EOF
DEBUG=false
DATABASE_URL=sqlite:///./data/jjcrawler.db
CORS_ORIGINS=*
MAX_CONCURRENT_REQUESTS=8
EOF

# 使用自定义环境变量启动
docker-compose --env-file .env.local up -d
```

#### 4.2.5 生产环境部署

**Nginx反向代理配置**

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 静态文件缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

**系统服务配置**

```bash
# 创建systemd服务文件
sudo vim /etc/systemd/system/jjcrawler.service

# 服务文件内容:
[Unit]
Description=JJ Crawler Backend Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=root
WorkingDirectory=/path/to/JJClawler-full/backend
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target

# 启用服务
sudo systemctl enable jjcrawler
sudo systemctl start jjcrawler
```

### 4.3 数据备份和恢复

```bash
# 备份数据目录
tar -czf jjcrawler-backup-$(date +%Y%m%d).tar.gz data/

# Docker容器数据备份
docker run --rm -v jjcrawler-data:/data -v $(pwd):/backup alpine \
  tar czf /backup/jjcrawler-data-$(date +%Y%m%d).tar.gz -C /data .

# 恢复数据
tar -xzf jjcrawler-backup-20240101.tar.gz
```

## 5. 开发指南

### 5.1 开发环境搭建

**使用uv（推荐）**

```bash
# 克隆项目
git clone https://github.com/lien-Gu/JJClawler-full.git
cd JJClawler-full/backend

# 安装依赖
uv sync

# 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000
```

### 5.2 代码规范

```bash
# 代码格式化
uv run black .
uv run isort .
uv run ruff check . --fix

# 运行测试
uv run pytest

# 生成覆盖率报告
uv run pytest --cov=app tests/
```

### 5.3 技术特点

**架构优势**：
- **两阶段爬取**：分离页面获取和书籍获取，优化并发性能
- **统一并发控制**：信号量统一管理所有HTTP请求
- **事件驱动调度**：APScheduler事件系统监控任务状态
- **类型安全**：SQLAlchemy + Pydantic完整类型支持

**性能优化**：
- **智能重试**：根据错误类型调整重试策略
- **连接池复用**：HTTP客户端连接池优化
- **数据库索引**：基于查询模式的复合索引设计
- **异步处理**：全面的async/await异步支持

## 6. API文档

完整的API接口文档请参考：[docs/API.md](docs/API.md)

主要接口包括：
- **调度任务管理**：创建任务、获取调度器状态
- **书籍数据查询**：书籍列表、详情、趋势分析
- **榜单数据查询**：榜单列表、历史数据

## 7. 监控与维护

### 7.1 健康检查

```bash
# 应用健康检查
curl http://localhost:8000/health

# 调度器状态检查
curl http://localhost:8000/api/v1/schedule/status

# 容器状态检查
docker-compose ps
```

### 7.2 日志管理

```bash
# 查看应用日志
docker-compose logs -f jjcrawler

# 查看特定时间段日志
docker-compose logs --since="2024-01-01T00:00:00" jjcrawler

# 系统服务日志
sudo journalctl -u jjcrawler -f
```

### 7.3 常见问题

**Q: 调度任务不执行？**
- 检查调度器状态和任务队列
- 查看容器日志排查错误
- 验证页面配置文件`data/urls.json`

**Q: API响应慢？**
- 检查数据库索引是否生效
- 调整并发请求数配置
- 考虑添加缓存层

**Q: Docker容器启动失败？**
- 检查端口占用情况
- 验证数据目录权限
- 重新构建镜像

## 8. 联系方式

- **项目仓库**：https://github.com/lien-Gu/JJClawler-full.git
- **问题反馈**：GitHub Issues
- **API文档**：`http://localhost:8000/docs`

---

*本文档最后更新时间：2025年8月*