# 晋江文学城爬虫后端项目设计文档

## 1. 项目概述

### 1.1 项目背景
晋江文学城是国内知名的网络文学平台，拥有大量的小说作品和活跃的读者群体。本项目旨在开发一个数据爬虫后端服务，用于采集平台上的榜单数据和小说信息，为作者和读者提供数据分析基础。

### 1.2 项目目标
- 实现自动化的榜单数据采集
- 提供RESTful API接口供前端调用
- 支持定时任务和手动触发
- 确保系统稳定性和数据准确性
- 快速完成MVP验证项目可行性

### 1.3 项目范围
- **包含**：榜单爬取、小说信息爬取、数据存储、API服务、定时调度
- **不包含**：前端界面、数据分析功能、用户系统

## 2. 需求分析

### 2.1 功能需求

#### 2.1.1 数据爬取需求
| 功能模块 | 需求描述 | 优先级 |
|---------|---------|--------|
| 夹子榜单爬取 | 每小时更新一次夹子榜单数据 | P0 |
| 分类榜单爬取 | 按配置频率爬取各分类榜单（言情、纯爱、衍生等） | P0 |
| 小说详情爬取 | 爬取榜单中小说的详细信息 | P0 |
| 增量更新 | 仅爬取新增或变化的数据 | P2 |

#### 2.1.2 API接口需求
| 接口类型 | 功能描述 | 优先级 |
|---------|---------|--------|
| 榜单查询 | 查询历史榜单数据、最新榜单 | P0 |
| 小说查询 | 查询小说列表、小说详情 | P0 |
| 任务管理 | 查看爬取任务状态、手动触发爬取 | P1 |
| 统计信息 | 系统运行统计、数据统计 | P1 |

### 2.2 非功能需求

| 需求类型 | 具体要求 | 备注 |
|---------|---------|------|
| 性能要求 | 支持每小时处理1000+请求 | 2C4G服务器限制 |
| 可靠性 | 系统可用性>95%，支持断点续爬 | - |
| 安全性 | 遵守robots协议，控制请求频率 | 避免被封禁 |
| 可维护性 | 代码简洁易读，模块化设计 | 便于后续扩展 |
| 部署要求 | 支持Docker容器化部署 | Linux环境 |

### 2.3 数据需求

#### 2.3.1 爬取数据结构

参考data/example中的文件

## 3. 系统架构设计

### 3.1 技术选型

| 技术栈 | 选择 | 选择理由 |
|--------|------|----------|
| 编程语言 | Python 3.13+ | 爬虫生态成熟，开发效率高 |
| Web框架 | FastAPI | 高性能，自动生成API文档，类型安全 |
| HTTP库 | httpx | 异步支持，性能更好 |
| 数据库 | SQLite | 轻量级，无需额外部署，适合中小型项目 |
| ORM | SQLModel | 类型安全，与FastAPI无缝集成，代码简洁 |
| 任务调度 | APScheduler | 轻量级Python调度器，支持异步 |
| 依赖管理 | Poetry | 现代Python包管理工具 |

#### 3.1.1 SQLModel vs SQLAlchemy 选择分析

**选择SQLModel的原因：**
- **类型安全**：基于Pydantic，提供完整的类型检查
- **代码简洁**：同一个类定义数据库模型和API模型，减少重复代码
- **FastAPI原生**：同一作者开发，无缝集成，开发体验一致
- **现代设计**：基于Python 3.7+类型注解，符合项目技术栈

**SQLAlchemy的优势但不适用于本项目：**
- 更成熟的生态系统（本项目为MVP，不需要复杂功能）
- 更丰富的文档（SQLModel文档已足够）
- 更多的社区支持（项目规模较小，遇到复杂问题概率低）

### 3.2 基于接口驱动的模块化架构

```
┌─────────────────────────────────────────────────────┐
│                  API接口层                           │
│              (定义所有对外接口)                       │
└─────────────────────────────────────────────────────┘
                            │
                    根据接口确定功能模块
                            ▼
┌─────────────────────────────────────────────────────┐
│                  功能模块层                          │
│   爬虫模块    数据模块    统计模块    任务模块        │
└─────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────┐
│                  工具支持层                          │
│      HTTP工具   文件工具   时间工具   日志工具       │
└─────────────────────────────────────────────────────┘
```

