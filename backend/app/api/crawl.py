"""
爬虫管理接口

提供爬虫任务触发、状态查询和监控的API端点
集成调度器功能，支持手动触发和定时任务管理
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.modules.models import CrawlPageRequest
from app.modules.service.crawl_service import get_crawl_service
from app.modules.service.scheduler_service import (
    get_scheduler_service,
    trigger_manual_crawl
)
from app.modules.service.task_monitor_service import get_task_monitor_service
from app.utils.error_codes import StatusCode
from app.utils.response_utils import ApiResponse, success_response, error_response

router = APIRouter(prefix="/crawl", tags=["爬虫管理"])


@router.post("/page/{id}", response_model=ApiResponse[dict])
async def trigger_page_crawl(
        id: str,
        request: CrawlPageRequest = CrawlPageRequest()
):
    """
    触发特定分类页面爬取
    
    启动指定分类页面的爬取任务，根据页面配置的更新频率执行。
    支持立即执行和调度器触发两种方式。
    """
    try:
        # 验证频道是否有效
        crawl_service = get_crawl_service()
        all_tasks = crawl_service.get_all_task_configs()
        valid_ids = [task.id for task in all_tasks]

        if id not in valid_ids:
            error_resp = error_response(
                code=StatusCode.PARAMETER_INVALID,
                message=f"无效ID: {id}"
            )
            raise HTTPException(
                status_code=400,
                detail=error_resp.model_dump()
            )

        if request.immediate:
            # 立即通过调度器执行
            task_id = trigger_manual_crawl(id)
            message = f"分类页面 {id} 爬取任务已立即触发"
        else:
            # 创建执行任务
            task_id = crawl_service.create_execution_task(id)
            message = f"分类页面 {id} 爬取任务已创建"

        return success_response(
            data={
                "task_id": task_id,
                "channel": id,
                "status": "pending",
                "force": request.force,
                "immediate": request.immediate
            },
            message=message + (" (强制模式)" if request.force else "")
        )

    except HTTPException:
        raise
    except Exception as e:
        error_resp = error_response(code=StatusCode.TASK_CREATE_FAILED, message="创建任务失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.get("/tasks", response_model=ApiResponse[dict])
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
        crawl_service = get_crawl_service()
        all_tasks = crawl_service.get_all_tasks()

        current_tasks = []
        completed_tasks = []
        failed_tasks = []

        # 转换任务信息格式  
        def task_to_dict(task):
            return {
                "task_id": task.task_id,
                "task_type": task.id,  # 使用配置ID作为任务类型
                "status": task.status.value if hasattr(task.status, 'value') else task.status,
                "created_at": task.created_at,  # 已经是ISO格式字符串
                "started_at": task.started_at,
                "completed_at": getattr(task, 'completed_at', None),
                "progress": task.progress,
                "items_crawled": task.items_crawled,
                "ranking_id": task.metadata.get('channel') if task.metadata else None
            }

        for task in all_tasks["current"]:
            current_tasks.append(task_to_dict(task))

        for task in all_tasks["completed"]:
            completed_tasks.append(task_to_dict(task))

        for task in all_tasks["failed"]:
            failed_tasks.append(task_to_dict(task))

        # 合并完成和失败的任务
        all_completed = completed_tasks + failed_tasks

        # 根据筛选条件过滤
        if status:
            current_tasks = [t for t in current_tasks if t["status"] == status]
            all_completed = [t for t in all_completed if t["status"] == status]

        if task_type:
            current_tasks = [t for t in current_tasks if t["task_type"] == task_type]
            all_completed = [t for t in all_completed if t["task_type"] == task_type]

        # 分页
        paginated_completed = all_completed[offset:offset + limit]

        return success_response(
            data={
                "current_tasks": current_tasks,  # 已经是字典了，不需要model_dump
                "completed_tasks": paginated_completed,  # 已经是字典了，不需要model_dump
                "total_current": len(current_tasks),
                "total_completed": len(all_completed),
                "filters": {
                    "status": status,
                    "task_type": task_type
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset
                }
            },
            message="获取任务列表成功"
        )

    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="获取任务列表失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.get("/tasks/{task_id}", response_model=ApiResponse[dict])
async def get_task_detail(task_id: str):
    """
    获取特定任务详情
    
    查询指定任务ID的详细信息和状态
    """
    try:
        crawl_service = get_crawl_service()
        task = crawl_service.get_task_status(task_id)

        if not task:
            error_resp = error_response(code=StatusCode.TASK_NOT_FOUND, message="任务不存在")
            raise HTTPException(
                status_code=404,
                detail=error_resp.model_dump()
            )

        return success_response(
            data={
                "task_id": task.task_id,
                "task_type": task.id,  # 使用配置ID作为任务类型
                "status": task.status.value if hasattr(task.status, 'value') else task.status,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": getattr(task, 'completed_at', None),
                "progress": task.progress,
                "items_crawled": task.items_crawled,
                "ranking_id": task.metadata.get('channel') if task.metadata else None,
                "metadata": task.metadata
            },
            message="获取任务详情成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="获取任务详情失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.get("/channels", response_model=ApiResponse[dict])
async def get_available_channels():
    """
    获取可用的爬取频道列表
    
    返回所有可以爬取的频道信息，包括夹子榜和各个分类页面
    """
    try:
        crawl_service = get_crawl_service()
        pages = crawl_service.get_pages_hierarchy()
        
        # 转换为频道格式
        channels = []
        for root_page in pages["root"]:
            channels.append({
                "id": root_page.id,
                "name": root_page.name,
                "frequency": root_page.frequency,
                "interval": root_page.interval
            })
        
        for parent_id, child_pages in pages["children"].items():
            for child_page in child_pages:
                channels.append({
                    "id": child_page.id,
                    "name": child_page.name,
                    "frequency": child_page.frequency,
                    "interval": child_page.interval,
                    "parent_id": child_page.parent_id
                })

        return success_response(
            data={
                "channels": channels,
                "total": len(channels)
            },
            message="获取频道列表成功"
        )

    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="获取频道列表失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.get("/scheduler/status", response_model=ApiResponse[dict])
async def get_scheduler_status():
    """
    获取调度器状态信息
    
    返回调度器的运行状态、任务统计和配置信息
    """
    try:
        scheduler_service = get_scheduler_service()
        status_info = scheduler_service.get_status()
        scheduled_jobs = scheduler_service.get_scheduled_jobs()

        return success_response(
            data={
                "status": "running" if status_info['is_running'] else "stopped",
                "statistics": status_info,
                "scheduled_jobs": scheduled_jobs
            },
            message="获取调度器状态成功"
        )

    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="获取调度器状态失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.get("/scheduler/jobs", response_model=ApiResponse[dict])
async def get_scheduled_jobs():
    """
    获取所有定时任务信息
    
    返回调度器中配置的所有定时任务详情
    """
    try:
        scheduler_service = get_scheduler_service()
        jobs = scheduler_service.get_scheduled_jobs()

        return success_response(
            data={
                "jobs": jobs,
                "total": len(jobs)
            },
            message="获取定时任务成功"
        )

    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="获取定时任务失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.post("/scheduler/trigger/{target}", response_model=ApiResponse[dict])
async def trigger_scheduled_job(target: str):
    """
    手动触发调度任务
    
    立即执行指定的爬取任务，target可以是"jiazi"或频道名
    """
    try:
        task_id = trigger_manual_crawl(target)

        return success_response(
            data={
                "task_id": task_id,
                "target": target,
                "timestamp": datetime.now().isoformat()
            },
            message=f"已手动触发 {target} 爬取任务"
        )

    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="触发任务失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.get("/monitor/status", response_model=ApiResponse[dict])
async def get_monitor_status():
    """
    获取任务监控状态
    
    返回任务监控服务的运行状态，包括缺失任务信息和重试历史。
    用于了解系统是否正常运行，以及是否有任务需要人工干预。
    """
    try:
        monitor_service = get_task_monitor_service()
        status = monitor_service.get_monitoring_status()

        return success_response(
            data=status,
            message="获取监控状态成功"
        )

    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="获取监控状态失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )


@router.post("/monitor/check", response_model=ApiResponse[dict])
async def manual_check_missing_tasks():
    """
    手动检查缺失任务
    
    立即执行一次任务检查，而不等待定时检查。
    用于调试或在修复问题后立即验证系统状态。
    """
    try:
        monitor_service = get_task_monitor_service()

        # 手动触发一次检查
        await monitor_service._check_missing_tasks()

        status = monitor_service.get_monitoring_status()

        return success_response(
            data=status,
            message="手动检查已完成"
        )

    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="手动检查失败")
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )
