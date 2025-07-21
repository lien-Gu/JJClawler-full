"""
书籍相关API接口 - 简化版本
"""

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
    BookTrendPoint,
)

router = APIRouter()

# 初始化服务
book_service = BookService()
ranking_service = RankingService()


def _get_book_or_404(db: Session, novel_id: str):
    """获取书籍或抛出404异常 - 使用novel_id"""
    # 先通过novel_id获取book_id，再获取书籍
    book = book_service.get_book_by_novel_id(db, novel_id) if hasattr(book_service, 'get_book_by_novel_id') else None
    if not book:
        # 如果没有novel_id方法，尝试通过搜索获取
        books = book_service.search_books(db, novel_id, 1, 1)
        if not books:
            raise HTTPException(status_code=404, detail=f"书籍不存在: {novel_id}")
        book = books[0]
    return book


@router.get("/", response_model=ListResponse[BookResponse])
async def get_books_list(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(get_db),
) -> ListResponse[BookResponse]:
    """获取书籍列表（分页）"""
    book_result, _ = book_service.get_books_with_pagination(db, page, size)

    return ListResponse(
        success=True,
        code=200,
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
    """搜索书籍 - 支持按标题、作者搜索"""
    books = book_service.search_books(db, keyword, page, size)

    return ListResponse(
        success=True,
        code=200,
        data=[BookResponse.from_book_table(book) for book in books],
        message="搜索成功"
    )


@router.get("/{novel_id}", response_model=DataResponse[BookDetailResponse])
async def get_book_detail(novel_id: str, db: Session = Depends(get_db)):
    """获取书籍详细信息 - 使用novel_id"""
    # 先获取书籍信息
    book = _get_book_or_404(db, novel_id)
    
    # 通过book_id获取详细信息
    book_detail = book_service.get_book_detail_with_latest_snapshot(db, book.id)
    if not book_detail:
        raise HTTPException(status_code=404, detail=f"书籍详情不存在: {novel_id}")

    book_info = book_detail["book"]
    latest_snapshot = book_detail["latest_snapshot"]

    response_data = BookDetailResponse.from_book_and_snapshot(book_info, latest_snapshot)

    return DataResponse(
        success=True,
        code=200,
        data=response_data,
        message="获取书籍详情成功"
    )


@router.get("/{novel_id}/trend", response_model=ListResponse[BookTrendPoint])
async def get_book_trend(
        novel_id: str,
        interval: str = Query(
            "day",
            pattern="^(hour|day|week|month)$", 
            description="时间间隔: hour/day/week/month"
        ),
        count: int = Query(24, ge=1, le=365, description="统计数量"),
        db: Session = Depends(get_db),
):
    """
    获取书籍趋势数据 - 统一接口
    
    Args:
        novel_id: 书籍novel_id
        interval: 时间间隔 (hour/day/week/month)
        count: 统计数量
            - hour: 最多168（一周的小时数）
            - day: 最多90天
            - week: 最多52周  
            - month: 最多24个月
    
    Returns:
        趋势数据点列表
    """
    # 检查书籍是否存在，获取book对象
    book = _get_book_or_404(db, novel_id)

    # 根据间隔类型调用不同的服务方法（使用book.id）
    if interval == "hour":
        # 限制最多一周
        count = min(count, 168)
        trend_data = book_service.get_book_trend_hourly(db, book.id, count)
        desc = f"{count}小时"
    elif interval == "day":  
        # 限制最多90天
        count = min(count, 90)
        trend_data = book_service.get_book_trend_daily(db, book.id, count)
        desc = f"{count}天"
    elif interval == "week":
        # 限制最多52周
        count = min(count, 52)
        trend_data = book_service.get_book_trend_weekly(db, book.id, count)
        desc = f"{count}周"
    elif interval == "month":
        # 限制最多24个月
        count = min(count, 24)
        trend_data = book_service.get_book_trend_monthly(db, book.id, count)
        desc = f"{count}个月"
    else:
        raise HTTPException(status_code=400, detail="不支持的时间间隔")

    # 转换为响应模型 - 处理可能的字典格式数据
    trend_points = []
    for snapshot in trend_data:
        if isinstance(snapshot, dict):
            # 如果是字典格式，直接创建BookTrendPoint
            trend_points.append(BookTrendPoint(
                snapshot_time=snapshot.get('snapshot_time'),
                clicks=snapshot.get('total_clicks', 0),
                favorites=snapshot.get('total_favorites', 0), 
                comments=snapshot.get('comment_count', 0),
            ))
        else:
            # 如果是模型对象，使用from_snapshot方法
            trend_points.append(BookTrendPoint.from_snapshot(snapshot))

    return ListResponse(
        success=True,
        code=200,
        data=trend_points,
        message=f"获取{desc}趋势数据成功"
    )


@router.get("/{novel_id}/rankings", response_model=DataResponse[BookRankingHistoryResponse])
async def get_book_ranking_history(
        novel_id: str,
        ranking_id: int | None = Query(None, description="指定榜单ID"),
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: Session = Depends(get_db),
):
    """获取书籍排名历史 - 使用novel_id"""
    # 检查书籍是否存在
    book = _get_book_or_404(db, novel_id)
    
    # 获取排名历史（使用book.id）
    ranking_history = ranking_service.get_book_ranking_history(
        db, book.id, ranking_id, days
    )

    # 转换为响应模型
    from ..models.book import BookRankingInfo

    ranking_infos = [
        BookRankingInfo.from_history_dict(book.id, history)
        for history in ranking_history
    ]

    response_data = BookRankingHistoryResponse(
        book_id=book.id, ranking_history=ranking_infos
    )

    return DataResponse(
        success=True,
        code=200,
        data=response_data,
        message="获取排名历史成功"
    )