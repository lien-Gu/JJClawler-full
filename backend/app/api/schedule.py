"""
爬虫管理API接口 - 简化的任务触发器
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi import status as http_status
from typing import Optional, List

from ..models.schedule import JobHandlerType, JobInfo, SchedulerInfo, TriggerType, JobStatus
from ..models.base import DataResponse

from ..schedule import get_scheduler
from datetime import datetime

router = APIRouter()
scheduler = get_scheduler()


@router.post("/task/create", response_model=DataResponse[JobInfo])
async def create_crawl_job(
        page_ids: List[str] = Query("jiazi", description="爬取的页面id列表"),
        run_time: datetime = Query(default=datetime.now(), description="任务运行时间"),
) -> DataResponse[JobInfo]:
    """
    创建爬取任务,爬取列表中的所有页面。

    :param page_ids:
    :param run_time: 爬取任务的时间
    :return:
    """
    job = JobInfo(
        page_ids=page_ids,
        trigger_type=TriggerType.DATE,
        trigger_time={"run_time": run_time},
        status=(JobStatus.PENDING, "尚未初始化"),
        handler=JobHandlerType.CRAWL,
        result=None
    )
    job_info = scheduler.add_job(job)
    return DataResponse(data=job_info)


@router.post("/task/{job_id}", response_model=DataResponse[JobInfo])
async def get_task_status(
        job_id: str = Query(..., description="调度任务的id"),
) -> DataResponse[JobInfo]:
    """
    获取此调度任务的信息
    :param job_id:
    :return:
    """


@router.get("/status", response_model=DataResponse[SchedulerInfo])
async def get_scheduler_status():
    """
    获取调度器状态和任务信息

    Returns:
        DataResponse: 调度器状态和任务统计信息
    """
