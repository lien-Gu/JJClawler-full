"""
榜单相关API接口
"""

from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.service.ranking_service import RankingService
from ..models.base import DataResponse, ListResponse
from ..models.ranking import (
    BookInRanking,
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
        sub_ranking_name: str | None = Query(None, description="子榜单名称筛选"),
        name: str | None = Query(None, description="榜单名称筛选"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(get_db),
):
    """
    获取榜单列表
    
    :param page_id: 榜单页面ID筛选
    :param sub_ranking_name: 子榜单名称筛选  
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
    if sub_ranking_name:
        filters["sub_ranking_name"] = sub_ranking_name
    if name:
        filters["name"] = name

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
        limit: int = Query(50, ge=1, le=200, description="榜单书籍数量限制"),
        db: Session = Depends(get_db),
):
    """
    获取榜单详情

    Args:
        ranking_id: 榜单ID
        date: 指定日期的榜单快照
        limit: 返回的书籍数量

    Returns:
        RankingDetailResponse: 榜单详情
    """
    ranking_detail = ranking_service.get_ranking_detail(db, ranking_id, date, limit)

    if not ranking_detail:
        raise HTTPException(status_code=404, detail="榜单不存在")

    ranking = ranking_detail["ranking"]
    books_data = ranking_detail["books"]

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
        snapshot_time=ranking_detail["snapshot_time"],
        books=books_in_ranking,
        total_books=ranking_detail["total_books"],
    )

    return DataResponse(data=response_data, message="榜单详情获取成功")


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
