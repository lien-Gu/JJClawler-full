"""
爬虫管理API接口 - 简化的任务触发器
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, Query

from ..models.base import DataResponse
from ..models.schedule import JobHandlerType, JobInfo, JobStatus, SchedulerInfo, TriggerType
from ..schedule import get_scheduler

router = APIRouter()
scheduler = get_scheduler()


@router.post("/task/create", response_model=DataResponse[JobInfo])
async def create_crawl_job(
        page_ids: List[str] = Query(["jiazi"], description="爬取的页面id列表"),
        run_time: datetime = Query(default_factory=datetime.now, description="任务运行时间"),
) -> DataResponse[JobInfo]:
    """
    创建爬取任务,爬取列表中的所有页面。

    :param page_ids: 要爬取的页面ID列表
    :param run_time: 爬取任务的时间
    :return: 包含任务信息的响应
    """
    try:
        # 创建任务信息
        job = JobInfo(
            job_id="",  # 由调度器生成
            trigger_type=TriggerType.DATE,
            trigger_time={"run_time": run_time},
            handler=JobHandlerType.CRAWL,
            page_ids=page_ids,
            status=(JobStatus.PENDING, "任务创建中"),
            desc=f"手动创建的爬取任务 - 页面: {', '.join(page_ids)}"
        )
        
        # 添加任务到调度器
        job_info = await scheduler.add_job(job)
        
        return DataResponse(
            success=True,
            message="任务创建成功",
            data=job_info
        )
        
    except Exception as e:
        return DataResponse(
            success=False,
            message=f"任务创建失败: {str(e)}",
            data=None
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
        job_info = await scheduler.get_job_info(job_id)
        
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
        # 从调度器获取状态信息
        scheduler_info_dict = await scheduler.get_scheduler_info()
        
        # 转换为Pydantic模型
        scheduler_info = SchedulerInfo(
            status=scheduler_info_dict["status"],
            job_wait=scheduler_info_dict["job_wait"],
            job_running=scheduler_info_dict["job_running"],
            run_time=scheduler_info_dict["run_time"]
        )
        
        return DataResponse(
            success=True,
            message="获取调度器状态成功",
            data=scheduler_info
        )
        
    except Exception as e:
        return DataResponse(
            success=False,
            message=f"获取调度器状态失败: {str(e)}",
            data=None
        )
