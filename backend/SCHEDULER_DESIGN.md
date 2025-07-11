# APScheduler 调度器设计文档

## 1. 系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI 应用层                            │
├─────────────────────────────────────────────────────────────┤
│  Crawl API        │  Schedule API    │  其他业务 API        │
│  (动态任务触发)    │  (调度器管理)     │                      │
├─────────────────────────────────────────────────────────────┤
│                    调度器核心层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ TaskScheduler│  │ JobHandlers │  │ JobContext  │         │
│  │   (调度管理)  │  │  (任务执行)  │  │  (上下文)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                  APScheduler 框架层                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │  Scheduler  │  │  JobStore   │  │  Executor   │         │
│  │   (调度器)   │  │  (任务存储)  │  │  (执行器)   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
├─────────────────────────────────────────────────────────────┤
│                     存储层                                  │
│  ┌─────────────┐  ┌─────────────┐                          │
│  │   SQLite    │  │   业务数据   │                          │
│  │  (任务持久化) │  │   (爬虫数据) │                          │
│  └─────────────┘  └─────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## 2. 核心组件详解

### 2.1 TaskScheduler (调度器主类)

**职责**：
- 管理调度器的生命周期（启动/停止）
- 添加/删除/暂停/恢复任务
- 处理任务执行和结果回调
- 提供调度器状态监控

**关键方法**：
```python
class TaskScheduler:
    async def start()                    # 启动调度器
    async def shutdown()                 # 停止调度器
    async def add_job()                  # 添加周期性任务
    async def add_one_time_job()         # 添加一次性任务
    def remove_job()                     # 删除任务
    def pause_job()                      # 暂停任务
    def resume_job()                     # 恢复任务
    def get_status()                     # 获取状态
```

### 2.2 JobHandlers (任务处理器)

**设计原理**：
- 基于策略模式，每种任务类型有独立的处理器
- 支持重试机制和错误处理
- 可扩展，易于添加新的任务类型

**处理器类型**：
- `CrawlJobHandler`: 爬虫任务处理器
- `MaintenanceJobHandler`: 维护任务处理器  
- `ReportJobHandler`: 报告任务处理器

**执行流程**：
```python
async def execute_with_retry(context):
    for attempt in range(max_retries + 1):
        try:
            result = await execute(context)
            if result.success:
                await on_success(context, result)
                return result
            else:
                if should_retry(result.exception, attempt):
                    await on_retry(context, attempt + 1)
                    await asyncio.sleep(get_retry_delay(attempt + 1))
                    continue
        except Exception as e:
            if should_retry(e, attempt):
                continue
            else:
                break
    
    await on_failure(context, last_exception)
    return error_result
```

### 2.3 JobContext (任务上下文)

**包含信息**：
- 任务标识: job_id, job_name
- 时间信息: trigger_time, scheduled_time
- 执行参数: job_data, executor
- 重试控制: retry_count, max_retries

### 2.4 JobResult (任务结果)

**结果信息**：
- 执行状态: success (bool)
- 结果消息: message (str)
- 返回数据: data (dict)
- 异常信息: exception (Exception)
- 性能数据: execution_time, timestamp, retry_count

## 3. APScheduler 框架集成

### 3.1 调度器配置

```python
# JobStore 配置 - 使用 SQLAlchemy 持久化任务
jobstores = {
    'default': SQLAlchemyJobStore(url=database_url)
}

# Executor 配置 - 使用异步执行器
executors = {
    'default': AsyncIOExecutor(max_workers=4)
}

# 调度器实例
scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults={
        'coalesce': False,      # 不合并错过的任务
        'max_instances': 1      # 每个任务最多1个实例
    },
    timezone='Asia/Shanghai'
)
```

### 3.2 触发器类型

**IntervalTrigger (间隔触发)**：
```python
# 每小时执行一次
trigger = IntervalTrigger(seconds=3600)
```

**CronTrigger (定时触发)**：
```python
# 每天凌晨2点执行
trigger = CronTrigger(
    minute=0, hour=2, day='*', month='*', day_of_week='*'
)
```

**DateTrigger (一次性触发)**：
```python
# 指定时间执行一次
trigger = DateTrigger(run_date=datetime(2024, 1, 1, 12, 0, 0))
```

## 4. 任务生命周期

### 4.1 周期性任务流程

```
1. 系统启动 → 2. 调度器启动 → 3. 加载预定义任务 → 4. 计算下次执行时间
                                                        ↓
8. 更新下次执行时间 ← 7. 记录结果 ← 6. 执行任务 ← 5. 触发时间到达
```

### 4.2 动态任务流程

```
1. API 请求 → 2. 创建任务记录 → 3. 添加到调度器 → 4. 立即/定时执行
                                                   ↓
8. 自动删除任务 ← 7. 更新数据库状态 ← 6. 执行完成 ← 5. 后台执行
```

## 5. 并发和性能控制

### 5.1 并发控制

