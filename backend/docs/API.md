# API文档

## 调度任务管理 API

### 创建爬取任务

**POST** `/api/v1/schedule/task/create`

创建爬取任务,爬取列表中的所有页面。每个页面ID对应一个独立的调度任务。

#### 请求参数

| 参数名 | 类型 | 必填 | 默认值 | 描述 |
|--------|------|------|--------|------|
| page_ids | List[str] | 否 | ["jiazi"] | 爬取的页面id列表 |
| run_time | datetime | 否 | 当前时间 | 任务运行时间 |

#### 响应格式

```json
{
  "success": true,
  "message": "成功创建 2 个爬取任务",
  "data": [
    {
      "job_id": "CrawlJobHandler_jiazi_20250730_143022",
      "trigger_type": "date",
      "trigger_time": {"run_time": "2025-07-30T14:30:22"},
      "handler": "CrawlJobHandler",
      "status": ["pending", "任务已添加到调度器"],
      "page_ids": ["jiazi"],
      "desc": "手动创建的爬取任务 - 页面: jiazi"
    },
    {
      "job_id": "CrawlJobHandler_category_20250730_143023",
      "trigger_type": "date", 
      "trigger_time": {"run_time": "2025-07-30T14:30:22"},
      "handler": "CrawlJobHandler",
      "status": ["pending", "任务已添加到调度器"],
      "page_ids": ["category"],
      "desc": "手动创建的爬取任务 - 页面: category"
    }
  ]
}
```

### 获取任务状态

**GET** `/api/v1/schedule/task/{job_id}`

获取指定调度任务的详细信息。

#### 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| job_id | str | 是 | 调度任务的ID |

#### 响应格式

```json
{
  "success": true,
  "message": "获取任务状态成功",
  "data": {
    "job_id": "CrawlJobHandler_jiazi_20250730_143022",
    "trigger_type": "date",
    "trigger_time": {"run_time": "2025-07-30T14:30:22"},
    "handler": "CrawlJobHandler",
    "status": ["success", "任务执行完成"],
    "page_ids": ["jiazi"],
    "desc": "手动创建的爬取任务 - 页面: jiazi"
  }
}
```

### 获取调度器状态

**GET** `/api/v1/schedule/status`

获取调度器状态和任务信息。

#### 响应格式

```json
{
  "success": true,
  "message": "获取调度器状态成功",
  "data": {
    "status": "running",
    "job_wait": [
      {
        "id": "CrawlJobHandler_jiazi_20250730_143022",
        "next_run_time": "2025-07-30 14:30:22",
        "trigger": "date[2025-07-30 14:30:22]",
        "status": "pending"
      }
    ],
    "job_running": [],
    "run_time": "0天2小时15分钟30秒"
  }
}
```

## 架构说明

### 多页面任务处理

当`create_crawl_job`接收到多个页面ID时：

1. **独立任务创建**: 为每个页面ID创建一个独立的调度任务
2. **任务ID生成**: 每个任务获得唯一的job_id，格式为`{handler}_{page_id}_{timestamp}`
3. **并行执行**: 各个页面的爬取任务可以独立并行执行
4. **状态跟踪**: 每个任务有独立的状态和执行结果

### 调度器架构

- **APScheduler 3.10.4**: 使用稳定版本的APScheduler
- **SQLAlchemyJobStore**: 任务持久化存储在SQLite数据库中
- **Metadata存储**: 业务数据存储在APScheduler的job.metadata中
- **事件驱动**: 使用APScheduler的事件系统处理任务状态变化

### 数据模型

#### JobInfo

```python
class JobInfo(BaseModel):
    job_id: str                           # 任务ID
    trigger_type: TriggerType             # 触发器类型 (date/cron/interval)
    trigger_time: Dict[str, Any]          # 触发器参数
    handler: JobHandlerType               # 处理器类型
    status: Optional[Tuple[JobStatus, str]]  # 任务状态和描述
    page_ids: Optional[List[str]]         # 页面ID列表
    result: Optional[List[JobResultModel]] # 执行结果
    desc: Optional[str]                   # 任务描述
```

#### DataResponse

```python
class DataResponse(BaseModel):
    success: bool = True                  # 请求是否成功
    message: str = "操作成功"             # 响应消息
    data: Optional[T] = None              # 响应数据
```