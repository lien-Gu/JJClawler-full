"""
书籍相关接口

提供书籍信息查询、榜单历史和趋势分析的API端点
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Query, Path, HTTPException
from app.schemas.books import (
    BookDetail,
    BookRankingsResponse, 
    BookTrendsResponse,
    BooksSearchResponse,
    BookRankingHistory,
    BookTrendData
)

router = APIRouter(prefix="/books", tags=["书籍信息"])


@router.get("/{book_id}", response_model=BookDetail)
async def get_book_detail(
    book_id: str = Path(..., description="书籍ID")
):
    """
    获取书籍详细信息
    
    返回指定书籍的完整信息，包括基本信息和最新统计数据
    """
    # Mock数据
    mock_book = BookDetail(
        book_id=book_id,
        title=f"测试小说_{book_id}",
        author_id=f"author_{book_id[:3]}",
        author_name=f"测试作者_{book_id[:3]}",
        novel_class="原创-言情-架空历史-仙侠-女主",
        tags="情有独钟,天作之合,仙侠修真,甜文,轻松",
        first_seen=datetime.now() - timedelta(days=30),
        last_updated=datetime.now() - timedelta(hours=2),
        latest_clicks=125000,
        latest_favorites=8500,
        latest_comments=2300,
        latest_chapters=85
    )
    
    return mock_book


@router.get("/{book_id}/rankings", response_model=BookRankingsResponse)
async def get_book_rankings(
    book_id: str = Path(..., description="书籍ID"),
    days: int = Query(30, ge=1, le=365, description="历史天数"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取书籍榜单历史
    
    返回指定书籍在各个榜单中的历史表现，
    包括当前在榜情况和历史记录
    """
    # Mock书籍基本信息
    mock_book = BookDetail(
        book_id=book_id,
        title=f"测试小说_{book_id}",
        author_id=f"author_{book_id[:3]}",
        author_name=f"测试作者_{book_id[:3]}",
        novel_class="原创-言情-架空历史-仙侠-女主",
        tags="情有独钟,天作之合,仙侠修真,甜文,轻松",
        first_seen=datetime.now() - timedelta(days=30),
        last_updated=datetime.now() - timedelta(hours=2),
        latest_clicks=125000,
        latest_favorites=8500,
        latest_comments=2300,
        latest_chapters=85
    )
    
    # Mock当前在榜情况
    current_rankings = [
        BookRankingHistory(
            ranking_id="jiazi",
            ranking_name="夹子",
            position=15,
            snapshot_time=datetime.now() - timedelta(hours=1)
        ),
        BookRankingHistory(
            ranking_id="yq_gy",
            ranking_name="言情-古言",
            position=8,
            snapshot_time=datetime.now() - timedelta(hours=2)
        )
    ]
    
    # Mock历史记录
    history_records = []
    for i in range(min(limit, 20)):
        if i >= offset:
            record_date = datetime.now() - timedelta(days=i+1)
            ranking_ids = ["jiazi", "yq_gy", "yq_xy"]
            ranking_names = ["夹子", "言情-古言", "言情-现言"]
            
            ranking_idx = i % len(ranking_ids)
            history_records.append(BookRankingHistory(
                ranking_id=ranking_ids[ranking_idx],
                ranking_name=ranking_names[ranking_idx],
                position=10 + (i % 15),  # 模拟排名在10-25之间变化
                snapshot_time=record_date
            ))
    
    return BookRankingsResponse(
        book=mock_book,
        current_rankings=current_rankings,
        history=history_records,
        total_records=min(days, 100)  # 模拟总记录数
    )


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
    # Mock趋势数据
    trends = []
    base_clicks = 100000
    base_favorites = 5000
    base_comments = 1500
    base_chapters = 50
    
    for i in range(days):
        trend_date = datetime.now() - timedelta(days=days-1-i)
        
        # 模拟数据增长趋势
        daily_growth = i * 50  # 每天增长
        trends.append(BookTrendData(
            date=trend_date.strftime("%Y-%m-%d"),
            total_clicks=base_clicks + daily_growth * 20,
            total_favorites=base_favorites + daily_growth,
            comment_count=base_comments + daily_growth // 2,
            chapter_count=base_chapters + i // 7  # 每周增加1章
        ))
    
    return BookTrendsResponse(
        book_id=book_id,
        title=f"测试小说_{book_id}",
        days=days,
        trends=trends
    )


@router.get("", response_model=BooksSearchResponse)
async def search_books(
    author: Optional[str] = Query(None, description="作者名筛选"),
    tags: Optional[str] = Query(None, description="标签筛选"),
    novel_class: Optional[str] = Query(None, description="分类筛选"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    搜索书籍
    
    根据作者、标签、分类等条件搜索书籍，
    支持分页查询
    """
    # Mock搜索结果
    mock_books = []
    for i in range(min(limit, 20)):
        if i >= offset:
            mock_books.append(BookDetail(
                book_id=f"search_book_{i+offset+1:03d}",
                title=f"搜索结果小说{i+offset+1}",
                author_id=f"author_{(i+offset)%10+1:03d}",
                author_name=author or f"作者{(i+offset)%10+1}",
                novel_class=novel_class or "原创-言情-架空历史",
                tags=tags or "甜文,轻松,情有独钟",
                first_seen=datetime.now() - timedelta(days=(i+offset+1)*2),
                last_updated=datetime.now() - timedelta(hours=(i+offset+1)),
                latest_clicks=50000 + (i+offset)*1000,
                latest_favorites=3000 + (i+offset)*100,
                latest_comments=800 + (i+offset)*50,
                latest_chapters=30 + (i+offset)*2
            ))
    
    return BooksSearchResponse(
        total=100,  # Mock总数
        books=mock_books
    )