### 3.3 标准四层架构设计（已实现）

项目采用经典的四层架构模式，职责分明、结构清晰。**T3重构已完成**，实现了标准的enterprise级架构：

```
JJClawer3/
├── app/
│   ├── __init__.py
│   ├── main.py                   # FastAPI应用入口
│   ├── config.py                 # 配置管理
│   ├── api/                      # ✅ API路由层（已重构）
│   │   ├── __init__.py
│   │   ├── pages.py              # ✅ 页面配置接口（静态配置）
│   │   ├── rankings.py           # ✅ 榜单相关接口（依赖注入）
│   │   ├── books.py              # ✅ 书籍相关接口（依赖注入）
│   │   └── crawl.py              # 爬虫管理接口（待实现）
│   └── modules/                  # ✅ 核心业务模块（四层架构已实现）
│       ├── database/             # ✅ Database层：数据库连接管理
│       │   ├── __init__.py       # ✅ 统一导出接口
│       │   └── connection.py     # ✅ 连接池、会话管理、表创建、SQLite优化
│       ├── models/               # ✅ Model层：数据模型定义（按领域拆分）
│       │   ├── __init__.py       # ✅ 统一导出接口
│       │   ├── base.py           # ✅ 基础类型和枚举
│       │   ├── book.py           # ✅ Book + BookSnapshot领域模型
│       │   ├── ranking.py        # ✅ Ranking + RankingSnapshot领域模型
│       │   └── api.py            # ✅ API请求响应模型
│       ├── dao/                  # ✅ DAO层：数据访问对象（按领域拆分）
│       │   ├── __init__.py       # ✅ 统一导出接口
│       │   ├── book_dao.py       # ✅ Book数据访问（CRUD + 复杂查询）
│       │   └── ranking_dao.py    # ✅ Ranking数据访问（CRUD + 复杂查询）
│       ├── service/              # ✅ Service层：业务逻辑（按领域拆分）
│       │   ├── __init__.py       # ✅ 统一导出接口
│       │   ├── book_service.py   # ✅ Book业务逻辑（含空数据处理）
│       │   └── ranking_service.py # ✅ Ranking业务逻辑（含空数据处理）
│       ├── crawler.py            # 爬虫模块（待实现）
│       └── task_service.py       # 任务管理（待实现）
├── data/
│   ├── urls.json                 # 爬取配置
│   ├── tasks/                    # 任务JSON文件存储
│   │   ├── tasks.json           # 当前任务状态
│   │   └── history/             # 历史任务记录
│   └── example/                  # 示例数据
├── tests/                        # 测试目录
├── pyproject.toml
└── .env.example
```

#### 3.3.1 四层架构详解（T3重构实现）

**🏗️ Database层（已实现）**
- **职责**：数据库连接管理、会话控制、表创建
- **文件**：`modules/database/connection.py`
- **功能**：SQLite连接池、PRAGMA优化、事务管理、健康检查
- **特性**：WAL模式、64MB缓存、外键约束、自动表创建

**📊 Model层（已实现）**
- **职责**：数据模型定义、类型约束、关系映射
- **文件**：`modules/models/`（按业务领域拆分）
  - `base.py`：基础枚举和类型定义
  - `book.py`：Book + BookSnapshot模型（静态+动态数据分离）
  - `ranking.py`：Ranking + RankingSnapshot模型（配置+快照数据）
  - `api.py`：API请求响应模型（完整业务模型）
- **设计**：SQLModel双重用途（数据库+API模型）

**🔧 DAO层（已实现）**
- **职责**：数据访问对象、CRUD操作、复杂查询
- **文件**：`modules/dao/`（按业务领域拆分）
  - `book_dao.py`：Book数据访问封装（搜索、快照、趋势）
  - `ranking_dao.py`：Ranking数据访问封装（榜单、历史、统计）
- **特性**：会话管理、复合查询、批量操作、资源清理

