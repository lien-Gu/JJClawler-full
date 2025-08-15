"""
爬虫管理API接口 - 简化的任务触发器
"""

from datetime import datetime
from typing import List

from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter, Query

from app.utils import generate_job_id
from ..models.base import DataResponse
from ..models.schedule import Job, JobBasic, JobType, SchedulerInfo
from ..schedule import get_scheduler

from ..logger import get_logger
logger = get_logger(__name__)
router = APIRouter()


@router.post("/task/create", response_model=DataResponse[JobBasic])
async def create_crawl_job(
        page_ids: List[str] = Query(["jiazi"], description="爬取的页面id列表"),
        run_time: datetime = Query(None, description="任务运行时间"),
) -> DataResponse[JobBasic]:
    """
    创建爬取任务,爬取列表中的所有页面。
    每个页面ID对应一个独立的调度任务。

    :param page_ids: 要爬取的页面ID列表
    :param run_time: 爬取任务的时间
    :return: 包含所有创建的任务信息的响应
    """
    try:
        run_time = run_time if run_time else datetime.now()
        
        # 调试信息
        generated_job_id = generate_job_id(JobType.CRAWL, run_time)
        logger.info(f"生成的job_id: {generated_job_id}")

        job = Job(
            job_id=generated_job_id,
            job_type=JobType.CRAWL,
            trigger=DateTrigger(run_date=run_time),
            desc=f"手动创建的爬取任务",
            page_ids=page_ids
        )
        
        logger.info(f"创建的job对象job_id: {job.job_id}")

        # 延迟获取调度器实例，确保调度器已经在lifespan中初始化
        scheduler = get_scheduler()
        created_job = await scheduler.add_schedule_job(job)
        logger.info(f"成功添加任务{created_job.job_id}，运行时间：{run_time}")

        return DataResponse(
            success=True,
            message=f"成功创建爬取任务: {created_job.job_id}",
            data=JobBasic(
                job_id=created_job.job_id,
                job_type=created_job.job_type,
                desc=created_job.desc
            )
        )

    except Exception as e:
        return DataResponse(
            success=False,
            message=f"任务创建失败: {str(e)}",
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
        # 延迟获取调度器实例，确保调度器已经在lifespan中初始化
        scheduler = get_scheduler()
        scheduler_info = scheduler.get_scheduler_info()
        logger.info(f"成功获取调度去信息：{scheduler_info.model_dump_json()}")
        return DataResponse(message="获取调度器状态成功", data=scheduler_info)
    except Exception as e:
        return DataResponse(success=False, message=f"获取调度器状态失败: {str(e)}", data=None)
