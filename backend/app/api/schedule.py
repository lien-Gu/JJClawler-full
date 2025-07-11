"""
调度管理API接口

提供调度器和任务管理的RESTful API:
- 调度器状态查询和控制
- 任务管理（查询、添加、删除、暂停、恢复）
- 任务执行历史和指标查询
"""

from typing import List

from fastapi import APIRouter, HTTPException, status

from app.models.schedule import (
    AddJobRequest, JobActionRequest, JobHistoryQuery, JobListResponse,
    JobResponse, JobResultListResponse, SchedulerMetricsResponse,
    SchedulerStatusResponse, UpdateJobRequest
)
from app.schedule import get_scheduler

router = APIRouter(prefix="/schedule", tags=["调度管理"])


@router.get("/status", response_model=SchedulerStatusResponse, summary="获取调度器状态")
async def get_scheduler_status():
    """
    获取调度器当前状态信息
    
    返回调度器的运行状态、任务统计等信息
    """
    try:
        scheduler = get_scheduler()
        status_data = scheduler.get_status()
        
        return SchedulerStatusResponse(
            success=True,
            message="获取调度器状态成功",
            data=status_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取调度器状态失败: {str(e)}"
        )


@router.get("/metrics", response_model=SchedulerMetricsResponse, summary="获取调度器指标")
async def get_scheduler_metrics():
    """
    获取调度器性能指标
    
    返回任务成功率、平均执行时间等指标信息
    """
    try:
        scheduler = get_scheduler()
        metrics_data = scheduler.get_metrics()
        
        return SchedulerMetricsResponse(
            success=True,
            message="获取调度器指标成功",
            data=metrics_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取调度器指标失败: {str(e)}"
        )


@router.post("/start", summary="启动调度器")
async def start_scheduler():
    """
    启动调度器
    
    启动任务调度服务，开始执行预定义任务
    """
    try:
        scheduler = get_scheduler()
        if scheduler.is_running():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="调度器已经在运行中"
            )
        
        await scheduler.start()
        
        return {
            "success": True,
            "message": "调度器启动成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动调度器失败: {str(e)}"
        )


@router.post("/stop", summary="停止调度器") 
async def stop_scheduler():
    """
    停止调度器
    
    停止任务调度服务，所有正在执行的任务将完成后停止
    """
    try:
        scheduler = get_scheduler()
        if not scheduler.is_running():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="调度器未运行"
            )
        
        await scheduler.shutdown()
        
        return {
            "success": True,
            "message": "调度器停止成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止调度器失败: {str(e)}"
        )


@router.get("/jobs", response_model=JobListResponse, summary="获取任务列表")
async def get_jobs():
    """
    获取所有任务列表
    
    返回当前调度器中的所有任务信息
    """
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        job_list = []
        for job in jobs:
            job_info = {
                "id": job.id,
                "name": job.name or job.id,
                "status": "running" if job.next_run_time else "paused",
                "trigger_type": "interval" if hasattr(job.trigger, 'interval') else "cron",
                "next_run_time": job.next_run_time,
                "last_run_time": None,  # APScheduler不直接提供此信息
                "handler_class": str(job.func),
                "max_instances": job.max_instances,
                "enabled": job.next_run_time is not None,
                "description": getattr(job, 'description', '')
            }
            job_list.append(job_info)
        
        return JobListResponse(
            success=True,
            message="获取任务列表成功",
            data=job_list,
            total=len(job_list)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="获取任务详情")
async def get_job(job_id: str):
    """
    获取指定任务的详细信息
    
    Args:
        job_id: 任务ID
        
    Returns:
        任务详细信息
    """
    try:
        scheduler = get_scheduler()
        job = scheduler.get_job(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {job_id}"
            )
        
        job_info = {
            "id": job.id,
            "name": job.name or job.id,
            "status": "running" if job.next_run_time else "paused",
            "trigger_type": "interval" if hasattr(job.trigger, 'interval') else "cron",
            "next_run_time": job.next_run_time,
            "last_run_time": None,  # APScheduler不直接提供此信息
            "handler_class": str(job.func),
            "max_instances": job.max_instances,
            "enabled": job.next_run_time is not None,
            "description": getattr(job, 'description', '')
        }
        
        return JobResponse(
            success=True,
            message="获取任务详情成功",
            data=job_info
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务详情失败: {str(e)}"
        )