**⚙️ Service层（已实现）**
- **职责**：业务逻辑组合、事务控制、数据转换
- **文件**：`modules/service/`（按业务领域拆分）
  - `book_service.py`：Book业务逻辑（详情、搜索、趋势、排名历史）
  - `ranking_service.py`：Ranking业务逻辑（榜单、历史、排名变化）
- **特性**：DAO组合、空数据处理、业务模型转换、依赖注入支持

**🌐 API层（已实现）**
- **职责**：HTTP接口、参数验证、响应格式化
- **文件**：`api/`（按功能模块拆分）
  - `pages.py`：静态页面配置（无数据库依赖）
  - `books.py`：书籍相关接口（依赖注入BookService）
  - `rankings.py`：榜单相关接口（依赖注入RankingService）
- **特性**：FastAPI依赖注入、自动资源清理、Pydantic验证

#### 3.3.2 T3重构架构优势

**🔄 分层解耦（已实现）**
- 每层职责单一，修改影响最小化
- 支持单元测试和集成测试
- 便于团队协作开发
- API -> Service -> DAO -> Database清晰调用链

**🚀 高可扩展性（已实现）**
- 按业务领域拆分（Book vs Ranking），便于功能扩展
- Service层可独立复用，支持不同API调用
- DAO层支持多数据源切换（当前SQLite，可扩展至PostgreSQL）
- 依赖注入支持Mock测试和替换实现

**💡 代码复用（已实现）**
- SQLModel双重用途（数据库+API模型），减少重复定义
- 统一的依赖注入机制，自动资源管理
- 标准化的异常处理和日志记录
- 模块化导出，易于import和使用

**🛡️ 数据安全（已实现）**
- 数据库事务控制，确保数据一致性
- SQL注入防护（SQLModel ORM）
- 连接池管理，避免连接泄漏
- 会话自动清理，防止资源占用

**📈 性能优化（已实现）**
- SQLite WAL模式，提升并发性能
- 64MB缓存配置，加速查询
- 复合索引设计，优化常用查询场景
- 空数据早期返回，避免无效计算

**🔧 开发体验（已实现）**
- 减少数据库表数量，降低复杂度
- 任务管理独立（JSON文件），不影响核心业务数据
- 便于调试和手动干预任务状态
- 完整的类型提示和IDE支持

### 3.4 数据库设计

#### 3.4.1 表结构设计

**核心表设计思路：**
- **rankings**：榜单配置表，存储榜单元数据
- **books**：书籍信息表，存储书籍基础信息
- **ranking_snapshots**：榜单快照表，存储时间序列数据（核心表）
- **crawl_tasks**：爬取任务表，存储任务状态和历史

**关键设计决策：**
1. **时间序列存储**：使用snapshot模式，每次爬取创建新快照
2. **查询优化**：针对常用查询场景创建复合索引
3. **数据完整性**：通过外键约束保证数据一致性

#### 3.4.2 SQLite优化配置

```python
# 针对爬虫项目的SQLite优化
SQLITE_PRAGMAS = {
    "journal_mode": "WAL",  # 写前日志，提高并发写入性能
    "cache_size": -64000,   # 64MB缓存，适合频繁查询
    "synchronous": "NORMAL", # 平衡性能和数据安全
    "foreign_keys": "ON",   # 启用外键约束
    "temp_store": "MEMORY", # 临时表存内存，加速复杂查询
}
```

#### 3.4.3 核心数据模型设计

**优化方案：增加BookSnapshot表存储书籍动态信息**

基于分析，书籍信息分为两类：
- **静态信息**：title, author等基本不变的信息
- **动态信息**：点击量、收藏量等随时间变化的统计信息

为支持"书籍变化情况"分析需求，采用以下设计：