- **max_workers**: 控制执行器最大并发数
- **max_instances**: 控制单个任务最大实例数
- **coalesce**: 控制是否合并错过的任务执行

### 5.2 性能优化

```python
# 1. 连接池管理
class CrawlerManager:
    def __init__(self):
        self.session = httpx.AsyncClient()  # 复用连接
    
    async def close(self):
        await self.session.aclose()         # 确保关闭

# 2. 并发控制
semaphore = asyncio.Semaphore(5)  # 限制同时爬取数量

async def crawl_single_book(book_id):
    async with semaphore:
        return await self._crawl_book_detail(book_id)

# 3. 批量处理
await asyncio.gather(*tasks, return_exceptions=True)
```

## 6. 错误处理和监控

### 6.1 重试策略

```python
def should_retry(exception, attempt):
    # 网络错误可重试
    retryable_exceptions = (ConnectionError, TimeoutError)
    return isinstance(exception, retryable_exceptions)

def get_retry_delay(attempt):
    # 指数退避：1, 2, 4, 8, ... 秒，最大60秒
    return min(2 ** (attempt - 1), 60)
```

### 6.2 状态监控

```python
def get_status():
    return {
        "status": "running" if scheduler.running else "paused",
        "job_count": len(scheduler.get_jobs()),
        "running_jobs": count_running_jobs(),
        "paused_jobs": count_paused_jobs(),
        "uptime": get_uptime()
    }
```

### 6.3 事件监听

```python
def _job_listener(event):
    if event.code == events.EVENT_JOB_EXECUTED:
        logger.info(f"任务 {event.job_id} 执行完成")
    elif event.code == events.EVENT_JOB_ERROR:
        logger.error(f"任务 {event.job_id} 执行失败: {event.exception}")
```

## 7. 数据库集成

### 7.1 任务状态同步

```python
async def _update_task_status(self, task_id, status, message):
    async for session in get_session():
        try:
            task_service = CrawlTaskService(session)
            await task_service.update_task_status(task_id, status, message)
            break
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
```

### 7.2 结果持久化

- 爬虫结果通过 `CrawlerManager` 直接存储到业务数据库
- 任务执行状态通过 `CrawlTaskService` 存储到任务表
- APScheduler 任务元数据存储到调度器数据库

## 8. API 接口设计

### 8.1 动态任务触发

```python
@router.post("/crawl/all")
async def crawl_all_pages():
    # 1. 生成任务ID
    task_id = f"crawl_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 2. 创建数据库记录
    await task_service.create_task(task_id, "all_pages", ["all"])
    
    # 3. 添加到调度器
    await scheduler.add_one_time_job(
        job_id=task_id,
        handler_class_name="crawl",
        job_data={"type": "category", "task_id": task_id}
    )
    
    # 4. 立即返回任务ID
    return {"task_id": task_id, "message": "任务已添加到调度器"}
```

### 8.2 任务状态查询

```python
@router.get("/crawl/tasks/{task_id}")
async def get_task_status(task_id: str):
    # 从数据库查询任务状态
    task = await task_service.get_task_by_id(task_id)
    
    # 从调度器查询执行状态
    scheduler_job = scheduler.get_job(task_id)
    
    return {
        "task_id": task_id,
        "status": task.status,
        "message": task.message,
        "scheduler_status": "running" if scheduler_job else "completed"
    }
```

## 9. 部署和运维

### 9.1 生产环境配置

```python
# config.py
class SchedulerSettings:
    max_workers: int = 4                    # 执行器并发数
    job_store_url: str = "sqlite:///jobs.db"  # 任务持久化数据库
    timezone: str = "Asia/Shanghai"         # 时区设置
    job_defaults: dict = {
        'coalesce': False,
        'max_instances': 1,
        'misfire_grace_time': 30
    }
```

### 9.2 监控指标

- 任务成功率
- 平均执行时间
- 队列长度
- 错误率
- 资源使用情况

### 9.3 故障恢复

- 调度器重启后自动恢复任务状态
- 未完成的任务会重新调度
- 错过的任务根据 `misfire_grace_time` 决定是否执行

## 10. 最佳实践

### 10.1 任务设计原则

1. **幂等性**: 任务多次执行结果一致
2. **无状态**: 任务不依赖外部状态
3. **快速失败**: 尽早发现并报告错误
4. **资源清理**: 确保资源在任务结束后释放

### 10.2 性能优化建议

1. **合理设置并发数**: 根据资源情况调整 max_workers
2. **批量处理**: 减少数据库操作次数
3. **连接复用**: 使用连接池管理数据库和HTTP连接
4. **异步优先**: 使用异步操作避免阻塞

### 10.3 运维建议

1. **监控告警**: 设置任务失败率告警
2. **日志管理**: 详细记录任务执行日志
3. **备份策略**: 定期备份任务配置和状态
4. **版本控制**: 任务代码变更需要版本管理

这个设计文档详细说明了调度器的架构、实现细节和最佳实践，可以帮助理解整个调度系统的工作原理。