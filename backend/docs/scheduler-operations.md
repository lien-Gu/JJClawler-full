# 定时任务调度系统操作指南

## 概述

JJCrawler3 使用 APScheduler (Advanced Python Scheduler) 实现自动化任务调度，支持多频率爬取任务管理、智能错误处理和实时状态监控。

## 目录

1. [调度器架构](#调度器架构)
2. [定时任务配置](#定时任务配置)
3. [任务管理操作](#任务管理操作)
4. [监控和日志](#监控和日志)
5. [故障排除](#故障排除)
6. [性能优化](#性能优化)

## 调度器架构

### 核心组件

```
┌─────────────────────────────────────────┐
│            FastAPI 应用生命周期             │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          SchedulerService               │
│  ┌─────────────────────────────────────┐ │
│  │      AsyncIOScheduler               │ │
│  │  - CronTrigger (定时触发)            │ │
│  │  - IntervalTrigger (间隔触发)        │ │
│  │  - DateTrigger (一次性任务)          │ │
│  └─────────────────────────────────────┘ │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          任务执行层                      │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ 夹子榜爬取   │  │  分类页面爬取    │   │
│  │ (每小时)     │  │  (每日错开)     │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────┬───────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│          任务管理系统                    │
│  - 任务状态跟踪                         │
│  - 错误处理和重试                       │
│  - 统计信息收集                         │
└─────────────────────────────────────────┘
```

### 调度器特性

- **异步执行**: 基于 AsyncIOScheduler，完美适配 FastAPI 异步架构
- **多触发器支持**: Cron、Interval、Date 三种触发器类型
- **任务隔离**: 每个任务独立执行，互不干扰
- **错误恢复**: 完善的异常处理和重试机制
- **资源管理**: 自动生命周期管理和资源清理
- **实时监控**: 详细的任务统计和状态监控

## 定时任务配置

### 1. 配置文件设置

在 `app/config.py` 中配置调度器参数：

```python
class Settings(BaseSettings):
    # 任务调度配置
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    JIAZI_SCHEDULE: str = "0 */1 * * *"  # 每小时执行
    RANKING_SCHEDULE: str = "0 0 * * *"  # 每天执行
```

### 2. 环境变量配置

在 `.env` 文件中自定义调度参数：

```env
# 调度器时区设置
SCHEDULER_TIMEZONE=Asia/Shanghai

# 夹子榜爬取频率 (Cron 表达式)
# 格式: 分 时 日 月 周
JIAZI_SCHEDULE=0 */1 * * *

# 分类榜单爬取频率
RANKING_SCHEDULE=0 2 * * *
```

### 3. 定时任务类型

#### 夹子榜任务 (高频率)

```python
# 每小时整点执行
self.scheduler.add_job(
    func=self._execute_jiazi_crawl,
    trigger=CronTrigger(minute=0),  # 每小时0分
    id="jiazi_hourly",
    max_instances=1,  # 防止重复执行
    misfire_grace_time=300,  # 5分钟容错时间
    replace_existing=True
)
```

#### 分类页面任务 (错开执行)

```python
# 根据频道数量错开执行时间
for i, channel_info in enumerate(channels):
    hour = 1 + (i % 6)  # 分布在1-6点
    minute = (i * 10) % 60  # 错开分钟
    
    self.scheduler.add_job(
        func=self._execute_page_crawl,
        trigger=CronTrigger(hour=hour, minute=minute),
        args=[channel],
        id=f"page_daily_{channel}",
        max_instances=1,
        misfire_grace_time=1800,  # 30分钟容错时间
        replace_existing=True
    )
```

#### 清理任务 (低频率)

```python
# 每周日凌晨2点清理旧任务
self.scheduler.add_job(
    func=self._cleanup_old_tasks,
    trigger=CronTrigger(day_of_week=0, hour=2),
    id="task_cleanup_weekly",
    max_instances=1,
    replace_existing=True
)
```

### 4. Cron 表达式详解

| 字段 | 范围 | 特殊字符 | 示例 |
|------|------|----------|------|
| 分钟 | 0-59 | * , - / | `0` (每小时0分), `*/15` (每15分钟) |
| 小时 | 0-23 | * , - / | `2` (凌晨2点), `9-17` (工作时间) |
| 日期 | 1-31 | * , - / ? | `1` (每月1号), `*/2` (每两天) |
| 月份 | 1-12 | * , - / | `*` (每月), `6-8` (夏季) |
| 星期 | 0-6 | * , - / ? | `0` (周日), `1-5` (工作日) |

**常用 Cron 表达式示例:**

```bash
# 每小时执行
0 * * * *

# 每天凌晨2点执行
0 2 * * *

# 每工作日上午9点执行
0 9 * * 1-5

# 每15分钟执行一次
*/15 * * * *

# 每月1号凌晨3点执行
0 3 1 * *
```

## 任务管理操作

### 1. 启动和停止调度器

#### 自动启动 (随应用启动)

```python
# app/main.py 中已集成
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动调度器
    from app.modules.service.scheduler_service import start_scheduler
    await start_scheduler()
    logger.info("任务调度器启动成功")
    
    yield
    
    # 停止调度器
    from app.modules.service.scheduler_service import stop_scheduler
    stop_scheduler()
    logger.info("任务调度器已停止")
```

#### 手动控制

```bash
# 通过 API 控制调度器
curl -X POST http://localhost:8000/api/v1/crawl/scheduler/start
curl -X POST http://localhost:8000/api/v1/crawl/scheduler/stop
curl -X GET http://localhost:8000/api/v1/crawl/scheduler/status
```

### 2. 查看定时任务状态

#### 通过 API 查询

```bash
# 获取所有定时任务
curl http://localhost:8000/api/v1/crawl/scheduler/jobs

# 获取调度器统计信息
curl http://localhost:8000/api/v1/crawl/scheduler/stats
```

#### 响应示例

```json
{
  "jobs": [
    {
      "id": "jiazi_hourly",
      "next_run_time": "2024-06-23T14:00:00+08:00",
      "func_ref": "_execute_jiazi_crawl",
      "max_instances": 1,
      "misfire_grace_time": 300
    },
    {
      "id": "page_daily_yq",
      "next_run_time": "2024-06-24T01:00:00+08:00",
      "func_ref": "_execute_page_crawl",
      "max_instances": 1,
      "misfire_grace_time": 1800
    }
  ],
  "stats": {
    "total_executed": 156,
    "total_failed": 3,
    "total_succeeded": 153,
    "last_execution": "2024-06-23T13:00:00+08:00",
    "is_running": true,
    "active_jobs": 8
  }
}
```

### 3. 手动触发任务

#### 立即执行爬取任务

```bash
# 手动触发夹子榜爬取
curl -X POST http://localhost:8000/api/v1/crawl/jiazi

# 手动触发特定频道爬取
curl -X POST "http://localhost:8000/api/v1/crawl/page?channel=yq"

# 批量触发所有页面爬取
curl -X POST http://localhost:8000/api/v1/crawl/page/all
```

#### 通过调度器添加一次性任务

```python
# 在 Python 代码中添加即时任务
from app.modules.service.scheduler_service import get_scheduler_service

scheduler_service = get_scheduler_service()

# 添加一次性任务
job_id = scheduler_service.add_manual_job(
    job_func=some_function,
    arg1="value1",
    arg2="value2"
)
```

### 4. 任务管理高级操作

#### 暂停和恢复任务

```python
from app.modules.service.scheduler_service import get_scheduler_service

scheduler_service = get_scheduler_service()

# 暂停特定任务
scheduler_service.scheduler.pause_job("jiazi_hourly")

# 恢复任务
scheduler_service.scheduler.resume_job("jiazi_hourly")

# 暂停所有任务
scheduler_service.scheduler.pause()

# 恢复所有任务
scheduler_service.scheduler.resume()
```

#### 修改任务调度时间

```python
from apscheduler.triggers.cron import CronTrigger

# 修改夹子榜任务为每30分钟执行
scheduler_service.scheduler.modify_job(
    "jiazi_hourly",
    trigger=CronTrigger(minute="0,30")
)

# 修改任务为每2小时执行
scheduler_service.scheduler.modify_job(
    "jiazi_hourly", 
    trigger=CronTrigger(hour="*/2", minute=0)
)
```

#### 删除任务

```python
# 删除特定任务
scheduler_service.scheduler.remove_job("jiazi_hourly")

# 删除所有任务
scheduler_service.scheduler.remove_all_jobs()
```

## 监控和日志

### 1. 任务执行日志

#### 日志级别配置

```python
# app/utils/log_utils.py
# 调整日志级别以获取不同详细程度的信息

# 调试模式 - 查看详细执行过程
LOG_LEVEL = "DEBUG"

# 信息模式 - 查看关键执行信息 (推荐)
LOG_LEVEL = "INFO"  

# 警告模式 - 仅显示警告和错误
LOG_LEVEL = "WARNING"
```

#### 典型日志输出

```log
2024-06-23 13:00:00,123 - scheduler_service - INFO - 开始执行夹子榜定时爬取
2024-06-23 13:00:00,124 - task_service - INFO - 创建任务: jiazi_20240623_130000
2024-06-23 13:00:02,456 - jiazi_crawler - INFO - 开始爬取夹子榜数据
2024-06-23 13:00:05,789 - jiazi_crawler - INFO - 爬取完成: 新增50本书籍, 更新30本书籍
2024-06-23 13:00:05,890 - task_service - INFO - 任务完成: jiazi_20240623_130000
2024-06-23 13:00:05,891 - scheduler_service - INFO - 夹子榜定时爬取完成: {'books_new': 50, 'books_updated': 30}
```

### 2. 任务统计监控

#### 实时统计信息

```bash
# 查看调度器统计
curl http://localhost:8000/api/v1/crawl/scheduler/stats
```

```json
{
  "total_executed": 1248,
  "total_failed": 15,
  "total_succeeded": 1233,
  "last_execution": "2024-06-23T13:00:05+08:00",
  "is_running": true,
  "startup_complete": true,
  "active_jobs": 8,
  "success_rate": 0.988
}
```

#### 任务历史记录

```bash
# 查看任务执行历史
curl http://localhost:8000/api/v1/crawl/tasks?limit=20&status=completed

# 查看失败任务
curl http://localhost:8000/api/v1/crawl/tasks?status=failed&limit=10
```

### 3. 性能监控指标

#### 关键性能指标 (KPI)

| 指标 | 正常范围 | 监控方法 |
|------|----------|----------|
| 任务成功率 | > 95% | 统计接口 |
| 平均执行时间 | < 60秒 | 日志分析 |
| 内存使用 | < 512MB | 系统监控 |
| CPU 使用率 | < 50% | 系统监控 |
| 任务队列长度 | < 5 | 调度器状态 |

#### 监控脚本示例

```bash
#!/bin/bash
# monitor_scheduler.sh - 调度器监控脚本

check_scheduler_health() {
    local api_response=$(curl -s http://localhost:8000/api/v1/crawl/scheduler/stats)
    local success_rate=$(echo $api_response | jq -r '.success_rate // 0')
    local is_running=$(echo $api_response | jq -r '.is_running')
    
    if (( $(echo "$success_rate < 0.95" | bc -l) )); then
        echo "❌ 警告: 任务成功率过低 ($success_rate)"
        return 1
    fi
    
    if [ "$is_running" != "true" ]; then
        echo "❌ 错误: 调度器未运行"
        return 1
    fi
    
    echo "✅ 调度器运行正常"
    return 0
}

# 执行检查
check_scheduler_health
```

### 4. 错误监控和告警

#### 错误类型分类

```python
# 网络错误处理
async def _handle_crawl_error(self, target: str, error: Exception) -> None:
    error_type = type(error).__name__
    
    if "network" in str(error).lower() or "timeout" in str(error).lower():
        # 网络错误 - 记录但不告警
        logger.warning(f"网络错误，将在下次调度时重试: {target} - {error}")
    elif "parse" in str(error).lower():
        # 解析错误 - 可能需要更新解析器
        logger.error(f"数据解析错误，需要检查页面结构: {target} - {error}")
    else:
        # 其他错误 - 需要人工介入
        logger.error(f"未知错误，需要人工检查: {target} - {error}")
```

#### 告警集成示例

```python
# 钉钉机器人告警示例
async def send_alert(message: str):
    webhook_url = "https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN"
    
    data = {
        "msgtype": "text",
        "text": {
            "content": f"JJCrawler3 告警: {message}"
        }
    }
    
    async with httpx.AsyncClient() as client:
        await client.post(webhook_url, json=data)

# 在错误处理中调用告警
if self._job_stats['total_failed'] > 10:
    await send_alert(f"任务失败次数过多: {self._job_stats['total_failed']}")
```

## 故障排除

### 1. 常见问题诊断

#### 调度器未启动

**症状**: API 返回调度器状态为 false

```bash
# 检查调度器状态
curl http://localhost:8000/api/v1/crawl/scheduler/stats
```

**解决方案**:
```bash
# 重启应用
docker-compose restart

# 或手动启动调度器
curl -X POST http://localhost:8000/api/v1/crawl/scheduler/start
```

#### 任务执行超时

**症状**: 任务长时间处于运行状态

```bash
# 查看运行中的任务
curl http://localhost:8000/api/v1/crawl/tasks?status=in_progress
```

**解决方案**:
```python
# 增加任务超时设置
self.scheduler.add_job(
    func=self._execute_jiazi_crawl,
    trigger=CronTrigger(minute=0),
    id="jiazi_hourly",
    max_instances=1,
    misfire_grace_time=600,  # 增加到10分钟
    replace_existing=True
)
```

#### 任务重复执行

**症状**: 同一时间段有多个相同任务执行

**解决方案**:
```python
# 确保 max_instances=1
# 检查任务 ID 唯一性
# 使用 replace_existing=True
```

### 2. 错误日志分析

#### 任务失败模式分析

```bash
# 分析失败任务的错误模式
curl http://localhost:8000/api/v1/crawl/tasks?status=failed | jq -r '.data[].error_message' | sort | uniq -c | sort -nr
```

#### 高频错误处理

```python
# 常见错误处理策略
ERROR_RETRY_STRATEGIES = {
    "ConnectionError": {"max_retries": 3, "delay": 60},
    "TimeoutError": {"max_retries": 2, "delay": 120},  
    "ParseError": {"max_retries": 1, "delay": 300},
    "RateLimitError": {"max_retries": 5, "delay": 900}
}
```

### 3. 性能问题诊断

#### 内存泄漏检查

```bash
# 监控内存使用趋势
docker stats --no-stream jjcrawler

# 如果内存持续增长，检查:
# 1. 爬虫连接是否正确关闭
# 2. 数据库连接是否泄漏
# 3. 任务管理器是否定期清理
```

#### 任务堆积问题

```bash
# 检查任务队列长度
curl http://localhost:8000/api/v1/crawl/tasks?status=pending | jq '.total'

# 如果任务堆积，考虑:
# 1. 增加执行频率
# 2. 优化任务执行时间
# 3. 增加并发度 (谨慎使用)
```

## 性能优化

### 1. 调度策略优化

#### 错峰执行配置

```python
# 优化频道任务执行时间分布
def _configure_daily_crawl_jobs(self) -> None:
    channels = self.page_service.get_ranking_channels()
    
    # 按重要性和频率分组
    high_priority = ['yq', 'ca', 'ys']  # 1-3点执行
    medium_priority = ['nocp_plus', 'bh']  # 4-5点执行
    
    for i, channel_info in enumerate(channels):
        channel = channel_info['channel']
        if channel == 'jiazi':
            continue
            
        # 根据优先级分配时间段
        if channel in high_priority:
            hour = 1 + high_priority.index(channel)
        elif channel in medium_priority:
            hour = 4 + medium_priority.index(channel)
        else:
            hour = 6
            
        minute = (i * 5) % 60  # 每5分钟错开一个任务
```

#### 动态调度频率

```python
# 根据数据变化频率动态调整
def adjust_schedule_frequency(self, channel: str, change_rate: float):
    """根据数据变化率调整调度频率"""
    if change_rate > 0.1:  # 变化频繁
        # 增加执行频率
        trigger = CronTrigger(hour="*/2", minute=0)
    elif change_rate < 0.01:  # 变化稀少
        # 降低执行频率
        trigger = CronTrigger(hour=6, minute=0, day="*/2")
    else:
        # 保持默认频率
        trigger = CronTrigger(hour=2, minute=0)
    
    self.scheduler.modify_job(
        f"page_daily_{channel}",
        trigger=trigger
    )
```

### 2. 资源使用优化

#### 内存管理

```python
# 优化爬虫服务资源使用
async def _execute_jiazi_crawl(self) -> None:
    crawler_service = None
    try:
        # 任务执行逻辑
        crawler_service = CrawlerService()
        result = await crawler_service.crawl_and_save_jiazi()
        # ... 处理结果
    finally:
        # 确保资源清理
        if crawler_service:
            crawler_service.close()
            del crawler_service
        
        # 强制垃圾回收
        import gc
        gc.collect()
```

#### 数据库连接优化

```python
# 使用连接池和批量操作
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_optimized_session():
    """优化的数据库会话管理"""
    session = SessionLocal()
    try:
        # 批量操作配置
        session.execute("PRAGMA temp_store = MEMORY")
        session.execute("PRAGMA journal_mode = WAL")
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### 3. 监控和调优

#### 性能指标收集

```python
# 收集详细的性能指标
class PerformanceMetrics:
    def __init__(self):
        self.task_durations = {}
        self.memory_usage = []
        self.error_counts = {}
    
    def record_task_duration(self, task_type: str, duration: float):
        if task_type not in self.task_durations:
            self.task_durations[task_type] = []
        self.task_durations[task_type].append(duration)
        
        # 保留最近100次记录
        if len(self.task_durations[task_type]) > 100:
            self.task_durations[task_type] = self.task_durations[task_type][-100:]
    
    def get_average_duration(self, task_type: str) -> float:
        durations = self.task_durations.get(task_type, [])
        return sum(durations) / len(durations) if durations else 0
```

#### 自动优化建议

```python
def generate_optimization_suggestions(self) -> List[str]:
    """生成自动优化建议"""
    suggestions = []
    
    # 检查任务执行时间
    avg_duration = self.get_average_duration("jiazi")
    if avg_duration > 60:
        suggestions.append("夹子榜任务执行时间过长，建议优化爬虫性能")
    
    # 检查失败率
    success_rate = self._job_stats['total_succeeded'] / max(self._job_stats['total_executed'], 1)
    if success_rate < 0.95:
        suggestions.append("任务成功率偏低，建议检查网络和错误处理")
    
    # 检查内存使用
    if self.get_memory_usage() > 500:  # MB
        suggestions.append("内存使用过高，建议优化资源管理")
    
    return suggestions
```

通过以上配置和操作指南，您可以有效地管理和监控 JJCrawler3 的定时任务调度系统，确保数据采集任务的稳定运行和高效执行。