```python
from sqlmodel import SQLModel, Field, Index
from datetime import datetime
from typing import Optional
from enum import Enum

class UpdateFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"

# 1. 榜单配置表
class Ranking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ranking_id: str = Field(unique=True, index=True)
    name: str  # 中文名
    channel: str  # API频道参数
    frequency: UpdateFrequency
    update_interval: int
    parent_id: Optional[str] = Field(default=None)  # 父级榜单

# 2. 书籍表（仅静态信息）
class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: str = Field(unique=True, index=True)
    title: str
    author_id: str = Field(index=True)
    author_name: str = Field(index=True)
    novel_class: Optional[str] = None
    tags: Optional[str] = None  # JSON字符串
    first_seen: datetime = Field(default_factory=datetime.now)
    last_updated: datetime = Field(default_factory=datetime.now)

# 3. 书籍快照表（存储书籍级别的动态信息）
class BookSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: str = Field(foreign_key="book.book_id", index=True)
    total_clicks: Optional[int] = None  # 总点击量
    total_favorites: Optional[int] = None  # 总收藏量
    comment_count: Optional[int] = None  # 评论数
    chapter_count: Optional[int] = None  # 章节数
    snapshot_time: datetime = Field(index=True)
    
    __table_args__ = (
        Index("idx_book_snapshot_time", "book_id", "snapshot_time"),
    )

# 4. 榜单快照表（存储榜单维度的数据）
class RankingSnapshot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ranking_id: str = Field(foreign_key="ranking.ranking_id", index=True)
    book_id: str = Field(foreign_key="book.book_id", index=True)
    position: int  # 榜单位置
    snapshot_time: datetime = Field(index=True)
    
    # 榜单期间的统计（可能与书籍总统计不同）
    ranking_clicks: Optional[int] = None  # 在榜期间点击量
    ranking_favorites: Optional[int] = None  # 在榜期间收藏量
    
    __table_args__ = (
        Index("idx_ranking_time", "ranking_id", "snapshot_time"),
        Index("idx_book_ranking_time", "book_id", "snapshot_time"),
        Index("idx_ranking_position", "ranking_id", "position", "snapshot_time"),
    )

# 注：任务管理不使用数据库，采用JSON文件存储
# 任务信息存储在 data/tasks/tasks.json 中
```

#### 3.4.4 设计优势分析

**数据存储设计：**
- **数据库存储**：Book、BookSnapshot、RankingSnapshot、Ranking四个表
- **文件存储**：任务管理使用JSON文件存储在data/tasks/目录
- **配置存储**：urls.json存储爬取配置信息

**查询场景优化：**
```sql
-- 书籍趋势分析
SELECT snapshot_time, total_clicks, total_favorites, comment_count, chapter_count
FROM BookSnapshot 
WHERE book_id = ? AND snapshot_time >= ?

-- 书籍榜单历史
SELECT r.name, rs.position, rs.snapshot_time
FROM RankingSnapshot rs JOIN Ranking r ON rs.ranking_id = r.ranking_id
WHERE rs.book_id = ?

-- 榜单当前快照
SELECT book_id, position, snapshot_time
FROM RankingSnapshot 
WHERE ranking_id = ? AND snapshot_time = (
    SELECT MAX(snapshot_time) FROM RankingSnapshot WHERE ranking_id = ?
)
ORDER BY position
```

## 4. 详细设计

### 4.1 API接口优先设计

根据需求分析，按优先级定义接口：

#### 4.1.1 核心业务接口设计

基于数据库结构，重新设计核心API接口：

**1. 页面配置接口**
```
GET /api/v1/pages
功能: 获取所有榜单页面配置（固定数据）
响应: {
  "pages": [
    {"page_id": "yq", "name": "言情", "rankings": [...]},
    {"page_id": "ca", "name": "纯爱", "rankings": [...]}
  ]
}
```

**2. 榜单接口**
```
GET /api/v1/rankings/{ranking_id}/books
功能: 获取特定榜单的书籍列表及排名变化
参数: date (可选), limit, offset
响应: {
  "ranking": {"id": "jiazi", "name": "夹子"},
  "snapshot_time": "2024-01-01T12:00:00Z",
  "books": [
    {
      "book_id": "123", "title": "书名", "author": "作者",
      "position": 1, "clicks": 1000, "favorites": 500,
      "position_change": "+2"  // 相比上次的排名变化
    }
  ]
}

GET /api/v1/rankings/{ranking_id}/history
功能: 获取榜单历史快照数据
参数: days (默认7天)
响应: {"snapshots": [{"snapshot_time": "...", "total_books": 50}]}
```

