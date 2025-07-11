"""
爬虫管理API接口 - 基于调度器的任务管理
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.crawl import (
    CrawlTaskResponse,
    CrawlResultItem,
    TaskStatus,
)
from ..models.base import DataResponse, ListResponse
from ..schedule import get_scheduler
from ..database.async_connection import get_session
from ..database.service.crawl_task_service import CrawlTaskService

router = APIRouter()


@router.post("/all", response_model=DataResponse[str])
async def crawl_all_pages(
        force: bool = Query(False, description="是否强制爬取（忽略间隔限制）"),
        session: AsyncSession = Depends(get_session)
):
    """
    触发爬取所有配置的页面 - 通过调度器添加任务
    
    Args:
        force: 是否强制爬取，忽略最小间隔限制
        session: 数据库会话
        
    Returns:
        DataResponse[str]: 任务ID
    """
    try:
        # 获取调度器
        scheduler = get_scheduler()
        
        # 生成任务ID
        task_id = f"crawl_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 创建任务服务记录
        task_service = CrawlTaskService(session)
        await task_service.create_task(
            task_id=task_id,
            task_type="all_pages",
            page_ids=["all"],
            message="已添加到调度器等待执行"
        )
        
        # 添加到调度器 - 一次性任务，立即执行
        job_data = {
            "type": "category",  # 爬取所有分类
            "force": force,
            "task_id": task_id
        }
        
        success = await scheduler.add_one_time_job(
            job_id=task_id,
            handler_class_name="crawl",  # 使用爬虫处理器
            job_data=job_data,
            run_date=None  # 立即执行
        )
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="添加任务到调度器失败"
            )

        return DataResponse(
            success=True,
            message=f"已将爬取任务添加到调度器，任务ID: {task_id}",
            data=task_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发爬取失败: {str(e)}"
        )


@router.post("/page", response_model=DataResponse[str])
async def crawl_multiple_pages(
        page_ids: List[str],
        force: bool = Query(False, description="是否强制爬取（忽略间隔限制）"),
        session: AsyncSession = Depends(get_session)
):
    """
    手动触发爬取多个指定页面 - 通过调度器添加任务
    
    Args:
        page_ids: 页面ID列表
        force: 是否强制爬取，忽略最小间隔限制
        session: 数据库会话
        
    Returns:
        DataResponse[str]: 任务ID
    """
    try:
        if not page_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="页面ID列表不能为空"
            )

        # 获取调度器
        scheduler = get_scheduler()
        
        # 生成任务ID
        task_id = f"crawl_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建任务服务记录
        task_service = CrawlTaskService(session)
        await task_service.create_task(
            task_id=task_id,
            task_type="specific_pages",
            page_ids=page_ids,
            message="已添加到调度器等待执行"
        )

        # 添加到调度器 - 一次性任务，立即执行
        job_data = {
            "type": "pages",  # 爬取指定页面
            "page_ids": page_ids,
            "force": force,
            "task_id": task_id
        }
        
        success = await scheduler.add_one_time_job(
            job_id=task_id,
            handler_class_name="crawl",  # 使用爬虫处理器
            job_data=job_data,
            run_date=None  # 立即执行
        )
        
        if not success:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="添加任务到调度器失败"
            )

        return DataResponse(
            success=True,
            message=f"已将 {len(page_ids)} 个页面的爬取任务添加到调度器，任务ID: {task_id}",
            data=task_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发爬取失败: {str(e)}"
        )


@router.get("/tasks", response_model=ListResponse[CrawlTaskResponse])
async def get_crawl_tasks(
        status: Optional[TaskStatus] = Query(None, description="任务状态筛选"),
        limit: int = Query(50, ge=1, le=200, description="返回数量限制"),
        session: AsyncSession = Depends(get_session)
):
    """
    获取爬虫任务列表
    
    Args:
        status: 任务状态筛选
        limit: 返回数量限制
        session: 数据库会话
        
    Returns:
        ListResponse[CrawlTaskResponse]: 任务状态列表
    """
    try:
        # 创建任务服务
        task_service = CrawlTaskService(session)

        # 获取任务列表
        tasks = await task_service.get_tasks(status=status, limit=limit)

        return ListResponse(
            success=True,
            message="获取任务列表成功",
            data=tasks,
            count=len(tasks)
        )

    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务列表失败: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=DataResponse[CrawlTaskResponse])
async def get_crawl_task_detail(
        task_id: str,
        session: AsyncSession = Depends(get_session)
):
    """
    获取特定爬虫任务的详细信息
    
    Args:
        task_id: 任务ID
        session: 数据库会话
        
    Returns:
        DataResponse[CrawlTaskResponse]: 任务详细信息
    """
    try:
        # 创建任务服务
        task_service = CrawlTaskService(session)

        # 获取任务详情
        task = await task_service.get_task_by_id(task_id)

        if not task:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {task_id}"
            )

        return DataResponse(
            success=True,
            message="获取任务详情成功",
            data=task
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取任务详情失败: {str(e)}"
        )



