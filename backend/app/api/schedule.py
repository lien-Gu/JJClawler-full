"""
爬虫管理API接口 - 简化的任务触发器
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Query

from ..models.base import DataResponse
from ..models.schedule import JobHandlerType, JobInfo, JobStatus, SchedulerInfo, TriggerType
from ..schedule import get_scheduler
from app.utils import generate_job_id
router = APIRouter()
scheduler = get_scheduler()


@router.post("/task/create", response_model=DataResponse[JobInfo])
async def create_crawl_job(
        page_ids: List[str] = Query(["jiazi"], description="爬取的页面id列表"),
        run_time: datetime = Query(None, description="任务运行时间"),
) -> DataResponse[JobInfo]:
    """
    创建爬取任务,爬取列表中的所有页面。
    每个页面ID对应一个独立的调度任务。

    :param page_ids: 要爬取的页面ID列表
    :param run_time: 爬取任务的时间
    :return: 包含所有创建的任务信息的响应
    """
    try:
        run_time = run_time if run_time else datetime.now()
        job_info = JobInfo(
            job_id=generate_job_id(JobHandlerType.CRAWL, run_time),
            trigger_type=JobHandlerType.CRAWL,
            trigger_time=run_time,
            handler=JobHandlerType.CRAWL,
            page_ids=page_ids,
            result=None
        )
        job_info.get_page_ids()
        job_info_with_result = await scheduler.add_crawl_job(job_info)

        return DataResponse(
            success=True,
            message=f"成功创建爬取任务",
            data=job_info_with_result
        )

    except Exception as e:
        return DataResponse(
            success=False,
            message=f"任务创建失败: {str(e)}",
            data=[]
        )


@router.get("/task/{job_id}", response_model=DataResponse[JobInfo])
async def get_task_status(
        job_id: str,
) -> DataResponse[JobInfo]:
    """
    获取指定调度任务的详细信息
    
    :param job_id: 调度任务的ID
    :return: 包含任务详细信息的响应
    """
    try:
        # 从调度器获取任务信息
        job_info = scheduler.get_job_info(job_id)

        if job_info is None:
            return DataResponse(
                success=False,
                message=f"未找到任务: {job_id}",
                data=None
            )

        return DataResponse(
            success=True,
            message="获取任务状态成功",
            data=job_info
        )

    except Exception as e:
        return DataResponse(
            success=False,
            message=f"获取任务状态失败: {str(e)}",
            data=None
        )


@router.get("/status", response_model=DataResponse[SchedulerInfo])
async def get_scheduler_status():
    """
    获取调度器状态和任务信息

    Returns:
        DataResponse: 调度器状态和任务统计信息
    """
    try:
        scheduler_info = scheduler.get_scheduler_info()
        return DataResponse(message="获取调度器状态成功", data=scheduler_info)
    except Exception as e:
        return DataResponse(success=False, message=f"获取调度器状态失败: {str(e)}", data=None)