**3. 书籍接口**
```
GET /api/v1/books/{book_id}
功能: 获取书籍详细信息
响应: {book基础信息 + 最新统计数据}

GET /api/v1/books/{book_id}/rankings
功能: 获取书籍出现在哪些榜单中及历史表现
响应: {
  "book": {"book_id": "123", "title": "书名"},
  "current_rankings": [
    {"ranking_id": "jiazi", "position": 5, "snapshot_time": "..."}
  ],
  "history": [...]
}

GET /api/v1/books/{book_id}/trends
功能: 获取书籍点击量、收藏量变化趋势
参数: days (默认30天)
响应: {
  "trends": [
    {"date": "2024-01-01", "clicks": 1000, "favorites": 500},
    {"date": "2024-01-02", "clicks": 1200, "favorites": 520}
  ]
}
```

**4. 爬虫管理接口**
```
POST /api/v1/crawl/jiazi
功能: 触发夹子榜单爬取
响应: {"task_id": "xxx", "message": "Task started"}

POST /api/v1/crawl/ranking/{ranking_id}
功能: 触发特定榜单爬取
响应: {"task_id": "xxx", "message": "Task started"}

GET /api/v1/tasks
功能: 获取爬取任务状态
响应: {"tasks": [{"task_id": "xxx", "status": "running", "progress": "50%"}]}
```

### 4.2 基于接口的功能模块拆分

根据上述接口设计，将功能拆分为以下独立模块：

#### 4.2.1 爬虫模块 (modules/crawler.py)
**负责接口**: `/api/v1/crawl/*`
**核心功能**:
- 夹子榜单爬取
- 分类榜单爬取  
- 数据解析和存储
- 异常处理和重试

#### 4.2.2 数据服务模块 (modules/data_service.py)
**负责接口**: `/api/v1/rankings/*`, `/api/v1/novels/*`
**核心功能**:
- 榜单数据查询和过滤
- 小说信息查询
- 数据分页处理
- JSON文件读取优化

#### 4.2.3 任务管理模块 (modules/task_service.py)
**负责接口**: `/api/v1/tasks/*`
**核心功能**:
- 任务状态跟踪
- 任务历史记录
- 异步任务处理

#### 4.2.4 统计服务模块 (modules/stats_service.py)
**负责接口**: `/api/v1/stats`
**核心功能**:
- 数据统计计算
- 系统运行状态监控
- 性能指标收集

### 4.3 爬虫策略设计

#### 4.3.1 请求策略
- **User-Agent**: 模拟移动端APP请求
- **请求间隔**: 1秒（可配置）
- **超时时间**: 30秒
- **重试机制**: 失败重试3次，指数退避

#### 4.3.2 调度策略
| 页面类型 | 更新频率 | 说明 |
|------|---------|------|
| 夹子榜单 | 1小时 | 热度榜单，更新频繁 |
| 其他榜单 | 24小时 | 日更新即可 |

#### 4.3.3 异常处理
- 网络异常：记录日志，等待重试
- 解析异常：保存原始数据，标记异常
- 频率限制：延长请求间隔，暂停任务

## 5. 部署方案

### 5.1 开发环境（macOS）
```bash
# 环境要求
- Python 3.10+
- SQLite3
- Git

# 部署步骤
1. 克隆代码库
2. 创建虚拟环境
3. 安装依赖
4. 初始化数据库
5. 启动服务
```

### 5.2 生产环境（Linux + Docker）

#### 5.2.1 Docker镜像构建
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

