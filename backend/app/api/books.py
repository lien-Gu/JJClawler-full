"""
书籍相关接口

提供书籍信息查询、榜单历史和趋势分析的API端点
"""
from typing import Optional
from fastapi import APIRouter, Query, Path, HTTPException

from app.modules.service import BookService
from app.modules.models import (
    BookDetail,
    BookRankingsResponse, 
    BookTrendsResponse,
    BookSearchResponse
)
from app.utils.service_utils import service_context, handle_api_error, to_api_response

router = APIRouter(prefix="/books", tags=["书籍信息"])


@router.get("/{book_id}", response_model=BookDetail)
async def get_book_detail(
    book_id: str = Path(..., description="书籍ID")
):
    """
    获取书籍详细信息
    
    返回指定书籍的完整信息，包括基本信息和最新统计数据
    """
    try:
        with service_context(BookService) as book_service:
            book_detail = book_service.get_book_detail(book_id)
            if not book_detail:
                raise HTTPException(status_code=404, detail=f"书籍 {book_id} 不存在")
            return book_detail
    except HTTPException:
        raise
    except Exception as e:
        handle_api_error(e, "获取书籍详情")


@router.get("/{book_id}/rankings", response_model=BookRankingsResponse)
async def get_book_rankings(
    book_id: str = Path(..., description="书籍ID"),
    days: int = Query(30, ge=1, le=365, description="历史天数")
):
    """
    获取书籍榜单历史
    
    返回指定书籍在各个榜单中的历史表现，
    包括当前在榜情况和历史记录
    """
    try:
        with service_context(BookService) as book_service:
            book_detail, current_rankings, history_rankings = book_service.get_book_ranking_history(book_id, days)
            
            if not book_detail:
                raise HTTPException(status_code=404, detail=f"书籍 {book_id} 不存在")
            
            return BookRankingsResponse(
                book=to_api_response(book_detail),
                current_rankings=to_api_response(current_rankings),
                history=to_api_response(history_rankings),
                total_records=len(history_rankings)
            )
    except HTTPException:
        raise
    except Exception as e:
        handle_api_error(e, "获取书籍榜单历史")


@router.get("/{book_id}/trends", response_model=BookTrendsResponse) 
async def get_book_trends(
    book_id: str = Path(..., description="书籍ID"),
    days: int = Query(30, ge=1, le=365, description="趋势天数")
):
    """
    获取书籍数据变化趋势
    
    返回指定书籍在过去N天的统计数据变化，
    包括点击量、收藏量、评论数、章节数的趋势
    """
    try:
        with service_context(BookService) as book_service:
            # 先检查书籍是否存在
            book_detail = book_service.get_book_detail(book_id)
            if not book_detail:
                raise HTTPException(status_code=404, detail=f"书籍 {book_id} 不存在")
            
            # 获取趋势数据
            trends = book_service.get_book_trend_data(book_id, days)
            
            return BookTrendsResponse(
                book_id=book_id,
                title=book_detail.title,
                days=days,
                trends=to_api_response(trends)
            )
    except HTTPException:
        raise
    except Exception as e:
        handle_api_error(e, "获取书籍趋势数据")


@router.get("", response_model=BookSearchResponse)
async def search_books(
    author: Optional[str] = Query(None, description="作者名筛选"),
    title: Optional[str] = Query(None, description="书名筛选"),
    novel_class: Optional[str] = Query(None, description="分类筛选"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    搜索书籍
    
    根据作者、书名、分类等条件搜索书籍，
    支持分页查询
    """
    try:
        with service_context(BookService) as book_service:
            books, total = book_service.search_books(
                title=title,
                author=author,
                novel_class=novel_class,
                limit=limit,
                offset=offset
            )
            
            return BookSearchResponse(
                total=total,
                books=to_api_response(books)
            )
    except Exception as e:
        handle_api_error(e, "搜索书籍")