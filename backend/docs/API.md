# JJCrawler API 文档

本文档描述了JJCrawler晋江文学城爬虫项目的所有API接口。

## 接口概述

- **基础URL**: `http://localhost:8000/api/v1`
- **认证方式**: 无需认证（内网使用）
- **响应格式**: 统一JSON格式
- **API版本**: v1

## 通用响应格式

所有API接口都使用统一的响应格式：

```json
{
  "success": boolean,      // 请求是否成功
  "message": string,       // 响应消息
  "data": object | null    // 响应数据（可选）
}
```

## 1. 调度任务管理 API

### 1.1 创建爬取任务

**POST** `/api/v1/schedule/task/create`

创建新的爬取任务，支持指定页面ID和执行时间。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page_ids | List[str] | 否 | ["jiazi"] | 爬取的页面ID列表 |
| run_time | datetime | 否 | 当前时间 | 任务运行时间（ISO格式） |

#### 请求示例

```bash
# 创建默认任务
curl -X POST "http://localhost:8000/api/v1/schedule/task/create"

# 创建指定页面任务
curl -X POST "http://localhost:8000/api/v1/schedule/task/create?page_ids=jiazi&page_ids=category"

# 创建定时任务
curl -X POST "http://localhost:8000/api/v1/schedule/task/create" \
  -H "Content-Type: application/json" \
  -d '{
    "page_ids": ["jiazi"],
    "run_time": "2025-08-12T15:00:00"
  }'
```

#### 响应格式

```json
{
  "success": true,
  "message": "成功创建爬取任务: CRAWL_20250812_140000",
  "data": {
    "job_id": "CRAWL_20250812_140000",
    "job_type": "crawl",
    "desc": "手动创建的爬取任务",
    "err": null
  }
}
```

#### 状态码
- **200**: 成功
- **422**: 参数验证失败

### 1.2 获取调度器状态

**GET** `/api/v1/schedule/status`

获取调度器当前状态和任务队列信息。

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/schedule/status"
```

#### 响应格式

```json
{
  "success": true,
  "message": "获取调度器状态成功",
  "data": {
    "status": "running",
    "jobs": [
      {
        "id": "CRAWL_20250812_140000",
        "next_run_time": "2025-08-12 14:00:00",
        "trigger": "date[2025-08-12 14:00:00]",
        "status": "scheduled"
      }
    ],
    "run_time": "1天2小时30分钟15秒"
  }
}
```

#### 状态码
- **200**: 成功

## 2. 书籍数据 API

### 2.1 获取书籍列表

**GET** `/api/v1/books/`

获取书籍列表，支持分页和筛选。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| skip | int | 否 | 0 | 跳过记录数 |
| limit | int | 否 | 100 | 每页记录数（最大1000） |

#### 请求示例

```bash
# 获取默认书籍列表
curl -X GET "http://localhost:8000/api/v1/books/"

# 分页获取书籍列表
curl -X GET "http://localhost:8000/api/v1/books/?skip=0&limit=50"
```

#### 响应格式

```json
{
  "success": true,
  "message": "获取书籍列表成功",
  "data": [
    {
      "novel_id": 12345,
      "title": "示例小说标题",
      "author_id": 67890,
      "created_at": "2025-08-12T10:00:00",
      "updated_at": "2025-08-12T10:00:00"
    }
  ]
}
```

### 2.2 获取书籍详情

**GET** `/api/v1/books/{novel_id}`

获取指定书籍的详细信息和最新统计数据。

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| novel_id | int | 是 | 书籍ID |

#### 请求示例

```bash
curl -X GET "http://localhost:8000/api/v1/books/12345"
```

#### 响应格式

```json
{
  "success": true,
  "message": "获取书籍详情成功",
  "data": {
    "novel_id": 12345,
    "title": "示例小说标题",
    "author_id": 67890,
    "latest_snapshot": {
      "favorites": 1500,
      "clicks": 25000,
      "comments": 200,
      "nutrition": 800,
      "word_counts": 150000,
      "chapter_counts": 45,
      "status": "连载中",
      "snapshot_time": "2025-08-12T10:00:00"
    }
  }
}
```

## 3. 榜单数据 API

### 3.1 获取榜单列表

**GET** `/api/v1/rankings/`

获取榜单配置列表，支持分页和分组筛选。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| skip | int | 否 | 0 | 跳过记录数 |
| limit | int | 否 | 100 | 每页记录数 |
| rank_group_type | str | 否 | null | 榜单分组类型筛选 |

#### 请求示例

```bash
# 获取所有榜单
curl -X GET "http://localhost:8000/api/v1/rankings/"

