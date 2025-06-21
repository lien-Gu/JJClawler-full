"""
爬虫管理接口

提供爬虫任务触发、状态查询和监控的API端点
"""
import asyncio
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from app.modules.models import (
    TasksResponse,
    TaskCreateResponse,
    CrawlJiaziRequest,
    CrawlRankingRequest,
    TaskInfo
)
from app.modules.service.task_service import (
    get_task_manager,
    create_jiazi_task,
    create_page_task,
    execute_jiazi_task,
    execute_page_task,
    TaskType
)
from app.modules.service.crawler_service import CrawlerService

router = APIRouter(prefix="/crawl", tags=["爬虫管理"])


@router.post("/jiazi", response_model=TaskCreateResponse)
async def trigger_jiazi_crawl(
    background_tasks: BackgroundTasks,
    request: CrawlJiaziRequest = CrawlJiaziRequest()
):
    """
    触发夹子榜单爬取
    
    启动夹子榜单的爬取任务，夹子榜单是热度最高的榜单，
    需要频繁更新
    """
    try:
        # 创建任务
        task_id = create_jiazi_task()
        
        # 在后台执行任务
        background_tasks.add_task(execute_jiazi_task, task_id)
        
        return TaskCreateResponse(
            task_id=task_id,
            message="夹子榜单爬取任务已创建" + (" (强制模式)" if request.force else ""),
            status="pending"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/page/{channel}", response_model=TaskCreateResponse)
async def trigger_page_crawl(
    channel: str,
    background_tasks: BackgroundTasks,
    request: CrawlRankingRequest = CrawlRankingRequest()
):
    """
    触发特定分类页面爬取
    
    启动指定分类页面的爬取任务，根据页面配置的更新频率执行
    """
    try:
        # 验证频道是否有效
        crawler = CrawlerController()
        available_channels = await crawler.get_available_channels()
        await crawler.close()
        
        valid_channels = [ch['short_name'] for ch in available_channels]
        if channel not in valid_channels:
            raise HTTPException(status_code=404, detail=f"分类页面 {channel} 不存在")
        
        # 创建任务
        task_id = create_page_task(channel)
        
        # 在后台执行任务
        background_tasks.add_task(execute_page_task, task_id, channel)
        
        return TaskCreateResponse(
            task_id=task_id,
            message=f"分类页面 {channel} 爬取任务已创建" + (" (强制模式)" if request.force else ""),
            status="pending"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/tasks", response_model=TasksResponse)
async def get_tasks(
    status: Optional[str] = Query(None, description="状态筛选 (pending/running/completed/failed)"),
    task_type: Optional[str] = Query(None, description="类型筛选 (jiazi/page/book_detail)"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取爬取任务列表
    
    查询当前和历史爬取任务的状态，支持按状态和类型筛选
    """
    try:
        task_manager = get_task_manager()
        all_tasks = task_manager.file_manager.get_all_tasks()
        
        current_tasks = []
        completed_tasks = []
        failed_tasks = []
        
        # 转换任务信息格式
        for task in all_tasks["current"]:
            current_tasks.append(TaskInfo(
                task_id=task.task_id,
                task_type=task.task_type,
                status=task.status,
                created_at=datetime.fromisoformat(task.created_at),
                started_at=datetime.fromisoformat(task.started_at) if task.started_at else None,
                completed_at=None,
                progress=task.progress,
                items_crawled=task.items_crawled,
                ranking_id=task.metadata.get('channel') if task.metadata else None
            ))
        
        for task in all_tasks["completed"]:
            completed_tasks.append(TaskInfo(
                task_id=task.task_id,
                task_type=task.task_type,
                status=task.status,
                created_at=datetime.fromisoformat(task.created_at),
                started_at=datetime.fromisoformat(task.started_at) if task.started_at else None,
                completed_at=datetime.fromisoformat(task.completed_at) if task.completed_at else None,
                progress=task.progress,
                items_crawled=task.items_crawled,
                ranking_id=task.metadata.get('channel') if task.metadata else None
            ))
        
        for task in all_tasks["failed"]:
            failed_tasks.append(TaskInfo(
                task_id=task.task_id,
                task_type=task.task_type,
                status=task.status,
                created_at=datetime.fromisoformat(task.created_at),
                started_at=datetime.fromisoformat(task.started_at) if task.started_at else None,
                completed_at=datetime.fromisoformat(task.completed_at) if task.completed_at else None,
                progress=task.progress,
                items_crawled=task.items_crawled,
                ranking_id=task.metadata.get('channel') if task.metadata else None
            ))
        
        # 合并完成和失败的任务
        all_completed = completed_tasks + failed_tasks
        
        # 根据筛选条件过滤
        if status:
            current_tasks = [t for t in current_tasks if t.status == status]
            all_completed = [t for t in all_completed if t.status == status]
        
        if task_type:
            current_tasks = [t for t in current_tasks if t.task_type == task_type]
            all_completed = [t for t in all_completed if t.task_type == task_type]
        
        # 分页
        paginated_completed = all_completed[offset:offset + limit]
        
        return TasksResponse(
            current_tasks=current_tasks,
            completed_tasks=paginated_completed,
            total_current=len(current_tasks),
            total_completed=len(all_completed)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务列表失败: {str(e)}")


@router.get("/tasks/{task_id}", response_model=TaskInfo)
async def get_task_detail(task_id: str):
    """
    获取特定任务详情
    
    查询指定任务ID的详细信息和状态
    """
    try:
        task_manager = get_task_manager()
        task = task_manager.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")
        
        return TaskInfo(
            task_id=task.task_id,
            task_type=task.task_type,
            status=task.status,
            created_at=datetime.fromisoformat(task.created_at),
            started_at=datetime.fromisoformat(task.started_at) if task.started_at else None,
            completed_at=datetime.fromisoformat(task.completed_at) if task.completed_at else None,
            progress=task.progress,
            items_crawled=task.items_crawled,
            ranking_id=task.metadata.get('channel') if task.metadata else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务详情失败: {str(e)}")


@router.get("/channels")
async def get_available_channels():
    """
    获取可用的爬取频道列表
    
    返回所有可以爬取的频道信息，包括甲子榜和各个分类页面
    """
    try:
        crawler = CrawlerController()
        channels = await crawler.get_available_channels()
        await crawler.close()
        
        return {
            "channels": channels,
            "total": len(channels)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取频道列表失败: {str(e)}")