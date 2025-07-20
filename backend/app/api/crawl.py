"""
爬虫管理API接口 - 简化的任务触发器
"""


from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status

from ..models.base import DataResponse
from ..models.schedule import (
    BatchJobResponse,
    BatchStatusResponse,
    SchedulerStatusResponse,
    SinglePageResponse,
)
from ..schedule import get_scheduler

router = APIRouter()


@router.post("/all", response_model=DataResponse[BatchJobResponse])
async def crawl_all_pages(
    force: bool = Query(False, description="是否强制爬取（忽略间隔限制）")
):
    """
    触发爬取所有配置的页面（简化版）

    Args:
        force: 是否强制爬取，忽略最小间隔限制

    Returns:
        DataResponse[str]: 批次任务ID
    """
    # 获取调度器并添加批量任务
    scheduler = get_scheduler()

    # 使用新的批量任务功能，为每个页面创建独立任务
    result = await scheduler.add_batch_jobs(
        page_ids=["all"], force=force  # 使用特殊字符
    )

    if not result["success"]:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"],
        )

    return DataResponse(
        success=True,
        message=result["message"],
        data=BatchJobResponse(
            batch_id=result["batch_id"],
            task_ids=result["task_ids"],
            total_pages=result["total_pages"],
            successful_tasks=result["successful_tasks"],
        ),
    )


@router.post("/pages", response_model=DataResponse[BatchJobResponse])
async def crawl_specific_pages(
    page_ids: list[str],
    force: bool = Query(False, description="是否强制爬取（忽略间隔限制）"),
):
    """
    手动触发爬取指定页面（简化版）

    Args:
        page_ids: 页面ID列表
        force: 是否强制爬取，忽略最小间隔限制

    Returns:
        DataResponse[str]: 批次任务ID
    """
    if not page_ids:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="页面ID列表不能为空",
        )

    # 获取调度器并添加批量任务
    scheduler = get_scheduler()

    # 使用新的批量任务功能，为每个页面创建独立任务
    result = await scheduler.add_batch_jobs(page_ids=page_ids, force=force)

    if not result["success"]:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"],
        )

    return DataResponse(
        success=True,
        message=result["message"],
        data=BatchJobResponse(
            batch_id=result["batch_id"],
            task_ids=result["task_ids"],
            total_pages=result["total_pages"],
            successful_tasks=result["successful_tasks"],
        ),
    )


@router.post("/page/{page_id}", response_model=DataResponse[SinglePageResponse])
async def crawl_single_page(
    page_id: str, force: bool = Query(False, description="是否强制爬取（忽略间隔限制）")
):
    """
    触发爬取单个页面

    Args:
        page_id: 页面ID
        force: 是否强制爬取，忽略最小间隔限制

    Returns:
        DataResponse[str]: 任务ID
    """
    # 获取调度器并添加任务
    scheduler = get_scheduler()

    # 使用新的批量任务功能，即使只有一个页面也能统一处理
    result = await scheduler.add_batch_jobs(page_ids=[page_id], force=force)

    if not result["success"]:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result["message"],
        )

    return DataResponse(
        success=True,
        message=f"已添加单页面爬取任务: {page_id}",
        data=SinglePageResponse(
            batch_id=result["batch_id"],
            task_ids=result["task_ids"],
            page_id=page_id,
        ),
    )


@router.get("/status", response_model=DataResponse[SchedulerStatusResponse])
async def get_scheduler_status():
    """
    获取调度器状态和任务信息

    Returns:
        DataResponse: 调度器状态和任务统计信息
    """
    scheduler = get_scheduler()

    # 获取调度器状态
    status = scheduler.get_status()

    # 获取任务列表
    jobs = scheduler.get_jobs()

    # 统计任务信息
    job_details = []
    for job in jobs:
        job_info = {
            "job_id": job.id,
            "name": job.name,
            "next_run_time": (
                job.next_run_time.isoformat() if job.next_run_time else None
            ),
            "trigger": str(job.trigger),
            "args": job.args,
            "kwargs": job.kwargs,
        }
        job_details.append(job_info)

    # 构建响应数据
    response_data = {
        "scheduler_status": status,
        "jobs": job_details,
        "job_count": len(jobs),
        "summary": {
            "total_jobs": status.get("job_count", 0),
            "running_jobs": status.get("running_jobs", 0),
            "paused_jobs": status.get("paused_jobs", 0),
            "scheduler_state": status.get("status", "unknown"),
            "uptime": status.get("uptime", 0),
        },
    }

    return DataResponse(
        success=True,
        message="获取调度器状态成功",
        data=SchedulerStatusResponse(
            scheduler_status=status,
            jobs=job_details,
            job_count=len(jobs),
            summary={
                "total_jobs": status.get("job_count", 0),
                "running_jobs": status.get("running_jobs", 0),
                "paused_jobs": status.get("paused_jobs", 0),
                "scheduler_state": status.get("status", "unknown"),
                "uptime": status.get("uptime", 0),
            },
        ),
    )


@router.get(
    "/batch/{batch_id}/status", response_model=DataResponse[BatchStatusResponse]
)
async def get_batch_status(batch_id: str):
    """
    获取批量任务状态

    Args:
        batch_id: 批量任务ID

    Returns:
        DataResponse: 批量任务状态信息
    """
    scheduler = get_scheduler()

    # 获取批量任务状态
    batch_status = scheduler.get_batch_status(batch_id)

    # 获取详细的任务信息
    batch_jobs = scheduler.get_batch_jobs(batch_id)
    job_details = []

    for job in batch_jobs:
        job_info = {
            "job_id": job.id,
            "page_id": job.id.split("_")[1] if "_" in job.id else "unknown",
            "next_run_time": (
                job.next_run_time.isoformat() if job.next_run_time else None
            ),
            "status": "running" if job.next_run_time else "completed",
        }
        job_details.append(job_info)

    response_data = {**batch_status, "jobs": job_details}

    return DataResponse(
        success=True,
        message=f"获取批量任务 {batch_id} 状态成功",
        data=BatchStatusResponse(
            batch_id=batch_status.get("batch_id", batch_id),
            status=batch_status.get("status", "unknown"),
            total_jobs=batch_status.get("total_jobs", 0),
            jobs=job_details,
        ),
    )
