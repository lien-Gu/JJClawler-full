"""
爬虫管理API接口 - 简化的任务触发器
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Query, HTTPException
from fastapi import status as http_status

from ..crawl.base import CrawlConfig
from ..models.base import DataResponse
from ..models.schedule import JobHandlerType
from ..schedule import get_scheduler

router = APIRouter()


@router.post("/all", response_model=DataResponse[str])
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
    try:
        # 获取所有页面ID
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        page_ids = []

        for task in all_tasks:
            task_id = task.get('id', '')
            page_ids.append(task_id)

        if not page_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="没有找到可用的页面任务"
            )

        # 获取调度器并添加批量任务
        scheduler = get_scheduler()
        batch_id = f"crawl_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 添加批量任务到调度器（统计逻辑在调度模块中处理）
        job_data = {
            "type": "pages",
            "page_ids": page_ids,
            "force": force,
            "batch_id": batch_id
        }

        success = await scheduler.add_one_time_job(
            job_id=batch_id,
            handler_class_name=JobHandlerType.CRAWL,
            job_data=job_data,
            run_date=None
        )

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="任务添加失败"
            )

        return DataResponse(
            success=True,
            message=f"已添加批量爬取任务，包含 {len(page_ids)} 个页面，批次ID: {batch_id}",
            data=batch_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发爬取失败: {str(e)}"
        )


@router.post("/pages", response_model=DataResponse[str])
async def crawl_specific_pages(
        page_ids: List[str],
        force: bool = Query(False, description="是否强制爬取（忽略间隔限制）")
):
    """
    手动触发爬取指定页面（简化版）
    
    Args:
        page_ids: 页面ID列表
        force: 是否强制爬取，忽略最小间隔限制
        
    Returns:
        DataResponse[str]: 批次任务ID
    """
    try:
        if not page_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="页面ID列表不能为空"
            )

        # 验证页面ID
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        available_ids = {task.get('id', '') for task in all_tasks}
        valid_page_ids = [pid for pid in page_ids if pid in available_ids]

        if not valid_page_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="没有有效的页面ID"
            )

        # 获取调度器并添加任务
        scheduler = get_scheduler()
        batch_id = f"crawl_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job_data = {
            "type": "pages",
            "page_ids": valid_page_ids,
            "force": force,
            "batch_id": batch_id
        }

        success = await scheduler.add_one_time_job(
            job_id=batch_id,
            handler_class_name="crawl",
            job_data=job_data,
            run_date=None
        )

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="任务添加失败"
            )

        return DataResponse(
            success=True,
            message=f"已添加批量爬取任务，包含 {len(valid_page_ids)} 个指定页面，批次ID: {batch_id}",
            data=batch_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发爬取失败: {str(e)}"
        )


@router.post("/page/{page_id}", response_model=DataResponse[str])
async def crawl_single_page(
        page_id: str,
        force: bool = Query(False, description="是否强制爬取（忽略间隔限制）")
):
    """
    触发爬取单个页面
    
    Args:
        page_id: 页面ID
        force: 是否强制爬取，忽略最小间隔限制
        
    Returns:
        DataResponse[str]: 任务ID
    """
    try:
        # 验证页面ID
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        available_ids = {task.get('id', '') for task in all_tasks}

        if page_id not in available_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=f"页面ID不存在: {page_id}"
            )

        # 获取调度器并添加任务
        scheduler = get_scheduler()
        job_id = f"crawl_single_{page_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        job_data = {
            "page_id": page_id,
            "force": force
        }

        success = await scheduler.add_one_time_job(
            job_id=job_id,
            handler_class_name="crawl",
            job_data=job_data,
            run_date=None
        )

        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="任务添加失败"
            )

        return DataResponse(
            success=True,
            message=f"已添加单页面爬取任务: {page_id}",
            data=job_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发爬取失败: {str(e)}"
        )


@router.get("/status")
async def get_scheduler_status():
    """
    获取调度器状态和任务信息
    
    Returns:
        DataResponse: 调度器状态和任务统计信息
    """
    try:
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
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
                "args": job.args,
                "kwargs": job.kwargs
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
                "uptime": status.get("uptime", 0)
            }
        }

        return DataResponse(
            success=True,
            message="获取调度器状态成功",
            data=response_data
        )

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取调度器状态失败: {str(e)}"
        )
