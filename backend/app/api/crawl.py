"""
爬虫管理接口

提供爬虫任务触发、状态查询和监控的API端点
集成调度器功能，支持手动触发和定时任务管理
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.modules.models import CrawlPageRequest
from app.modules.task import get_task_manager
from app.modules.task import get_task_scheduler, trigger_manual_crawl
from app.utils.error_codes import StatusCode
from app.utils.response_utils import ApiResponse, success_response, error_response

router = APIRouter(prefix="/crawl", tags=["爬虫管理"])


@router.post("/page/{page_id}", response_model=ApiResponse[dict])
async def trigger_page_crawl(
    page_id: str, request: CrawlPageRequest = CrawlPageRequest()
):
    """
    触发特定分类页面爬取

    启动指定分类页面的爬取任务，根据页面配置的更新频率执行。
    支持立即执行和调度器触发两种方式。
    """
    try:
        # 验证频道是否有效
        task_manager = get_task_manager()
        all_configs = task_manager.get_all_task_configs()
        valid_ids = [config.id for config in all_configs]

        if page_id not in valid_ids:
            error_resp = error_response(
                code=StatusCode.PARAMETER_INVALID, message=f"无效ID: {page_id}"
            )
            raise HTTPException(status_code=400, detail=error_resp.model_dump())

        task_id = trigger_manual_crawl(page_id)
        message = f"分类页面 {page_id} 爬取任务已立即触发"

        return success_response(
            data={
                "task_id": task_id,
                "channel": page_id,
                "status": "pending",
                "force": request.force,
                "immediate": request.immediate,
            },
            message=message + (" (强制模式)" if request.force else ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        error_resp = error_response(
            code=StatusCode.TASK_CREATE_FAILED, message="创建任务失败"
        )
        raise HTTPException(status_code=500, detail=error_resp.model_dump())


@router.get("/jobs", response_model=ApiResponse[dict])
async def get_scheduled_jobs():
    """
    获取调度任务列表

    查询APScheduler中的调度任务状态
    """
    try:
        scheduler = get_task_scheduler()
        jobs = scheduler.get_scheduled_jobs()
        status = scheduler.get_status()

        return success_response(
            data={
                "scheduled_jobs": jobs,
                "scheduler_status": status,
                "total_jobs": len(jobs),
            },
            message="获取调度任务成功",
        )

    except Exception as e:
        error_resp = error_response(
            code=StatusCode.INTERNAL_ERROR, message="获取调度任务失败"
        )
        raise HTTPException(status_code=500, detail=error_resp.model_dump())


@router.get("/channels", response_model=ApiResponse[dict])
async def get_available_channels():
    """
    获取可用的爬取频道列表

    返回所有可以爬取的频道信息，包括夹子榜和各个分类页面
    """
    try:
        task_manager = get_task_manager()
        hierarchy = task_manager.get_pages_hierarchy()

        # 转换为频道格式
        channels = []
        for config in hierarchy["root"]:
            channels.append(
                {
                    "id": config.id,
                    "name": config.name,
                    "frequency": config.frequency,
                    "interval": config.interval,
                }
            )

        for parent_id, child_configs in hierarchy["children"].items():
            for config in child_configs:
                channels.append(
                    {
                        "id": config.id,
                        "name": config.name,
                        "frequency": config.frequency,
                        "interval": config.interval,
                        "parent_id": config.parent_id,
                    }
                )

        return success_response(
            data={"channels": channels, "total": len(channels)},
            message="获取频道列表成功",
        )

    except Exception as e:
        error_resp = error_response(
            code=StatusCode.INTERNAL_ERROR, message="获取频道列表失败"
        )
        raise HTTPException(status_code=500, detail=error_resp.model_dump())


@router.get("/scheduler/status", response_model=ApiResponse[dict])
async def get_scheduler_status():
    """
    获取调度器状态信息

    返回调度器的运行状态、任务统计和配置信息
    """
    try:
        scheduler = get_task_scheduler()
        status_info = scheduler.get_status()
        scheduled_jobs = scheduler.get_scheduled_jobs()

        return success_response(
            data={
                "status": "running" if status_info["is_running"] else "stopped",
                "statistics": status_info,
                "scheduled_jobs": scheduled_jobs,
            },
            message="获取调度器状态成功",
        )

    except Exception as e:
        error_resp = error_response(
            code=StatusCode.INTERNAL_ERROR, message="获取调度器状态失败"
        )
        raise HTTPException(status_code=500, detail=error_resp.model_dump())


@router.get("/scheduler/jobs", response_model=ApiResponse[dict])
async def get_scheduled_jobs():
    """
    获取所有定时任务信息

    返回调度器中配置的所有定时任务详情
    """
    try:
        scheduler = get_task_scheduler()
        jobs = scheduler.get_scheduled_jobs()

        return success_response(
            data={"jobs": jobs, "total": len(jobs)}, message="获取定时任务成功"
        )

    except Exception as e:
        error_resp = error_response(
            code=StatusCode.INTERNAL_ERROR, message="获取定时任务失败"
        )
        raise HTTPException(status_code=500, detail=error_resp.model_dump())


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
                "timestamp": datetime.now().isoformat(),
            },
            message=f"已手动触发 {target} 爬取任务",
        )

    except Exception as e:
        error_resp = error_response(
            code=StatusCode.INTERNAL_ERROR, message="触发任务失败"
        )
        raise HTTPException(status_code=500, detail=error_resp.model_dump())
