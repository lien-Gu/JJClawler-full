"""
书籍相关API接口
"""
from typing import List, Optional
from datetime import date as Date, datetime, timedelta
from fastapi import APIRouter, Query, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from ..models.book import (
    BookResponse, 
    BookDetailResponse, 
    BookTrendPoint,
    BookRankingHistoryResponse
)
from ..models.base import DataResponse, ListResponse
from ..database.base import get_db
from ..modules.service.book_service import BookService
from ..modules.service.ranking_service import RankingService

router = APIRouter()

# 初始化服务
book_service = BookService()
ranking_service = RankingService()



@router.get("/search", response_model=ListResponse[BookResponse])
async def search_books(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    搜索书籍
    
    支持按标题、作者搜索
    """
    try:
        books = book_service.search_books(db, keyword, page, size)
        
        # 转换为响应模型
        book_responses = []
        for book in books:
            book_responses.append(BookResponse(
                id=book.id,
                novel_id=book.novel_id,
                title=book.title
            ))
        
        return ListResponse(
            data=book_responses,
            count=len(book_responses),
            message="搜索成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.get("/{book_id}", response_model=DataResponse[BookDetailResponse])
async def get_book_detail(
    book_id: int,
    db: Session = Depends(get_db)
):
    """
    获取书籍详细信息
    
    Args:
        book_id: 书籍ID
        
    Returns:
        BookDetailResponse: 书籍详细信息
    """
    try:
        book_detail = book_service.get_book_detail_with_latest_snapshot(db, book_id)
        
        if not book_detail:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        book = book_detail["book"]
        latest_snapshot = book_detail["latest_snapshot"]
        
        # 构造响应数据
        response_data = BookDetailResponse(
            id=book.id,
            novel_id=book.novel_id,
            title=book.title,
            snapshot_time=latest_snapshot.snapshot_time if latest_snapshot else datetime.now(),
            clicks=latest_snapshot.clicks if latest_snapshot else None,
            favorites=latest_snapshot.favorites if latest_snapshot else None,
            comments=latest_snapshot.comments if latest_snapshot else None,
            recommendations=latest_snapshot.recommendations if latest_snapshot else None
        )
        
        return DataResponse(
            data=response_data,
            message="获取书籍详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取书籍详情失败: {str(e)}")


@router.get("/{book_id}/trend", response_model=ListResponse[BookTrendPoint])
async def get_book_trend(
    book_id: int,
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取书籍数据趋势
    
    Args:
        book_id: 书籍ID
        days: 统计天数
        
    Returns:
        BookTrendResponse: 书籍趋势数据
    """
    try:
        # 检查书籍是否存在
        book = book_service.get_book_by_id(db, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="书籍不存在")
        
        # 获取趋势数据
        trend_data = book_service.get_book_trend(db, book_id, days)
        
        # 转换为响应模型
        trend_points = []
        for snapshot in trend_data:
            trend_points.append(BookTrendPoint(
                snapshot_time=snapshot.snapshot_time,
                clicks=snapshot.clicks,
                favorites=snapshot.favorites,
                comments=snapshot.comments,
                recommendations=snapshot.recommendations
            ))
        
        return ListResponse(
            data=trend_points,
            count=len(trend_points),
            message=f"获取{days}天趋势数据成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势数据失败: {str(e)}")


@router.get("/{book_id}/rankings", response_model=DataResponse[BookRankingHistoryResponse])
async def get_book_ranking_history(
    book_id: int,
    ranking_id: Optional[int] = Query(None, description="指定榜单ID"),
    days: int = Query(30, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
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
    try:
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
        
        ranking_infos = []
        for history in ranking_history:
            ranking_infos.append(BookRankingInfo(
                book_id=book_id,
                ranking_id=history["ranking_id"],
                ranking_name=history["ranking_name"],
                position=history["position"],
                snapshot_time=history["snapshot_time"]
            ))
        
        response_data = BookRankingHistoryResponse(
            book_id=book_id,
            ranking_history=ranking_infos
        )
        
        return DataResponse(
            data=response_data,
            message="获取排名历史成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取排名历史失败: {str(e)}")


