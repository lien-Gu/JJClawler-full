"""
调度模块 - 模块化的任务调度系统

APScheduler 调度器设计说明:
=========================

## 核心组件
1. TaskScheduler: 任务调度器主类，管理任务的生命周期
2. JobHandlers: 任务处理器，负责具体任务的执行逻辑
3. JobContext: 任务执行上下文，包含任务参数和状态
4. JobResult: 任务执行结果，包含成功状态和执行数据

## 工作流程
1. FastAPI 启动时自动启动调度器
2. 调度器加载预定义的周期性任务（如定时爬取）
3. API 通过 add_one_time_job() 添加一次性任务（如手动触发爬取）
4. 调度器根据触发器规则执行任务
5. 任务执行完成后更新状态到数据库

## 任务类型
- 周期性任务: 通过 JobConfigModel 定义，使用 IntervalTrigger 或 CronTrigger
- 一次性任务: 通过 add_one_time_job() 添加，立即执行或定时执行

## 优势
- 统一的任务管理: 所有任务都通过调度器管理，便于监控和控制
- 异步执行: 任务在后台异步执行，不阻塞 API 响应
- 持久化: 使用数据库存储任务状态，重启后任务不丢失
- 可扩展: 支持自定义任务处理器和触发器
"""

from .handlers import BaseJobHandler, CrawlJobHandler, ReportJobHandler
from .scheduler import TaskScheduler, get_scheduler, start_scheduler, stop_scheduler

__all__ = [
    "TaskScheduler",
    "BaseJobHandler",
    "CrawlJobHandler",
    "ReportJobHandler",
    "get_scheduler",
    "start_scheduler",
    "stop_scheduler",
]
