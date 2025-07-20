"""
书籍相关API接口
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.service.book_service import BookService
from ..database.service.ranking_service import RankingService
from ..models.base import DataResponse, ListResponse
from ..models.book import (
    BookDetailResponse,
    BookRankingHistoryResponse,
    BookResponse,
    BookTrendAggregatedPoint,
    BookTrendPoint,
)

router = APIRouter()

# 初始化服务
book_service = BookService()
ranking_service = RankingService()


@router.get("/", response_model=ListResponse[BookResponse])
async def get_books_list(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(get_db),
) -> ListResponse[BookResponse]:
    """
    获取书籍列表（分页）
    """
    book_result, _ = book_service.get_books_with_pagination(db, page, size)

    return ListResponse(
        data=[BookResponse.from_book_table(book) for book in book_result],
        message="获取书籍列表成功"
    )


@router.get("/search", response_model=ListResponse[BookResponse])
async def search_books(
        keyword: str = Query(..., min_length=1, description="搜索关键词"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(get_db),
) -> ListResponse[BookResponse]:
    """
    搜索书籍

    支持按标题、作者搜索
    """
    books = book_service.search_books(db, keyword, page, size)

    return ListResponse(
        data=[BookResponse.from_book_table(book) for book in books],
        message="搜索成功"
    )


@router.get("/{book_id}", response_model=DataResponse[BookDetailResponse])
async def get_book_detail(book_id: int, db: Session = Depends(get_db)):
    """
    获取书籍详细信息

    Args:
        book_id: 书籍ID

    Returns:
        BookDetailResponse: 书籍详细信息
    """
    book_detail = book_service.get_book_detail_with_latest_snapshot(db, book_id)

    if not book_detail:
        raise HTTPException(status_code=404, detail="书籍不存在")

    book = book_detail["book"]
    latest_snapshot = book_detail["latest_snapshot"]

    # 构造响应数据
    response_data = BookDetailResponse.from_book_and_snapshot(book, latest_snapshot)

    return DataResponse(data=response_data, message="获取书籍详情成功")


@router.get("/{book_id}/trend", response_model=ListResponse[BookTrendPoint])
async def get_book_trend(
        book_id: int,
        duration: str = Query(
            "day",
            pattern="^(day|week|month|half-year)$",
            description="时间范围：day(24小时内每小时)/week(一周内每小时)/month(一月内每天1点)/half-year(半年内每天1点)",
        ),
        db: Session = Depends(get_db),
):
    """
    获取书籍数据趋势（根据duration智能选择快照）

    Args:
        book_id: 书籍ID
        duration: 时间范围
            - day: 返回24小时内每个小时的快照
            - week: 返回一周内每个小时的快照
            - month: 返回一个月内每天1点的快照（或最接近1点的快照）
            - half-year: 返回半年内每天1点的快照（或最接近1点的快照）

    Returns:
        BookTrendResponse: 书籍趋势数据
    """
    # 检查书籍是否存在
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 获取趋势数据
    trend_data = book_service.get_book_trend(db, book_id, duration)

    # 转换为响应模型
    trend_points = [
        BookTrendPoint.from_snapshot(snapshot) for snapshot in trend_data
    ]

    duration_desc = {
        "day": "24小时内每小时",
        "week": "一周内每小时",
        "month": "一个月内每天1点",
        "half-year": "半年内每天1点",
    }

    return ListResponse(
        data=trend_points,
        count=len(trend_points),
        message=f"获取{duration_desc[duration]}趋势数据成功",
    )


@router.get(
    "/{book_id}/trend/hourly", response_model=ListResponse[BookTrendAggregatedPoint]
)
async def get_book_trend_hourly(
        book_id: int,
        hours: int = Query(24, ge=1, le=168, description="统计小时数，最多1周"),
        db: Session = Depends(get_db),
):
    """
    按小时获取书籍聚合趋势数据

    Args:
        book_id: 书籍ID
        hours: 统计小时数

    Returns:
        按小时聚合的趋势数据
    """
    # 检查书籍是否存在
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 获取小时级趋势数据
    trend_data = book_service.get_book_trend_hourly(db, book_id, hours)

    # 转换为响应模型
    trend_points = _convert_to_aggregated_points(trend_data)

    return ListResponse(
        data=trend_points,
        count=len(trend_points),
        message=f"获取{hours}小时的趋势数据成功",
    )


@router.get(
    "/{book_id}/trend/daily", response_model=ListResponse[BookTrendAggregatedPoint]
)
async def get_book_trend_daily(
        book_id: int,
        days: int = Query(7, ge=1, le=90, description="统计天数，最多90天"),
        db: Session = Depends(get_db),
):
    """
    按天获取书籍聚合趋势数据

    Args:
        book_id: 书籍ID
        days: 统计天数

    Returns:
        按天聚合的趋势数据
    """
    # 检查书籍是否存在
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 获取日级趋势数据
    trend_data = book_service.get_book_trend_daily(db, book_id, days)

    # 转换为响应模型
    trend_points = _convert_to_aggregated_points(trend_data)

    return ListResponse(
        data=trend_points,
        count=len(trend_points),
        message=f"获取{days}天的趋势数据成功",
    )


@router.get(
    "/{book_id}/trend/weekly", response_model=ListResponse[BookTrendAggregatedPoint]
)
async def get_book_trend_weekly(
        book_id: int,
        weeks: int = Query(4, ge=1, le=52, description="统计周数，最多52周"),
        db: Session = Depends(get_db),
):
    """
    按周获取书籍聚合趋势数据

    Args:
        book_id: 书籍ID
        weeks: 统计周数

    Returns:
        按周聚合的趋势数据
    """
    # 检查书籍是否存在
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 获取周级趋势数据
    trend_data = book_service.get_book_trend_weekly(db, book_id, weeks)

    # 转换为响应模型
    trend_points = _convert_to_aggregated_points(trend_data)

    return ListResponse(
        data=trend_points,
        count=len(trend_points),
        message=f"获取{weeks}周的趋势数据成功",
    )


@router.get(
    "/{book_id}/trend/monthly", response_model=ListResponse[BookTrendAggregatedPoint]
)
async def get_book_trend_monthly(
        book_id: int,
        months: int = Query(3, ge=1, le=24, description="统计月数，最多24个月"),
        db: Session = Depends(get_db),
):
    """
    按月获取书籍聚合趋势数据

    Args:
        book_id: 书籍ID
        months: 统计月数

    Returns:
        按月聚合的趋势数据
    """
    # 检查书籍是否存在
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 获取月级趋势数据
    trend_data = book_service.get_book_trend_monthly(db, book_id, months)

    # 转换为响应模型
    trend_points = _convert_to_aggregated_points(trend_data)

    return ListResponse(
        data=trend_points,
        count=len(trend_points),
        message=f"获取{months}个月的趋势数据成功",
    )


@router.get(
    "/{book_id}/trend/aggregated", response_model=ListResponse[BookTrendAggregatedPoint]
)
async def get_book_trend_aggregated(
        book_id: int,
        period_count: int = Query(7, ge=1, le=365, description="统计周期数"),
        interval: str = Query(
            "day",
            pattern="^(hour|day|week|month)$",
            description="时间间隔：hour/day/week/month",
        ),
        db: Session = Depends(get_db),
):
    """
    按指定时间间隔获取书籍聚合趋势数据（通用接口）

    Args:
        book_id: 书籍ID
        period_count: 统计周期数（对应interval的数量）
        interval: 时间间隔
            - hour: 按小时聚合
            - day: 按天聚合
            - week: 按周聚合
            - month: 按月聚合

    Returns:
        聚合后的趋势数据，包含平均值、最大值、最小值等统计信息
    """
    # 检查书籍是否存在
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 获取聚合趋势数据
    trend_data = book_service.get_book_trend_with_interval(
        db, book_id, period_count, interval
    )

    # 转换为响应模型
    trend_points = _convert_to_aggregated_points(trend_data)

    interval_desc = {"hour": "小时", "day": "天", "week": "周", "month": "月"}

    return ListResponse(
        data=trend_points,
        count=len(trend_points),
        message=f"获取{period_count}个{interval_desc[interval]}的聚合趋势数据成功",
    )


def _convert_to_aggregated_points(
        trend_data: list[dict[str, Any]]
) -> list[BookTrendAggregatedPoint]:
    """
    将趋势数据转换为响应模型

    Args:
        trend_data: 原始趋势数据

    Returns:
        List[BookTrendAggregatedPoint]: 响应模型列表
    """
    trend_points = []
    for data_point in trend_data:
        trend_points.append(
            BookTrendAggregatedPoint(
                time_period=data_point["time_period"],
                avg_favorites=data_point["avg_favorites"],
                avg_clicks=data_point["avg_clicks"],
                avg_comments=data_point["avg_comments"],
                max_favorites=data_point["max_favorites"],
                max_clicks=data_point["max_clicks"],
                min_favorites=data_point["min_favorites"],
                min_clicks=data_point["min_clicks"],
                snapshot_count=data_point["snapshot_count"],
                period_start=data_point["period_start"],
                period_end=data_point["period_end"],
            )
        )
    return trend_points


@router.get(
    "/{book_id}/rankings", response_model=DataResponse[BookRankingHistoryResponse]
)
async def get_book_ranking_history(
        book_id: int,
        ranking_id: int | None = Query(None, description="指定榜单ID"),
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: Session = Depends(get_db),
):
    """
    获取书籍排名历史

    Args:
        book_id: 书籍ID
        ranking_id: 指定榜单ID，不指定则获取所有榜单
        days: 统计天数

    Returns:
        BookRankingHistoryResponse: 书籍排名历史
    """
    # 检查书籍是否存在
    book = book_service.get_book_by_id(db, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="书籍不存在")

    # 获取排名历史
    ranking_history = ranking_service.get_book_ranking_history(
        db, book_id, ranking_id, days
    )

    # 转换为响应模型
    from ..models.book import BookRankingInfo

    ranking_infos = [
        BookRankingInfo.from_history_dict(book_id, history)
        for history in ranking_history
    ]

    response_data = BookRankingHistoryResponse(
        book_id=book_id, ranking_history=ranking_infos
    )

    return DataResponse(data=response_data, message="获取排名历史成功")