# 按分组筛选榜单
curl -X GET "http://localhost:8000/api/v1/rankings/?rank_group_type=热门"
```

#### 响应格式

```json
{
  "success": true,
  "message": "获取榜单列表成功",
  "data": [
    {
      "id": 1,
      "rank_id": "jiazi_rank",
      "channel_name": "夹子相关",
      "rank_group_type": "热门",
      "page_id": "jiazi",
      "created_at": "2025-08-12T10:00:00"
    }
  ]
}
```

### 3.2 获取榜单详情

**GET** `/api/v1/rankings/{ranking_id}`

获取指定榜单的详细信息和当前排名。

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| ranking_id | int | 是 | 榜单ID |

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| limit | int | 否 | 50 | 返回排名数量 |

#### 响应格式

```json
{
  "success": true,
  "message": "获取榜单详情成功",
  "data": {
    "ranking": {
      "id": 1,
      "rank_id": "jiazi_rank",
      "channel_name": "夹子相关",
      "rank_group_type": "热门"
    },
    "books": [
      {
        "position": 1,
        "novel_id": 12345,
        "title": "排名第一的小说",
        "author_id": 67890,
        "snapshot_time": "2025-08-12T10:00:00"
      }
    ]
  }
}
```

## 4. 系统接口

### 4.1 健康检查

**GET** `/health`

系统健康状态检查。

#### 请求示例

```bash
curl -X GET "http://localhost:8000/health"
```

#### 响应格式

```json
{
  "status": "ok",
  "timestamp": "2025-08-12T10:00:00Z"
}
```

### 4.2 API文档

**GET** `/docs`

Swagger UI API文档界面（浏览器访问）。

**GET** `/redoc`

ReDoc API文档界面（浏览器访问）。

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "message": "错误描述信息",
  "data": null
}
```

### 常见错误码

| 状态码 | 描述 | 示例 |
|-------|------|------|
| 200 | 成功 | 所有正常响应 |
| 400 | 请求参数错误 | 参数格式不正确 |
| 404 | 资源不存在 | 书籍或榜单ID不存在 |
| 422 | 参数验证失败 | 必需参数缺失 |
| 500 | 服务器内部错误 | 数据库连接失败 |

## 技术说明

### 任务调度架构

- **APScheduler 3.x**: 使用稳定版本的APScheduler
- **事件驱动**: 使用APScheduler事件系统监控任务状态
- **简化设计**: 移除复杂的元数据存储，专注任务执行

### 数据模型

#### JobBasic（任务基础信息）

```python
class JobBasic(BaseModel):
    job_id: str = ""           # 任务ID
    job_type: JobType = JobType.CRAWL  # 任务类型
    desc: str = ""             # 任务描述
    err: Optional[str] = None  # 错误信息
```

#### SchedulerInfo（调度器信息）

```python
class SchedulerInfo(BaseModel):
    status: str                    # 调度器状态
    jobs: List[Dict[str, Any]]     # 任务列表
    run_time: str                  # 运行时间
```

### 爬取配置

系统支持的页面ID（page_ids）：
- **jiazi**: 夹子相关榜单
- **category**: 分类页面
- **其他**: 参考`data/urls.json`配置文件

---

*文档最后更新时间：2025年8月12日*