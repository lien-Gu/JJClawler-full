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
    BookSnapshotResponse,
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
    :param page:
    :param size:
    :param db:
    :return:
    """
    book_result, _ = book_service.get_books_with_pagination(db, page, size)

    return ListResponse(
        success=True,
        code=200,
        data=[BookResponse.from_book_table(book) for book in book_result],
        message="获取书籍列表成功"
    )


@router.get("/{novel_id}", response_model=DataResponse[BookDetailResponse])
async def get_book_detail(novel_id: str, db: Session = Depends(get_db)) -> DataResponse[BookDetailResponse]:
    """
    获取书籍详细信息 - 使用novel_id
    :param novel_id:
    :param db:
    :return:
    """
    # 获取书籍信息，如果不存在则抛出404异常
    book = book_service.get_book_by_novel_id(db, novel_id)

    # 通过book_id获取详细信息
    book, snapshot = book_service.get_book_detail_with_latest_snapshot(db, book.id)
    if not book or not snapshot:
        raise HTTPException(status_code=404, detail=f"书籍详情不存在: {novel_id}")

    return DataResponse(
        data=BookDetailResponse.from_book_and_snapshot(book, snapshot),
        message="获取书籍详情成功"
    )


@router.get("/{novel_id}/snapshots", response_model=ListResponse[BookSnapshotResponse])
async def get_book_snapshots(
        novel_id: str,
        interval: str = Query(
            "day",
            pattern="^(hour|day|week|month)$",
            description="时间间隔: hour/day/week/month"
        ),
        count: int = Query(7, ge=1, le=365, description="时间段数量"),
        db: Session = Depends(get_db),
) -> ListResponse[BookSnapshotResponse]:
    """
    获取书籍历史快照

    Examples:
        - interval=hour, count=7: 获取7小时内每小时的第一个快照
        - interval=day, count=7: 获取7天内每天的第一个快照
        - interval=week, count=4: 获取4周内每周的第一个快照
        - interval=month, count=3: 获取3个月内每月的第一个快照

    :param novel_id: 书籍novel_id
    :param interval: 时间间隔 (hour/day/week/month)
    :param count: 时间段数量
    :param db:
    :return: 历史快照列表
    """
    # 参数范围限制
    limits = {"hour": 168, "day": 90, "week": 52, "month": 24}
    count = min(count, limits[interval])

    # 获取书籍并验证存在性
    book = book_service.get_book_by_novel_id(db, novel_id, raise_404=True)

    # 调用统一的历史快照获取方法
    snapshots = book_service.get_historical_snapshots(db, book.id, interval, count)

    # 转换为响应模型
    snapshot_responses = [BookSnapshotResponse.from_snapshot(snapshot) for snapshot in snapshots]

    return ListResponse(
        success=True,
        code=200,
        data=snapshot_responses,
        message=f"获取{len(snapshots)}个{interval}间隔的历史快照成功"
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
    book = book_service.get_book_by_novel_id(db, novel_id, raise_404=True)

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
