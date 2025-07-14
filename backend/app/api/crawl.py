"""
爬虫管理API接口 - 基于调度器的任务管理
"""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.async_connection import get_session
from ..database.service.crawl_task_service import CrawlTaskService
from ..models.base import DataResponse, ListResponse
from ..models.crawl import (
    CrawlTaskResponse,
    TaskStatus,
)
from ..schedule import get_scheduler
from ..crawl.base import CrawlConfig

router = APIRouter()


@router.post("/all", response_model=DataResponse[str])
async def crawl_all_pages(
        force: bool = Query(False, description="是否强制爬取（忽略间隔限制）"),
        session: AsyncSession = Depends(get_session)
):
    """
    触发爬取所有配置的页面 - 通过任务分解器分解为单个页面任务（重构后）
    
    Args:
        force: 是否强制爬取，忽略最小间隔限制
        session: 数据库会话
        
    Returns:
        DataResponse[str]: 批次任务ID
    """
    try:
        # 获取所有分类页面（排除夹子榜）
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        page_ids = []
        
        for task in all_tasks:
            task_id = task.get('id', '')
            if not ('jiazi' in task_id.lower() or task.get('category') == 'jiazi'):
                page_ids.append(task_id)
        
        if not page_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="没有找到可用的页面任务"
            )

        # 获取调度器
        scheduler = get_scheduler()

        # 生成批次任务ID
        batch_id = f"crawl_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建任务服务记录
        task_service = CrawlTaskService(session)
        await task_service.create_task(
            task_id=batch_id,
            task_type="all_pages",
            page_ids=page_ids,
            message=f"已分解为 {len(page_ids)} 个单页面任务"
        )

        # 为每个页面添加单独的调度任务
        success_count = 0
        for i, page_id in enumerate(page_ids):
            job_id = f"{batch_id}_page_{i}_{page_id}"
            job_data = {
                "page_id": page_id,  # 重构后：单个页面ID
                "force": force,
                "batch_id": batch_id
            }

            success = await scheduler.add_one_time_job(
                job_id=job_id,
                handler_class_name="crawl",
                job_data=job_data,
                run_date=None  # 立即执行
            )
            
            if success:
                success_count += 1

        if success_count == 0:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="所有任务都添加失败"
            )

        return DataResponse(
            success=True,
            message=f"已分解为 {len(page_ids)} 个单页面任务，成功添加 {success_count} 个，批次ID: {batch_id}",
            data=batch_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发爬取失败: {str(e)}"
        )


@router.post("/jiazi", response_model=DataResponse[str])
async def crawl_jiazi_pages(
        force: bool = Query(False, description="是否强制爬取（忽略间隔限制）"),
        session: AsyncSession = Depends(get_session)
):
    """
    触发爬取夹子榜页面 - 通过任务分解器分解为单个页面任务（重构后）
    
    Args:
        force: 是否强制爬取，忽略最小间隔限制
        session: 数据库会话
        
    Returns:
        DataResponse[str]: 批次任务ID
    """
    try:
        # 获取夹子榜页面
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        page_ids = []
        
        for task in all_tasks:
            task_id = task.get('id', '')
            if 'jiazi' in task_id.lower() or task.get('category') == 'jiazi':
                page_ids.append(task_id)
        
        if not page_ids:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="没有找到夹子榜页面任务"
            )

        # 获取调度器
        scheduler = get_scheduler()

        # 生成批次任务ID
        batch_id = f"crawl_jiazi_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建任务服务记录
        task_service = CrawlTaskService(session)
        await task_service.create_task(
            task_id=batch_id,
            task_type="jiazi_pages",
            page_ids=page_ids,
            message=f"已分解为 {len(page_ids)} 个单页面任务"
        )

        # 为每个页面添加单独的调度任务
        success_count = 0
        for i, page_id in enumerate(page_ids):
            job_id = f"{batch_id}_page_{i}_{page_id}"
            job_data = {
                "page_id": page_id,  # 重构后：单个页面ID
                "force": force,
                "batch_id": batch_id,
                "category": "jiazi"
            }

            success = await scheduler.add_one_time_job(
                job_id=job_id,
                handler_class_name="crawl",
                job_data=job_data,
                run_date=None  # 立即执行
            )
            
            if success:
                success_count += 1

        if success_count == 0:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="所有任务都添加失败"
            )

        return DataResponse(
            success=True,
            message=f"已分解为 {len(page_ids)} 个夹子榜单页面任务，成功添加 {success_count} 个，批次ID: {batch_id}",
            data=batch_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"触发夹子榜爬取失败: {str(e)}"
        )


@router.post("/page", response_model=DataResponse[str])
async def crawl_multiple_pages(
        page_ids: List[str],
        force: bool = Query(False, description="是否强制爬取（忽略间隔限制）"),
        session: AsyncSession = Depends(get_session)
):
    """
    手动触发爬取多个指定页面 - 通过任务分解器验证并分解为单个任务（重构后）
    
    Args:
        page_ids: 页面ID列表
        force: 是否强制爬取，忽略最小间隔限制
        session: 数据库会话
        
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

        # 获取调度器
        scheduler = get_scheduler()

        # 生成批次任务ID
        batch_id = f"crawl_pages_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # 创建任务服务记录
        task_service = CrawlTaskService(session)
        await task_service.create_task(
            task_id=batch_id,
            task_type="specific_pages",
            page_ids=valid_page_ids,
            message=f"已分解为 {len(valid_page_ids)} 个单页面任务"
        )

        # 为每个页面添加单独的调度任务
        success_count = 0
        for i, page_id in enumerate(valid_page_ids):
            job_id = f"{batch_id}_page_{i}_{page_id}"
            job_data = {
                "page_id": page_id,  # 重构后：单个页面ID
                "force": force,
                "batch_id": batch_id
            }

            success = await scheduler.add_one_time_job(
                job_id=job_id,
                handler_class_name="crawl",
                job_data=job_data,
                run_date=None  # 立即执行
            )
            
            if success:
                success_count += 1

        if success_count == 0:
            raise HTTPException(
                status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="所有任务都添加失败"
            )

        return DataResponse(
            success=True,
            message=f"已分解为 {len(valid_page_ids)} 个单页面任务，成功添加 {success_count} 个，批次ID: {batch_id}",
            data=batch_id
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
