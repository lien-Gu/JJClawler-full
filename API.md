# JJ Crawler API Documentation

## 概述

本文档详细介绍晋江文学城爬虫后端系统的所有API接口，已完成T4.4 API实现层的开发，所有接口均已连接到真实的Service层实现。

**API基础信息**
- **基础URL**: `http://localhost:8000/api/v1`
- **数据格式**: JSON
- **认证方式**: 无（开发阶段）
- **API版本**: v1
- **实现状态**: ✅ T4.4完成 - 所有Mock API已替换为真实实现

## 目录

1. [页面配置接口](#1-页面配置接口)
2. [榜单数据接口](#2-榜单数据接口) 
3. [书籍信息接口](#3-书籍信息接口)
4. [爬虫管理接口](#4-爬虫管理接口)
5. [系统状态接口](#5-系统状态接口)
6. [错误处理](#6-错误处理)

---

## 1. 页面配置接口

### 1.1 获取页面配置

**接口地址**: `GET /api/v1/pages`

**功能描述**: 获取所有页面配置信息，用于前端导航和页面布局生成

**请求参数**: 无

**响应格式**:
```json
{
  "pages": [
    {
      "name": "榜单页面",
      "path": "/rankings",
      "sub_pages": [
        {
          "name": "甲子榜",
          "path": "/rankings/jiazi",
          "rankings": [
            {
              "ranking_id": "jiazi",
              "name": "甲子",
              "update_frequency": "hourly"
            }
          ]
        }
      ]
    }
  ],
  "total_pages": 3,
  "total_rankings": 8
}
```

**使用示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/pages"
```

### 1.2 获取页面统计信息

**接口地址**: `GET /api/v1/pages/statistics`

**功能描述**: 获取页面配置统计信息

**响应格式**:
```json
{
  "total_pages": 15,
  "root_pages": 3,
  "sub_pages": 12,
  "total_rankings": 8,
  "config_path": "data/urls.json",
  "cache_valid": true,
  "last_updated": "2024-01-01T12:00:00"
}
```

### 1.3 刷新页面配置缓存

**接口地址**: `POST /api/v1/pages/refresh`

**功能描述**: 强制刷新页面配置缓存

**响应格式**:
```json
{
  "message": "页面配置缓存已刷新",
  "timestamp": "2024-01-01T12:00:00"
}
```

---

## 2. 榜单数据接口

### 2.1 获取榜单书籍列表

**接口地址**: `GET /api/v1/rankings/{ranking_id}/books`

**功能描述**: 获取指定榜单的书籍排名信息，支持历史查询和排名变化对比

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| ranking_id | string | 是 | 榜单ID，如 "jiazi", "yq", "ca" |

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|-------|------|
| date | string | 否 | 最新 | 指定日期，格式：YYYY-MM-DD |
| limit | integer | 否 | 50 | 每页数量，范围：1-100 |
| offset | integer | 否 | 0 | 偏移量，用于分页 |

**响应格式**:
```json
{
  "ranking": {
    "id": "jiazi",
    "name": "甲子榜",
    "description": "全站热度榜单"
  },
  "snapshot_time": "2024-01-01T12:00:00Z",
  "books": [
    {
      "book_id": "123456",
      "title": "书籍标题",
      "author": "作者名称",
      "position": 1,
      "total_clicks": 1000000,
      "total_favorites": 50000,
      "comment_count": 1500,
      "chapter_count": 120,
      "position_change": "+2",
      "novel_class": "言情",
      "tags": "现代,都市"
    }
  ],
  "pagination": {
    "total": 50,
    "limit": 50,
    "offset": 0,
    "has_next": false
  }
}
```

**使用示例**:
```bash
# 获取甲子榜最新数据
curl -X GET "http://localhost:8000/api/v1/rankings/jiazi/books"

# 获取指定日期的榜单数据
curl -X GET "http://localhost:8000/api/v1/rankings/jiazi/books?date=2024-01-01"

# 分页获取数据
curl -X GET "http://localhost:8000/api/v1/rankings/jiazi/books?limit=20&offset=20"
```

### 2.2 获取榜单历史数据

**接口地址**: `GET /api/v1/rankings/{ranking_id}/history`

**功能描述**: 获取榜单的历史快照数据，用于趋势分析

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| ranking_id | string | 是 | 榜单ID |

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|-------|------|
| days | integer | 否 | 7 | 查询天数，范围：1-30 |

**响应格式**:
```json
{
  "ranking_id": "jiazi",
  "snapshots": [
    {
      "snapshot_time": "2024-01-01T12:00:00Z",
      "total_books": 50,
      "avg_clicks": 50000,
      "avg_favorites": 2500
    }
  ],
  "period": {
    "start_date": "2023-12-25",
    "end_date": "2024-01-01",
    "days": 7
  }
}
```

---

## 3. 书籍信息接口

### 3.1 获取书籍详细信息

**接口地址**: `GET /api/v1/books/{book_id}`

**功能描述**: 获取指定书籍的完整信息，包括基本信息和最新统计数据

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| book_id | string | 是 | 书籍ID |

**响应格式**:
```json
{
  "book_id": "123456",
  "title": "书籍标题",
  "author_id": "789",
  "author_name": "作者名称",
  "novel_class": "言情",
  "tags": "现代,都市",
  "first_seen": "2024-01-01T12:00:00Z",
  "last_updated": "2024-01-01T12:00:00Z",
  "latest_stats": {
    "total_clicks": 1000000,
    "total_favorites": 50000,
    "comment_count": 1500,
    "chapter_count": 120,
    "snapshot_time": "2024-01-01T12:00:00Z"
  }
}
```

### 3.2 获取书籍榜单历史

**接口地址**: `GET /api/v1/books/{book_id}/rankings`

**功能描述**: 获取书籍在各榜单中的出现历史和排名表现

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| book_id | string | 是 | 书籍ID |

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|-------|------|
| days | integer | 否 | 30 | 查询天数 |

**响应格式**:
```json
{
  "book": {
    "book_id": "123456",
    "title": "书籍标题",
    "author_name": "作者名称"
  },
  "current_rankings": [
    {
      "ranking_id": "jiazi",
      "ranking_name": "甲子榜",
      "position": 5,
      "snapshot_time": "2024-01-01T12:00:00Z"
    }
  ],
  "history": [
    {
      "ranking_id": "jiazi",
      "position": 3,
      "snapshot_time": "2023-12-31T12:00:00Z"
    }
  ]
}
```

### 3.3 获取书籍趋势数据

**接口地址**: `GET /api/v1/books/{book_id}/trends`

**功能描述**: 获取书籍点击量、收藏量等统计数据的变化趋势

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| book_id | string | 是 | 书籍ID |

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|-------|------|
| days | integer | 否 | 30 | 查询天数 |
| metrics | string | 否 | all | 指标类型：clicks,favorites,comments,chapters,all |

**响应格式**:
```json
{
  "book_id": "123456",
  "trends": [
    {
      "date": "2024-01-01",
      "total_clicks": 1000000,
      "total_favorites": 50000,
      "comment_count": 1500,
      "chapter_count": 120
    }
  ],
  "period": {
    "start_date": "2023-12-02",
    "end_date": "2024-01-01",
    "days": 30
  },
  "summary": {
    "clicks_growth": "+5.2%",
    "favorites_growth": "+3.8%",
    "peak_date": "2023-12-25"
  }
}
```

### 3.4 搜索书籍

**接口地址**: `GET /api/v1/books`

**功能描述**: 根据条件搜索书籍

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|-------|------|
| keyword | string | 否 | - | 搜索关键词（书名、作者） |
| novel_class | string | 否 | - | 小说分类 |
| author | string | 否 | - | 作者名称 |
| limit | integer | 否 | 20 | 每页数量 |
| offset | integer | 否 | 0 | 偏移量 |

**响应格式**:
```json
{
  "books": [
    {
      "book_id": "123456",
      "title": "书籍标题",
      "author_name": "作者名称",
      "novel_class": "言情",
      "tags": "现代,都市",
      "latest_stats": {
        "total_clicks": 1000000,
        "total_favorites": 50000
      }
    }
  ],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_next": true
  }
}
```

---

## 4. 爬虫管理接口

### 4.1 触发甲子榜爬取

**接口地址**: `POST /api/v1/crawl/jiazi`

**功能描述**: 手动触发甲子榜数据爬取任务

**请求体**:
```json
{
  "immediate": true,
  "metadata": {
    "trigger_source": "manual",
    "description": "手动触发的甲子榜爬取"
  }
}
```

**响应格式**:
```json
{
  "task_id": "jiazi_20240101_120000_abc123",
  "message": "甲子榜爬取任务已创建",
  "estimated_duration": "2-3分钟",
  "status": "pending"
}
```

### 4.2 触发分类页面爬取

**接口地址**: `POST /api/v1/crawl/page/{channel}`

**功能描述**: 触发指定分类页面的爬取任务

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| channel | string | 是 | 频道标识，如 "yq", "ca" |

**请求体**:
```json
{
  "immediate": true,
  "metadata": {
    "trigger_source": "manual"
  }
}
```

**响应格式**:
```json
{
  "task_id": "page_yq_20240101_120000_def456",
  "message": "分类页面爬取任务已创建",
  "channel": "yq",
  "estimated_duration": "1-2分钟"
}
```

### 4.3 获取任务状态

**接口地址**: `GET /api/v1/crawl/tasks`

**功能描述**: 获取所有爬取任务的状态信息

**查询参数**:
| 参数 | 类型 | 必填 | 默认值 | 描述 |
|------|------|------|-------|------|
| status | string | 否 | all | 任务状态：pending,running,completed,failed,all |
| limit | integer | 否 | 20 | 返回数量限制 |

**响应格式**:
```json
{
  "current_tasks": [
    {
      "task_id": "jiazi_20240101_120000_abc123",
      "task_type": "jiazi",
      "status": "running",
      "progress": 75,
      "items_crawled": 38,
      "total_items": 50,
      "created_at": "2024-01-01T12:00:00Z",
      "started_at": "2024-01-01T12:00:30Z"
    }
  ],
  "recent_completed": [
    {
      "task_id": "jiazi_20240101_110000_xyz789",
      "task_type": "jiazi",
      "status": "completed",
      "items_crawled": 50,
      "completed_at": "2024-01-01T11:05:00Z",
      "duration": "4分32秒"
    }
  ],
  "statistics": {
    "total_running": 1,
    "total_completed_today": 5,
    "total_failed_today": 0,
    "success_rate": "100%"
  }
}
```

### 4.4 获取单个任务详情

**接口地址**: `GET /api/v1/crawl/tasks/{task_id}`

**功能描述**: 获取指定任务的详细信息

**路径参数**:
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| task_id | string | 是 | 任务ID |

**响应格式**:
```json
{
  "task_id": "jiazi_20240101_120000_abc123",
  "task_type": "jiazi",
  "status": "completed",
  "progress": 100,
  "items_crawled": 50,
  "created_at": "2024-01-01T12:00:00Z",
  "started_at": "2024-01-01T12:00:30Z",
  "completed_at": "2024-01-01T12:05:02Z",
  "duration": "4分32秒",
  "metadata": {
    "trigger_source": "scheduled",
    "books_new": 3,
    "books_updated": 47,
    "snapshots_created": 50
  },
  "error_message": null
}
```

---

## 5. 系统状态接口

### 5.1 健康检查

**接口地址**: `GET /health`

**功能描述**: 系统健康状态检查

**响应格式**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "uptime": "2天3小时15分钟",
  "database": "connected",
  "cache": "active"
}
```

### 5.2 系统统计

**接口地址**: `GET /api/v1/stats`

**功能描述**: 获取系统运行统计信息

**响应格式**:
```json
{
  "books": {
    "total_count": 12450,
    "new_today": 25,
    "updated_today": 380
  },
  "rankings": {
    "total_count": 8,
    "active_count": 8,
    "last_update": "2024-01-01T12:00:00Z"
  },
  "snapshots": {
    "total_count": 450000,
    "created_today": 400,
    "storage_size": "120MB"
  },
  "tasks": {
    "completed_today": 24,
    "failed_today": 0,
    "success_rate": "100%",
    "avg_duration": "3分45秒"
  },
  "system": {
    "cpu_usage": "12%",
    "memory_usage": "340MB",
    "disk_usage": "2.5GB"
  }
}
```

---

## 6. 错误处理

### 6.1 标准错误格式

所有API错误都遵循统一的格式：

```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "指定的书籍不存在",
    "details": "书籍ID '123456' 在数据库中未找到",
    "timestamp": "2024-01-01T12:00:00Z",
    "request_id": "req_abc123def456"
  }
}
```

### 6.2 常见错误码

| 状态码 | 错误码 | 描述 |
|--------|--------|------|
| 400 | INVALID_PARAMETER | 请求参数无效 |
| 404 | RESOURCE_NOT_FOUND | 资源不存在 |
| 409 | TASK_ALREADY_RUNNING | 任务已在运行中 |
| 429 | RATE_LIMIT_EXCEEDED | 请求频率超限 |
| 500 | INTERNAL_SERVER_ERROR | 服务器内部错误 |
| 503 | SERVICE_UNAVAILABLE | 服务暂不可用 |

### 6.3 错误处理示例

```bash
# 请求不存在的书籍
curl -X GET "http://localhost:8000/api/v1/books/nonexistent"

# 响应
HTTP/1.1 404 Not Found
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "书籍 'nonexistent' 不存在",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

---

## 7. 使用示例

### 7.1 完整爬取流程

```bash
# 1. 获取页面配置
curl -X GET "http://localhost:8000/api/v1/pages"

# 2. 触发甲子榜爬取
curl -X POST "http://localhost:8000/api/v1/crawl/jiazi" \
  -H "Content-Type: application/json" \
  -d '{"immediate": true}'

# 3. 查看任务状态
curl -X GET "http://localhost:8000/api/v1/crawl/tasks"

# 4. 获取榜单数据
curl -X GET "http://localhost:8000/api/v1/rankings/jiazi/books"

# 5. 查看书籍详情
curl -X GET "http://localhost:8000/api/v1/books/123456"
```

### 7.2 数据分析流程

```bash
# 1. 获取书籍趋势数据
curl -X GET "http://localhost:8000/api/v1/books/123456/trends?days=30"

# 2. 获取书籍榜单历史
curl -X GET "http://localhost:8000/api/v1/books/123456/rankings"

# 3. 获取榜单历史对比
curl -X GET "http://localhost:8000/api/v1/rankings/jiazi/history?days=7"

# 4. 系统统计信息
curl -X GET "http://localhost:8000/api/v1/stats"
```

---

## 8. 技术说明

### 8.1 分页机制

所有列表类接口都支持基于 offset/limit 的分页：
- `limit`: 每页数量，最大100
- `offset`: 偏移量，从0开始
- 响应中包含 `pagination` 对象提供分页信息

### 8.2 日期格式

- 所有日期参数使用 ISO 8601 格式：`YYYY-MM-DD`
- 时间戳使用 ISO 8601 格式：`YYYY-MM-DDTHH:MM:SSZ`

### 8.3 数据更新频率

- 甲子榜：每小时更新
- 其他榜单：每日更新
- 书籍统计：随榜单更新
- 系统统计：实时计算

### 8.4 性能优化

- 页面配置缓存：30分钟TTL
- 数据库连接池：最大10个连接
- HTTP请求限流：1秒间隔
- 响应压缩：支持gzip

---

## 9. T4.4 API实现层完成状态

### 9.1 实现概览

✅ **T4.4.1 页面配置API** - 已完成真实实现
- 连接PageService，支持动态配置获取
- 实现配置缓存机制（30分钟TTL）
- 支持配置刷新和统计信息

✅ **T4.4.2 榜单数据API** - 已完成真实实现
- 连接RankingService，支持实时榜单查询
- 实现历史数据查询和排名变化对比
- 支持分页和日期筛选

✅ **T4.4.3 书籍信息API** - 已完成真实实现
- 连接BookService，支持书籍详情查询
- 实现趋势分析和榜单历史功能
- 支持多条件搜索和分页

✅ **T4.4.4 爬虫管理API** - 已完成真实实现
- 连接CrawlerService和SchedulerService
- 支持手动触发和调度器集成
- 实现任务状态监控和管理

### 9.2 架构特点

- **服务层集成**: 所有API都正确连接到对应的Service层
- **错误处理**: 统一的异常处理和错误响应格式
- **数据验证**: 使用Pydantic模型进行请求响应验证
- **依赖注入**: 使用FastAPI的依赖注入管理服务实例
- **资源管理**: 正确的数据库连接关闭和资源清理

### 9.3 核心功能

1. **实时数据**: 所有API都返回数据库中的真实数据
2. **事务安全**: Service层保证数据操作的事务性
3. **性能优化**: 实现分页、缓存等性能优化措施
4. **任务调度**: 集成APScheduler支持定时和手动任务触发

---

## 10. 数据模型

### 10.1 数据库架构

本系统采用SQLModel ORM，基于SQLite数据库，支持类型安全的数据模型定义。数据库架构分为核心业务表和文件存储两部分：

**数据库表（4个核心表）：**
- `rankings`：榜单配置元数据
- `books`：书籍静态信息
- `book_snapshots`：书籍动态统计快照
- `ranking_snapshots`：榜单排名快照

**文件存储：**
- `data/tasks/tasks.json`：任务管理状态
- `data/urls.json`：爬取配置信息

### 10.2 核心数据模型

#### 10.2.1 榜单配置模型

```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class UpdateFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"

# 榜单配置表
class Ranking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ranking_id: str = Field(unique=True, index=True)
    name: str  # 中文名
    channel: str  # API频道参数
    frequency: UpdateFrequency
    update_interval: int
    parent_id: Optional[str] = Field(default=None)  # 父级榜单
```

#### 10.2.2 书籍数据模型

**书籍基础信息表（静态数据）：**
```python
# 书籍表（仅静态信息）
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
```

**书籍统计快照表（动态数据）：**
```python
from sqlmodel import Index

# 书籍快照表（存储书籍级别的动态信息）
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
```

#### 10.2.3 榜单快照模型

```python
# 榜单快照表（存储榜单维度的数据）
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
```

### 10.3 API请求响应模型

#### 10.3.1 分页模型

```python
class PaginationInfo(BaseModel):
    total: int
    limit: int
    offset: int
    has_next: bool
```

#### 10.3.2 书籍相关模型

```python
class BookDetail(BaseModel):
    book_id: str
    title: str
    author_id: str
    author_name: str
    novel_class: Optional[str] = None
    tags: Optional[str] = None
    first_seen: datetime
    last_updated: datetime
    latest_stats: Optional[Dict[str, Any]] = None

class BookTrendData(BaseModel):
    date: str
    total_clicks: Optional[int] = None
    total_favorites: Optional[int] = None
    comment_count: Optional[int] = None
    chapter_count: Optional[int] = None
```

#### 10.3.3 榜单相关模型

```python
class RankingInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None

class RankingBookItem(BaseModel):
    book_id: str
    title: str
    author: str
    position: int
    total_clicks: Optional[int] = None
    total_favorites: Optional[int] = None
    comment_count: Optional[int] = None
    chapter_count: Optional[int] = None
    position_change: Optional[str] = None
    novel_class: Optional[str] = None
    tags: Optional[str] = None
```

### 10.4 数据库优化配置

#### 10.4.1 SQLite性能优化

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

#### 10.4.2 索引设计

**核心查询场景优化：**

```sql
-- 1. 书籍趋势分析查询
SELECT snapshot_time, total_clicks, total_favorites, comment_count, chapter_count
FROM BookSnapshot 
WHERE book_id = ? AND snapshot_time >= ?
ORDER BY snapshot_time;

-- 2. 书籍榜单历史查询
SELECT r.name, rs.position, rs.snapshot_time
FROM RankingSnapshot rs JOIN Ranking r ON rs.ranking_id = r.ranking_id
WHERE rs.book_id = ?
ORDER BY rs.snapshot_time DESC;

-- 3. 榜单当前快照查询
SELECT book_id, position, snapshot_time
FROM RankingSnapshot 
WHERE ranking_id = ? AND snapshot_time = (
    SELECT MAX(snapshot_time) FROM RankingSnapshot WHERE ranking_id = ?
)
ORDER BY position;
```

### 10.5 数据设计优势

#### 10.5.1 分离静态与动态数据

**设计理念：**
- **静态信息**：书籍标题、作者等基本不变的信息存储在Books表
- **动态信息**：点击量、收藏量等随时间变化的统计信息存储在BookSnapshot表
- **时序数据**：支持完整的趋势分析和历史数据查询

**查询优化：**
- 基本信息查询：仅访问Books表，速度快
- 趋势分析：BookSnapshot表有针对性索引
- 榜单查询：RankingSnapshot表支持复杂排名查询

#### 10.5.2 混合存储策略

**数据库存储（适合复杂查询）：**
- Book相关的结构化数据
- 需要关联查询的榜单数据
- 时间序列的快照数据

**JSON文件存储（适合简单状态管理）：**
- 任务状态管理（data/tasks/tasks.json）
- 爬取配置信息（data/urls.json）
- 临时状态和日志信息

---

## 11. 系统架构

### 11.1 五层模块化架构

本系统采用接口驱动的五层架构设计，实现了清晰的职责分离和高度的模块化：

```
┌─────────────────────────────────────────────────────┐
│                  API接口层                           │
│         (FastAPI路由, 请求响应处理)                    │
└─────────────────────────────────────────────────────┘
                            │
                    根据接口确定业务功能
                            ▼
┌─────────────────────────────────────────────────────┐
│                 Service业务层                        │
│   BookService  RankingService  CrawlerService      │
└─────────────────────────────────────────────────────┘
                            │
                    数据访问和持久化
                            ▼
┌─────────────────────────────────────────────────────┐
│                DAO数据访问层                          │
│     BookDAO    RankingDAO    Database连接管理       │
└─────────────────────────────────────────────────────┘
                            │
                    专业功能模块支持
                            ▼
┌─────────────────────────────────────────────────────┐
│               专业功能模块层                          │
│  爬虫模块   调度器模块   任务管理   页面配置模块       │
└─────────────────────────────────────────────────────┘
                            │
                    通用工具和基础设施
                            ▼
┌─────────────────────────────────────────────────────┐
│                工具支持层 (Utils)                     │
│  HTTP工具  文件工具  时间工具  日志工具  数据工具      │
└─────────────────────────────────────────────────────┘
```

### 11.2 架构层级详解

**🌐 API接口层**
- **职责**：HTTP接口、参数验证、响应格式化
- **实现**：FastAPI路由、Pydantic模型验证、依赖注入
- **文件**：`api/` 目录下的路由模块

**⚙️ Service业务层**
- **职责**：业务逻辑组合、事务控制、数据转换
- **实现**：业务规则封装、DAO层组合、异常处理
- **文件**：`modules/service/` 目录下的服务模块

**🔧 DAO数据访问层**
- **职责**：数据访问对象、CRUD操作、复杂查询
- **实现**：SQLModel ORM、数据库事务、资源管理
- **文件**：`modules/dao/` 目录下的数据访问模块

**🏗️ 专业功能模块层**
- **职责**：领域特定功能、专业逻辑实现
- **实现**：爬虫、调度器、任务管理等专业模块
- **文件**：`modules/crawler/`、`modules/service/scheduler_service.py` 等

**🛠️ 工具支持层**
- **职责**：通用工具函数、横切关注点、基础设施
- **实现**：HTTP客户端、文件工具、时间工具、数据处理等
- **文件**：`utils/` 目录下的工具模块

### 11.3 关键技术特性

**依赖注入机制**
```python
# FastAPI依赖注入示例
@app.get("/api/v1/books/{book_id}")
async def get_book_detail(
    book_id: str,
    book_service: BookService = Depends(get_book_service)
):
    return await book_service.get_book_detail(book_id)
```

**自动资源管理**
```python
# Service层自动Session管理
class BookService:
    def __init__(self, session: Session):
        self.session = session
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.session.rollback()
        else:
            self.session.commit()
        self.session.close()
```

**统一异常处理**
```python
# 统一API异常响应格式
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.detail.get("code", "UNKNOWN_ERROR"),
                "message": exc.detail.get("message", str(exc.detail)),
                "timestamp": datetime.now().isoformat()
            }
        }
    )
```

---

## 13. 接口设计原则

### 13.1 API优先设计方法

本项目采用严格的“API优先”开发方法论：

1. **接口定义优先**：基于业务需求定义所有API端点
2. **Mock API支持**：创建返回虚拟数据的Mock API支持前端开发
3. **Pydantic模型验证**：使用类型安全的请求/响应模型
4. **逐步替换实现**：将Mock API替换为真实实现

### 13.2 核心业务接口设计

#### 13.2.1 页面配置接口
```
GET /api/v1/pages
功能: 获取所有榜单页面配置（动态配置服务）
响应: {
  "pages": [
    {"page_id": "yq", "name": "言情", "rankings": [...]},
    {"page_id": "ca", "name": "纯爱", "rankings": [...]}
  ]
}
```

#### 13.2.2 榜单数据接口
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

#### 13.2.3 书籍信息接口
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

#### 13.2.4 爬虫管理接口
```
POST /api/v1/crawl/jiazi
功能: 触发夹子榜单爬取
响应: {"task_id": "xxx", "message": "Task started"}

POST /api/v1/crawl/page/{channel}
功能: 触发特定榜单爬取
响应: {"task_id": "xxx", "message": "Task started"}

GET /api/v1/crawl/tasks
功能: 获取爬取任务状态
响应: {"tasks": [{"task_id": "xxx", "status": "running", "progress": "50%"}]}
```

### 13.3 接口设计特性

**RESTful设计原则**
- 使用标准HTTP方法（GET, POST, PUT, DELETE）
- 资源层级化URL路径设计
- 统一的响应格式和错误处理

**分页机制**
- 基于offset/limit的分页方式
- 所有列表接口支持分页参数
- 响应中包含pagination对象

**数据过滤**
- 支持日期范围过滤（date参数）
- 支持分类和关键词过滤
- 支持排序参数（sort, order）

---

## 14. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2024-01-01 | 初始版本，包含基础功能 |
| v1.1.0 | 2024-01-01 | T4.4完成 - API实现层完整实现 |
| v1.2.0 | 2024-06-21 | 数据模型迁移 - 完整数据库设计和架构文档 |
| v1.3.0 | 待定 | 计划添加用户认证和权限管理 |

---

**文档更新时间**: 2024-01-01  
**API版本**: v1.0.0  
**联系方式**: guliyu0216@163.com