"""
爬虫管理接口

提供爬虫任务触发、状态查询和监控的API端点
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.modules.models import (
    TasksResponse,
    TaskCreateResponse,
    CrawlJiaziRequest,
    CrawlRankingRequest,
    TaskInfo
)

router = APIRouter(prefix="/crawl", tags=["爬虫管理"])


@router.post("/jiazi", response_model=TaskCreateResponse)
async def trigger_jiazi_crawl(request: CrawlJiaziRequest = CrawlJiaziRequest()):
    """
    触发夹子榜单爬取
    
    启动夹子榜单的爬取任务，夹子榜单是热度最高的榜单，
    需要频繁更新
    """
    task_id = f"jiazi_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # Mock任务创建
    return TaskCreateResponse(
        task_id=task_id,
        message="夹子榜单爬取任务已创建" + (" (强制模式)" if request.force else ""),
        status="pending"
    )


@router.post("/ranking/{ranking_id}", response_model=TaskCreateResponse)
async def trigger_ranking_crawl(
    ranking_id: str,
    request: CrawlRankingRequest = CrawlRankingRequest()
):
    """
    触发特定榜单爬取
    
    启动指定榜单的爬取任务，根据榜单配置的更新频率执行
    """
    # 验证榜单ID
    valid_rankings = ["jiazi", "yq_gy", "yq_xy", "ca_ds", "ca_gd", "ys_nocp"]
    if ranking_id not in valid_rankings:
        raise HTTPException(status_code=404, detail=f"榜单 {ranking_id} 不存在")
    
    task_id = f"{ranking_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    return TaskCreateResponse(
        task_id=task_id,
        message=f"榜单 {ranking_id} 爬取任务已创建" + (" (强制模式)" if request.force else ""),
        status="pending"
    )


@router.get("/tasks", response_model=TasksResponse)
async def get_tasks(
    status: Optional[str] = Query(None, description="状态筛选 (pending/running/completed/failed)"),
    task_type: Optional[str] = Query(None, description="类型筛选 (jiazi/ranking/book_detail)"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取爬取任务列表
    
    查询当前和历史爬取任务的状态，支持按状态和类型筛选
    """
    # Mock当前运行中的任务
    current_tasks = [
        TaskInfo(
            task_id="jiazi_20240120_143000_abc12345",
            task_type="jiazi",
            status="running",
            created_at=datetime.now() - timedelta(minutes=5),
            started_at=datetime.now() - timedelta(minutes=3),
            progress=65,
            items_crawled=32,
            ranking_id=None
        ),
        TaskInfo(
            task_id="yq_gy_20240120_140000_def67890",
            task_type="ranking", 
            status="pending",
            created_at=datetime.now() - timedelta(minutes=2),
            progress=0,
            items_crawled=0,
            ranking_id="yq_gy"
        )
    ]
    
    # Mock已完成的任务
    completed_tasks = []
    for i in range(min(limit, 10)):
        if i >= offset:
            task_time = datetime.now() - timedelta(hours=i+1)
            task_types = ["jiazi", "ranking", "book_detail"]
            task_type_choice = task_types[i % len(task_types)]
            
            completed_tasks.append(TaskInfo(
                task_id=f"{task_type_choice}_{task_time.strftime('%Y%m%d_%H%M%S')}_mock{i:03d}",
                task_type=task_type_choice,
                status="completed",
                created_at=task_time,
                started_at=task_time + timedelta(minutes=1),
                completed_at=task_time + timedelta(minutes=5),
                progress=100,
                items_crawled=50 - (i % 10),
                ranking_id=f"ranking_{i}" if task_type_choice == "ranking" else None
            ))
    
    # 根据筛选条件过滤
    if status:
        current_tasks = [t for t in current_tasks if t.status == status]
        completed_tasks = [t for t in completed_tasks if t.status == status]
    
    if task_type:
        current_tasks = [t for t in current_tasks if t.task_type == task_type]
        completed_tasks = [t for t in completed_tasks if t.task_type == task_type]
    
    return TasksResponse(
        current_tasks=current_tasks,
        completed_tasks=completed_tasks,
        total_current=len(current_tasks),
        total_completed=len(completed_tasks)
    )


@router.get("/tasks/{task_id}", response_model=TaskInfo)
async def get_task_detail(task_id: str):
    """
    获取特定任务详情
    
    查询指定任务ID的详细信息和状态
    """
    # Mock任务详情
    if "jiazi" in task_id:
        return TaskInfo(
            task_id=task_id,
            task_type="jiazi",
            status="completed",
            created_at=datetime.now() - timedelta(hours=1),
            started_at=datetime.now() - timedelta(minutes=55),
            completed_at=datetime.now() - timedelta(minutes=50),
            progress=100,
            items_crawled=50,
            ranking_id=None
        )
    elif "ranking" in task_id:
        return TaskInfo(
            task_id=task_id,
            task_type="ranking",
            status="running",
            created_at=datetime.now() - timedelta(minutes=10),
            started_at=datetime.now() - timedelta(minutes=8),
            progress=75,
            items_crawled=38,
            ranking_id="yq_gy"
        )
    else:
        raise HTTPException(status_code=404, detail=f"任务 {task_id} 不存在")