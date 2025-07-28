"""
书籍相关API接口 - 简化版本
"""

from typing import cast, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.service.book_service import BookService
from ..database.service.ranking_service import RankingService
from ..models.base import DataResponse, PaginationData
from ..models.book import (
    BookDetail,
    BookRankingInfo,
    BookBasic,
    BookSnapshot,
)

router = APIRouter()

# 初始化服务
book_service = BookService()
ranking_service = RankingService()


@router.get("/", response_model=DataResponse[PaginationData])
async def get_books_list(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(get_db),
) -> DataResponse[PaginationData[BookBasic]]:
    """
    获取书籍列表（分页）
    :param page:
    :param size:
    :param db:
    :return:
    """
    book_result, total = book_service.get_books_with_pagination(db, page, size)

    return DataResponse(
        data=PaginationData(
            data_list=book_result,
            page=page,
            size=size,
            total_pages=total
        ),
        message="获取书籍列表成功"
    )


@router.get("/{novel_id}", response_model=DataResponse[BookDetail])
async def get_book_detail(novel_id: int, db: Session = Depends(get_db)) -> DataResponse[BookDetail]:
    """
    获取书籍详细信息 - 使用novel_id
    :param novel_id:
    :param db:
    :return:
    """
    book = book_service.get_book_by_novel_id(db, novel_id)

    # 通过book_id获取详细信息
    book_detail = book_service.get_book_detail_by_novel_id(db, cast(int, book.id))
    if not book_detail:
        raise HTTPException(status_code=404, detail=f"书籍详情不存在: {novel_id}")

    return DataResponse(
        data=book_detail,
        message="获取书籍详情成功"
    )


@router.get("/{novel_id}/snapshots", response_model=DataResponse[List[BookSnapshot]])
async def get_book_snapshots(
        novel_id: int,
        interval: str = Query(
            "day",
            pattern="^(hour|day|week|month)$",
            description="时间间隔: hour/day/week/month"
        ),
        count: int = Query(7, ge=1, le=365, description="时间段数量"),
        db: Session = Depends(get_db),
) -> DataResponse:
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
    book = book_service.get_book_by_novel_id(db, novel_id)

    # 调用统一的历史快照获取方法
    snapshots = book_service.get_historical_snapshots_by_novel_id(db, book.id, interval, count)

    return DataResponse(
        data=snapshots,
        message=f"获取{len(snapshots)}个{interval}间隔的历史快照成功"
    )


@router.get("/{novel_id}/rankings", response_model=DataResponse[List[BookRankingInfo]])
async def get_book_ranking_history(
        novel_id: int,
        ranking_id: int | None = Query(None, description="指定榜单ID"),
        days: int = Query(30, ge=1, le=365, description="统计天数"),
        db: Session = Depends(get_db),
) -> DataResponse:
    """
    获取书籍排名历史 - 使用novel_id

    :param novel_id: 书籍novel_id，晋江文学城的小说ID
    :param ranking_id: 指定榜单ID，可选，如果不指定则查询所有榜单
    :param days: 统计天数，查询最近多少天的排名历史
    :param db: 数据库会话对象
    :return: 书籍排名历史列表
    """
    # 检查书籍是否存在
    book = book_service.get_book_by_novel_id(db, novel_id)

    ranking_history_data = ranking_service.get_book_ranking_history_with_details(
        db, book.novel_id, ranking_id, days
    )

    # 转换为响应模型
    ranking_responses = [
        BookRankingInfo.from_snapshot(book.novel_id, ranking, snapshot)
        for ranking, snapshot in ranking_history_data
    ]

    return DataResponse(
        data=ranking_responses,
        message=f"获取{len(ranking_responses)}条排名历史成功"
    )
