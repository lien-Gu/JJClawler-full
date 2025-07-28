"""
榜单相关API接口
"""

from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.service.ranking_service import RankingService
from ..models.base import DataResponse
from ..models.ranking import (
    BatchInfoResponse,
    BookInRanking,
    RankingBatchListResponse,
    RankingDetailResponse,
    RankingHistoryResponse,
    RankingResponse,
)

router = APIRouter()

# 初始化服务
ranking_service = RankingService()


@router.get("/", response_model=ListResponse[RankingResponse])
async def get_rankings(
        page_id: str | None = Query(None, description="榜单页面ID筛选"),
        name: str | None = Query(None, description="榜单名称筛选"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(get_db),
):
    """
    获取榜单列表
    
    :param page_id: 榜单页面ID筛选
    :param sub_page_id: 子榜单名称筛选
    :param name: 榜单名称筛选
    :param page: 页码
    :param size: 每页数量
    :param db: 数据库会话对象
    :return: 榜单列表
    """
    # 构建筛选条件
    filters = {}
    if page_id:
        filters["page_id"] = page_id
    if name:
        filters["channel_name"] = name

    # 获取榜单数据
    result, _ = ranking_service.get_rankings_with_pagination(db, page, size, filters)

    return ListResponse(
        success=True,
        code=200,
        data=[RankingResponse.from_ranking(ranking) for ranking in result],
        message="榜单列表获取成功"
    )


@router.get("/{ranking_id}", response_model=DataResponse[RankingDetailResponse])
async def get_ranking_detail(
        ranking_id: int,
        date: Date | None = Query(None, description="指定日期，默认为最新"),
        batch_id: str | None = Query(None, description="指定批次ID，优先级高于date"),
        limit: int = Query(50, ge=1, le=200, description="榜单书籍数量限制"),
        db: Session = Depends(get_db),
):
    """
    获取榜单详情 - 支持batch_id查询确保数据一致性

    Args:
        ranking_id: 榜单ID
        date: 指定日期的榜单快照
        batch_id: 指定批次ID，如果提供则忽略date参数
        limit: 返回的书籍数量

    Returns:
        RankingDetailResponse: 榜单详情
    """
    # 优先使用batch_id查询
    if batch_id:
        snapshots = ranking_service.get_snapshots_by_batch_id(db, ranking_id, batch_id, limit)
        if not snapshots:
            raise HTTPException(status_code=404, detail=f"批次ID {batch_id} 的数据不存在")
        # 获取榜单基本信息
        ranking = ranking_service.get_ranking_by_id(db, ranking_id)
        if not ranking:
            raise HTTPException(status_code=404, detail="榜单不存在")
        
        # 使用batch_id查询到的第一个快照的时间作为快照时间
        snapshot_time = snapshots[0].snapshot_time
        books_data = [
            {
                "book_id": snapshot.book_id,
                "title": "待获取书籍信息",  # 需要关联查询书籍表
                "position": snapshot.position,
                "score": snapshot.score,
            }
            for snapshot in snapshots
        ]
    else:
        # 使用原有的方法
        ranking_detail = ranking_service.get_ranking_detail(db, ranking_id, date, limit)
        if not ranking_detail:
            raise HTTPException(status_code=404, detail="榜单不存在")
        
        ranking = ranking_detail["ranking"]
        books_data = ranking_detail["books"]
        snapshot_time = ranking_detail["snapshot_time"]
        # 获取batch_id - 从现有快照数据中获取
        if "snapshots" in ranking_detail and ranking_detail["snapshots"]:
            batch_id = ranking_detail["snapshots"][0].batch_id
        else:
            batch_id = "unknown"

    # 转换书籍数据
    books_in_ranking = []
    for book_data in books_data:
        books_in_ranking.append(
            BookInRanking(
                book_id=book_data["book_id"],
                title=book_data["title"],
                position=book_data["position"],
                score=book_data["score"],
                clicks=None,  # 这些数据需要从book_snapshot获取
                favorites=None,
                comments=None,
                word_count=None,
            )
        )

    response_data = RankingDetailResponse(
        ranking_id=str(ranking.rank_id),  # 转换为字符串
        name=ranking.name,
        page_id=ranking.page_id,
        category=ranking.rank_group_type,
        snapshot_time=snapshot_time,
        batch_id=batch_id,
        books=books_in_ranking,
        total_books=len(books_in_ranking),
    )

    return DataResponse(
        success=True,
        code=200,
        data=response_data, 
        message="榜单详情获取成功"
    )


@router.get(
    "/{ranking_id}/history", response_model=DataResponse[RankingHistoryResponse]
)
async def get_ranking_history(
        ranking_id: int,
        start_date: Date | None = Query(None, description="开始日期"),
        end_date: Date | None = Query(None, description="结束日期"),
        db: Session = Depends(get_db),
):
    """
    获取榜单历史数据

    Args:
        ranking_id: 榜单ID
        start_date: 开始日期
        end_date: 结束日期

    Returns:
        RankingHistoryResponse: 榜单历史数据
    """
    history_data = ranking_service.get_ranking_history(
        db, ranking_id, start_date, end_date
    )

    # 转换为响应模型
    from ..models.ranking import RankingHistoryPoint

    history_points = []
    for trend_point in history_data["trend_data"]:
        # 简化的历史点数据，实际应该包含更多信息
        history_points.append(
            RankingHistoryPoint(
                date=trend_point["snapshot_time"].date(),
                book_id=0,  # 占位符，实际需要更复杂的逻辑
                title="",
                position=0,
                score=None,
            )
        )

    response_data = RankingHistoryResponse(
        ranking_id=ranking_id,
        ranking_name="榜单名称",  # 需要从数据库获取
        start_date=start_date or Date.today(),
        end_date=end_date or Date.today(),
        history_data=history_points,
    )

    return DataResponse(data=response_data, message="榜单历史数据获取成功")


@router.get("/{ranking_id}/batches", response_model=DataResponse[RankingBatchListResponse])
async def get_ranking_batches(
        ranking_id: int,
        date: Date = Query(..., description="查询日期"),
        db: Session = Depends(get_db),
):
    """
    获取指定日期的可用批次列表
    
    Args:
        ranking_id: 榜单ID
        date: 查询日期
        
    Returns:
        RankingBatchListResponse: 可用批次列表
    """
    # 获取可用的batch_id列表
    batch_ids = ranking_service.get_available_batch_ids_by_date(db, ranking_id, date)
    
    if not batch_ids:
        raise HTTPException(status_code=404, detail=f"日期 {date} 没有可用的批次数据")
    
    # 为每个batch_id获取详细信息
    batch_info_list = []
    for batch_id in batch_ids:
        # 获取该批次的快照数据以统计书籍数量和时间
        snapshots = ranking_service.get_snapshots_by_batch_id(db, ranking_id, batch_id, limit=1000)
        if snapshots:
            batch_info = BatchInfoResponse(
                batch_id=batch_id,
                snapshot_time=snapshots[0].snapshot_time,
                total_books=len(snapshots)
            )
            batch_info_list.append(batch_info)
    
    response_data = RankingBatchListResponse(
        ranking_id=ranking_id,
        target_date=date,
        available_batches=batch_info_list
    )
    
    return DataResponse(
        success=True,
        code=200,
        data=response_data,
        message=f"获取到 {len(batch_info_list)} 个可用批次"
    )