#### 5.2.2 部署架构
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Nginx     │────▶│   Docker    │────▶│   sqlite     │
│  (可选)     │     │  Container  │     │  (可选)     │
└─────────────┘     └─────────────┘     └─────────────┘
```

### 5.3 监控方案
- **日志监控**: 使用日志文件记录关键操作
- **健康检查**: 定期调用/health接口
- **数据监控**: 统计爬取成功率、数据量
- **告警机制**: 失败率超过阈值时告警

## 6. 测试方案

### 6.1 测试策略

| 测试类型 | 测试内容 | 测试方法 |
|---------|---------|----------|
| 单元测试 | 数据解析、工具函数 | pytest |
| 接口测试 | API接口功能 | Postman/pytest |
| 集成测试 | 爬虫流程、数据存储 | 手动测试 |
| 压力测试 | 并发请求处理 | locust |

### 6.2 测试用例示例

#### 6.2.1 爬虫功能测试
- 测试正常爬取流程
- 测试网络异常处理
- 测试数据解析异常
- 测试重复数据处理

#### 6.2.2 API接口测试
- 测试参数校验
- 测试分页功能
- 测试错误响应
- 测试并发请求

## 7. 风险评估

| 风险类型 | 风险描述 | 应对措施 |
|---------|---------|----------|
| 技术风险 | API接口变更 | 灵活的解析器设计，快速适配 |
| 技术风险 | 反爬虫机制 | 控制频率，模拟正常请求 |
| 性能风险 | 数据量增长 | 数据库优化，定期清理 |
| 运维风险 | 服务器资源限制 | 监控资源使用，优化代码 |
| 法律风险 | 数据使用合规 | 仅用于研究分析，遵守协议 |

## 8. 项目计划

### 8.1 优化后的开发阶段（2周）

**基于接口驱动开发（API-First）的优化方案：**

**第一阶段：基础搭建（Day 1-2）**
- Day 1: 项目结构搭建和环境配置
  - Poetry依赖管理配置
  - 基础FastAPI应用框架
  - 开发环境配置（IDE、Git等）
- Day 2: 项目基础架构
  - 目录结构设计
  - 配置管理模块
  - 日志系统配置

**第二阶段：API设计优先（Day 3-4）**
- Day 3: API接口定义和文档
  - 基于需求设计所有API端点
  - Pydantic模型定义（请求/响应）
  - FastAPI自动文档生成
- Day 4: Mock接口实现
  - 实现返回假数据的API接口
  - 支持前端并行开发
  - API设计验证和调整

**第三阶段：数据层实现（Day 5-6）**
- Day 5: 数据库设计
  - 基于API需求设计SQLModel模型
  - 数据库表结构创建
  - 数据迁移脚本
- Day 6: 基础数据操作
  - CRUD操作实现
  - 数据库连接和配置
  - 基础查询方法

**第四阶段：功能模块开发（Day 7-11）**
- Day 7-8: 爬虫模块实现
  - HTTP客户端封装
  - 数据解析逻辑
  - 爬虫核心功能
- Day 9-10: 数据服务模块
  - API接口真实实现（替换Mock）
  - 复杂查询逻辑
  - 数据分页和过滤
- Day 11: 任务管理模块
  - 任务调度实现
  - 状态管理
  - 错误处理

**第五阶段：集成测试（Day 12-14）**
- Day 12: 系统集成测试
  - 端到端流程测试
  - 数据一致性验证
- Day 13: 性能优化
  - 数据库查询优化
  - 接口性能调优
- Day 14: 文档和部署
  - 部署文档编写
  - 系统部署验证

### 8.2 详细子任务划分

#### 阶段一：基础搭建（Day 1-2）
**T1.1 项目结构初始化**
- 创建Poetry项目结构和依赖配置
- 设置开发工具（black、isort、pytest）
- 建立Git仓库和基础文档

**T1.2 FastAPI应用框架**
- 创建main.py应用入口
- 配置CORS和中间件，设置基础路由
- 实现健康检查端点

**T1.3 配置管理系统**
- 创建config.py（环境变量、数据库、爬虫参数）
- 配置日志系统

#### 阶段二：API设计优先（Day 3-4）
**T2.1 数据模型定义**
- 创建Pydantic请求/响应模型
- 定义API数据传输对象和验证规则

**T2.2 页面接口Mock实现**
- `/api/v1/pages` 返回页面榜单配置
- 基于urls.json生成结构化数据

**T2.3 榜单接口Mock实现**
- `/api/v1/rankings/{ranking_id}/books` 榜单书籍列表
- `/api/v1/rankings/{ranking_id}/history` 榜单历史对比

**T2.4 书籍接口Mock实现**
- `/api/v1/books/{book_id}` 书籍详情查询
- `/api/v1/books/{book_id}/rankings` 书籍榜单历史
- `/api/v1/books/{book_id}/trends` 书籍趋势分析

**T2.5 爬虫管理接口Mock**
- `/api/v1/crawl/*` 爬取任务触发
- `/api/v1/tasks` 任务状态查询

#### 阶段三：数据层实现（Day 5-6）
**T3.1 SQLModel模型实现**
- 实现Ranking、Book、BookSnapshot、RankingSnapshot、CrawlTask
- 配置表关系、索引和数据库初始化

**T3.2 数据库操作层**
- 基础CRUD操作和连接池配置
- 事务管理和数据迁移脚本

**T3.3 数据访问方法**
- 在data_service.py中实现数据查询方法
- 直接使用SQLModel的查询功能，简化架构

#### 阶段四：功能模块开发（Day 7-11）
**T4.1 爬虫模块（modules/crawler.py）**
- HTTP客户端封装（httpx、重试、限频）
- 夹子榜单爬取器
- 榜单页面爬取器
- 书籍详情爬取器
- 数据解析器和清洗逻辑

**T4.2 数据服务模块（modules/data_service.py）**
- 页面服务（配置生成、层级关系）
- 榜单服务（查询、历史对比、排名变化）
- 书籍服务（详情查询、榜单历史、趋势分析）
- 分页过滤服务（通用分页、多维过滤、排序）

**T4.3 任务管理模块（modules/task_service.py）**
- JSON文件读写操作（tasks.json的增删改查）
- 任务状态管理（pending、running、completed、failed）
- 任务调度器（APScheduler集成、定时配置）
- 任务监控和错误处理

**T4.4 API实现层**
- 将所有Mock接口替换为真实实现
- 集成数据服务和爬虫模块
- 完善错误处理和响应格式

#### 阶段五：集成测试（Day 12-14）
**T5.1 单元测试**
- 爬虫模块测试（解析逻辑、异常处理）
- 数据服务测试（查询逻辑、分页功能）
- API接口测试（参数验证、响应格式）

**T5.2 集成测试**
- 端到端爬取流程测试
- 数据一致性验证
- 接口性能测试

**T5.3 系统优化**
- 数据库查询优化
- 接口响应性能调优
- 部署文档和系统验证

### 8.3 子任务设计原则

**功能清晰性：**
- 每个子任务有明确的输入输出
- 任务之间通过接口约定进行协作
- 避免跨模块的紧耦合

**无重复性：**
- 数据层、业务层、接口层职责明确分离
- Mock实现和真实实现分阶段替换
- 测试任务按模块和集成分层

**可并行性：**
- API Mock实现后，前端可并行开发
- 各功能模块可独立开发测试
- 数据访问层为各模块提供统一接口

### 8.2 里程碑
1. **M1**: 完成基础爬虫功能（第3天）
2. **M2**: 完成API接口（第9天）
3. **M3**: 完成调度系统（第11天）
4. **M4**: 项目上线（第14天）

## 9. 后续优化建议

### 9.1 短期优化（1个月内）
- 实现增量更新机制
- 添加数据去重逻辑
- 优化数据库查询性能
- 完善错误处理机制

### 9.2 中期优化（3个月内）
- 引入Redis缓存
- 实现分布式爬虫
- 添加数据分析功能
- 开发前端界面

### 9.3 长期规划
- 支持更多数据源
- 机器学习预测分析
- 实时数据推送
- 用户个性化服务

## 10. 附录

### 10.1 参考资料
- FastAPI官方文档: https://fastapi.tiangolo.com
- SQLAlchemy文档: https://www.sqlalchemy.org
- APScheduler文档: https://apscheduler.readthedocs.io

### 10.2 相关规范
- RESTful API设计规范
- Python PEP8编码规范
- Git提交信息规范

### 10.3 联系方式
- 项目负责人：[Lien Gu]
- 技术支持：[guliyu0216@163.com]
- 项目仓库：[https://github.com/lien-Gu/JJClawer3.git]