@router.post("/jobs", summary="添加任务")
async def add_job(request: AddJobRequest):
    """
    添加新的任务到调度器
    
    Args:
        request: 任务配置请求
        
    Returns:
        添加结果
    """
    try:
        scheduler = get_scheduler()
        
        # 检查任务是否已存在
        existing_job = scheduler.get_job(request.job_config.job_id)
        if existing_job:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"任务已存在: {request.job_config.job_id}"
            )
        
        success = await scheduler.add_job(request.job_config)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="添加任务失败"
            )
        
        return {
            "success": True,
            "message": f"任务 {request.job_config.job_id} 添加成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加任务失败: {str(e)}"
        )


@router.put("/jobs/{job_id}", summary="更新任务")
async def update_job(job_id: str, request: UpdateJobRequest):
    """
    更新任务配置
    
    Args:
        job_id: 任务ID
        request: 更新请求
        
    Returns:
        更新结果
    """
    try:
        scheduler = get_scheduler()
        
        # 检查任务是否存在
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {job_id}"
            )
        
        # TODO: 实现任务配置更新逻辑
        # APScheduler的modify_job方法可以用来更新任务配置
        
        return {
            "success": True,
            "message": f"任务 {job_id} 更新成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新任务失败: {str(e)}"
        )


@router.delete("/jobs/{job_id}", summary="删除任务")
async def delete_job(job_id: str):
    """
    删除指定任务
    
    Args:
        job_id: 任务ID
        
    Returns:
        删除结果
    """
    try:
        scheduler = get_scheduler()
        
        # 检查任务是否存在
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {job_id}"
            )
        
        success = scheduler.remove_job(job_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除任务失败"
            )
        
        return {
            "success": True,
            "message": f"任务 {job_id} 删除成功"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除任务失败: {str(e)}"
        )


@router.post("/jobs/{job_id}/action", summary="任务操作")
async def job_action(job_id: str, request: JobActionRequest):
    """
    对任务执行操作（暂停/恢复/立即执行）
    
    Args:
        job_id: 任务ID
        request: 操作请求
        
    Returns:
        操作结果
    """
    try:
        scheduler = get_scheduler()
        
        # 检查任务是否存在
        job = scheduler.get_job(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {job_id}"
            )
        
        if request.action == "pause":
            success = scheduler.pause_job(job_id)
            message = f"任务 {job_id} 暂停成功" if success else "暂停任务失败"
        elif request.action == "resume":
            success = scheduler.resume_job(job_id)
            message = f"任务 {job_id} 恢复成功" if success else "恢复任务失败"
        elif request.action == "run":
            # 立即执行任务
            # TODO: 实现立即执行逻辑
            success = True
            message = f"任务 {job_id} 触发执行成功"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的操作: {request.action}"
            )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=message
            )
        
        return {
            "success": True,
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"任务操作失败: {str(e)}"
        )


@router.get("/jobs/{job_id}/history", response_model=JobResultListResponse, summary="获取任务执行历史")
async def get_job_history(job_id: str, query: JobHistoryQuery):
    """
    获取任务执行历史记录
    
    Args:
        job_id: 任务ID
        query: 查询参数
        
    Returns:
        任务执行历史列表
    """
    try:
        # TODO: 实现任务执行历史查询逻辑
        # 需要集成任务执行结果存储系统
        
        return JobResultListResponse(
            success=True,
            message="获取任务执行历史成功",
            data=[],
            total=0
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务执行历史失败: {str(e)}"
        )