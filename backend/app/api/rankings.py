"""
榜单相关API接口
"""
from typing import List, Optional
from datetime import date as Date
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session

from ..models.ranking import (
    RankingResponse,
    RankingDetailResponse, 
    RankingHistoryResponse,
    RankingStatsResponse,
    RankingCompareRequest,
    RankingCompareResponse,
    BookInRanking
)
from ..models.base import DataResponse, ListResponse
from ..database.db.base import get_db
from ..database.service.ranking_service import RankingService

router = APIRouter()

# 初始化服务
ranking_service = RankingService()

@router.get("/", response_model=ListResponse[RankingResponse])
async def get_rankings(
    group_type: Optional[str] = Query(None, description="榜单分组类型筛选"),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """
    获取榜单列表
    
    Args:
        group_type: 榜单分组类型筛选
        page: 页码
        size: 每页数量
        
    Returns:
        List[RankingResponse]: 榜单列表
    """
    try:
        filters = {}
        if group_type:
            filters["rank_group_type"] = group_type
        
        result = ranking_service.get_all_rankings(db, page, size, filters)
        
        # 转换为响应模型
        ranking_responses = []
        for ranking in result["rankings"]:
            ranking_responses.append(RankingResponse(
                ranking_id=ranking.rank_id,
                name=ranking.name,
                page_id=ranking.page_id,
                url="",  # URL字段不在数据库模型中，需要从配置获取
                category=ranking.rank_group_type,
                description=None,
                is_active=True,  # 模型中没有is_active字段，默认True
                crawl_frequency=60,  # 默认值
                last_crawl_time=None,
                create_time=ranking.created_at
            ))
        
        return ListResponse(
            data=ranking_responses,
            count=result["total"],
            message="榜单列表获取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取榜单列表失败: {str(e)}")


@router.get("/{ranking_id}", response_model=DataResponse[RankingDetailResponse])
async def get_ranking_detail(
    ranking_id: int,
    date: Optional[Date] = Query(None, description="指定日期，默认为最新"),
    limit: int = Query(50, ge=1, le=200, description="榜单书籍数量限制"),
    db: Session = Depends(get_db)
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
    try:
        ranking_detail = ranking_service.get_ranking_detail(db, ranking_id, date, limit)
        
        if not ranking_detail:
            raise HTTPException(status_code=404, detail="榜单不存在")
        
        ranking = ranking_detail["ranking"]
        books_data = ranking_detail["books"]
        
        # 转换书籍数据
        books_in_ranking = []
        for book_data in books_data:
            books_in_ranking.append(BookInRanking(
                book_id=book_data["book_id"],
                title=book_data["title"],
                author=book_data["author"],
                position=book_data["position"],
                score=book_data["score"],
                clicks=None,  # 这些数据需要从book_snapshot获取
                favorites=None,
                comments=None,
                recommendations=None,
                word_count=None,
                status=None
            ))
        
        response_data = RankingDetailResponse(
            ranking_id=ranking.rank_id,
            name=ranking.name,
            page_id=ranking.page_id,
            category=ranking.rank_group_type,
            description=None,
            snapshot_time=ranking_detail["snapshot_time"],
            books=books_in_ranking,
            total_books=ranking_detail["total_books"]
        )
        
        return DataResponse(
            data=response_data,
            message="榜单详情获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取榜单详情失败: {str(e)}")


@router.get("/{ranking_id}/history", response_model=DataResponse[RankingHistoryResponse])
async def get_ranking_history(
    ranking_id: int,
    start_date: Optional[Date] = Query(None, description="开始日期"),
    end_date: Optional[Date] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
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
    try:
        history_data = ranking_service.get_ranking_history(
            db, ranking_id, start_date, end_date
        )
        
        # 转换为响应模型
        from ..models.ranking import RankingHistoryPoint
        
        history_points = []
        for trend_point in history_data["trend_data"]:
            # 简化的历史点数据，实际应该包含更多信息
            history_points.append(RankingHistoryPoint(
                date=trend_point["snapshot_time"].date(),
                book_id=0,  # 占位符，实际需要更复杂的逻辑
                title="",
                author="",
                position=0,
                score=None
            ))
        
        response_data = RankingHistoryResponse(
            ranking_id=ranking_id,
            ranking_name="榜单名称",  # 需要从数据库获取
            start_date=start_date or Date.today(),
            end_date=end_date or Date.today(),
            history_data=history_points
        )
        
        return DataResponse(
            data=response_data,
            message="榜单历史数据获取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取榜单历史失败: {str(e)}")


@router.get("/{ranking_id}/stats", response_model=DataResponse[RankingStatsResponse])
async def get_ranking_stats(
    ranking_id: int,
    db: Session = Depends(get_db)
):
    """
    获取榜单统计信息
    
    Args:
        ranking_id: 榜单ID
        
    Returns:
        RankingStatsResponse: 榜单统计信息
    """
    try:
        ranking = ranking_service.get_ranking_by_id(db, ranking_id)
        if not ranking:
            raise HTTPException(status_code=404, detail="榜单不存在")
        
        stats = ranking_service.get_ranking_statistics(db, ranking_id)
        
        response_data = RankingStatsResponse(
            ranking_id=ranking.rank_id,
            ranking_name=ranking.name,
            total_snapshots=stats.get("total_snapshots", 0),
            unique_books=stats.get("unique_books", 0),
            avg_books_per_snapshot=0.0,  # 需要计算
            most_frequent_author=None,
            most_stable_book=None,
            first_snapshot_time=stats.get("first_snapshot_time"),
            last_snapshot_time=stats.get("last_snapshot_time")
        )
        
        return DataResponse(
            data=response_data,
            message="榜单统计信息获取成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取榜单统计失败: {str(e)}")


@router.post("/compare", response_model=DataResponse[RankingCompareResponse])
async def compare_rankings(
    request: RankingCompareRequest,
    db: Session = Depends(get_db)
):
    """
    对比多个榜单
    
    Args:
        request: 榜单对比请求
        
    Returns:
        RankingCompareResponse: 榜单对比结果
    """
    try:
        if len(request.ranking_ids) < 2:
            raise HTTPException(status_code=400, detail="至少需要选择2个榜单进行对比")
        
        comparison_result = ranking_service.compare_rankings(
            db, request.ranking_ids, request.date
        )
        
        # 转换为响应模型
        ranking_details = []
        for ranking_info in comparison_result["rankings"]:
            # 获取该榜单的书籍数据
            ranking_books = comparison_result["ranking_data"].get(ranking_info["ranking_id"], [])
            books_in_ranking = []
            
            for book_data in ranking_books:
                books_in_ranking.append(BookInRanking(
                    book_id=book_data["book_id"],
                    title=book_data["title"],
                    author=book_data["author"],
                    position=book_data["position"],
                    score=book_data["score"],
                    clicks=None,
                    favorites=None,
                    comments=None,
                    recommendations=None,
                    word_count=None,
                    status=None
                ))
            
            ranking_details.append(RankingDetailResponse(
                ranking_id=ranking_info["ranking_id"],
                name=ranking_info["name"],
                page_id=ranking_info["page_id"],
                category=None,
                description=None,
                snapshot_time=None,
                books=books_in_ranking,
                total_books=len(books_in_ranking)
            ))
        
        # 转换共同书籍
        common_books = []
        for book_info in comparison_result["common_books"]:
            common_books.append(BookInRanking(
                book_id=book_info["id"],
                title=book_info["title"],
                author=book_info["author"],
                position=0,  # 共同书籍没有位置概念
                score=None,
                clicks=None,
                favorites=None,
                comments=None,
                recommendations=None,
                word_count=None,
                status=None
            ))
        
        response_data = RankingCompareResponse(
            compare_date=comparison_result["comparison_date"],
            rankings=ranking_details,
            common_books=common_books,
            unique_books_count=comparison_result["stats"]["total_unique_books"]
        )
        
        return DataResponse(
            data=response_data,
            message="榜单对比完成"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"榜单对比失败: {str(e)}")


@router.get("/trending/books", response_model=ListResponse[dict])
async def get_trending_books(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取各榜单趋势书籍
    
    分析最近一段时间内在各榜单上升最快的书籍
    
    Args:
        days: 统计最近天数
        limit: 返回数量
        
    Returns:
        List[dict]: 趋势书籍列表
    """
    try:
        from ..modules.data_service import get_trending_books
        trending_books = get_trending_books(db, days, limit)
        
        # 转换为字典格式
        result_data = []
        for trending_book in trending_books:
            book = trending_book["book"]
            latest_snapshot = trending_book["latest_snapshot"]
            
            result_data.append({
                "book_id": book.id,
                "novel_id": book.novel_id,
                "title": book.title,
                "author": book.author,
                "favorites_growth": trending_book["favorites_growth"],
                "clicks_growth": trending_book["clicks_growth"],
                "total_growth": trending_book["total_growth"],
                "current_favorites": latest_snapshot.favorites,
                "current_clicks": latest_snapshot.clicks
            })
        
        return ListResponse(
            data=result_data,
            count=len(result_data),
            message=f"最近{days}天趋势书籍获取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势书籍失败: {str(e)}")


@router.get("/active", response_model=ListResponse[RankingResponse])
async def get_active_rankings(
    db: Session = Depends(get_db)
):
    """
    获取所有启用的榜单
    
    Returns:
        List[RankingResponse]: 启用的榜单列表
    """
    try:
        # 获取所有榜单（目前模型中没有is_active字段，返回所有榜单）
        result = ranking_service.get_all_rankings(db, page=1, size=1000)
        
        # 转换为响应模型
        ranking_responses = []
        for ranking in result["rankings"]:
            ranking_responses.append(RankingResponse(
                ranking_id=ranking.rank_id,
                name=ranking.name,
                page_id=ranking.page_id,
                url="",
                category=ranking.rank_group_type,
                description=None,
                is_active=True,  # 默认都是启用的
                crawl_frequency=60,
                last_crawl_time=None,
                create_time=ranking.created_at
            ))
        
        return ListResponse(
            data=ranking_responses,
            count=len(ranking_responses),
            message="启用榜单列表获取成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取启用榜单失败: {str(e)}") 