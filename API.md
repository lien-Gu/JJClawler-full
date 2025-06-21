# 晋江文学城爬虫后端 API 文档

## 概述

本文档详细介绍晋江文学城爬虫后端系统的所有API接口，包括功能说明、输入输出格式和使用示例。

**API基础信息**
- **基础URL**: `http://localhost:8000/api/v1`
- **数据格式**: JSON
- **认证方式**: 无（开发阶段）
- **API版本**: v1

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

**接口地址**: `POST /api/v1/crawl/ranking/{channel}`

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

**接口地址**: `GET /api/v1/tasks`

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

**接口地址**: `GET /api/v1/tasks/{task_id}`

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
curl -X GET "http://localhost:8000/api/v1/tasks"

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

## 9. 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.0 | 2024-01-01 | 初始版本，包含基础功能 |
| v1.1.0 | 待定 | 计划添加用户认证和权限管理 |

---

**文档更新时间**: 2024-01-01  
**API版本**: v1.0.0  
**联系方式**: guliyu0216@163.com