"""
榜单相关接口

提供榜单数据查询和历史分析的API端点
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, Path, HTTPException, Depends
from app.modules.service import RankingService
from app.modules.service.page_service import get_page_service
from app.modules.models import (
    RankingBooksResponse, 
    RankingHistoryResponse, 
    RankingConfig,
    RankingSearchResponse
)

router = APIRouter(prefix="/rankings", tags=["榜单数据"])


def get_ranking_service() -> RankingService:
    """获取Ranking服务实例"""
    return RankingService()


@router.get("/search", response_model=RankingSearchResponse)
async def search_rankings(
    name: Optional[str] = Query(None, description="榜单名称搜索关键词（支持模糊匹配）"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    搜索榜单
    
    根据榜单名称进行模糊搜索，返回匹配的榜单列表
    """
    try:
        page_service = get_page_service()
        all_pages = page_service.get_all_pages()
        
        # 收集所有榜单
        all_rankings = []
        for page in all_pages:
            for ranking in page.get('rankings', []):
                all_rankings.append({
                    'ranking_id': ranking['ranking_id'],
                    'name': ranking['name'],
                    'update_frequency': ranking['update_frequency'],
                    'page_name': page['name']
                })
        
        # 如果有搜索关键词，进行模糊匹配
        if name:
            filtered_rankings = []
            for ranking in all_rankings:
                if name.lower() in ranking['name'].lower():
                    filtered_rankings.append(ranking)
            all_rankings = filtered_rankings
        
        # 计算分页
        total = len(all_rankings)
        start_idx = offset
        end_idx = offset + limit
        paged_rankings = all_rankings[start_idx:end_idx]
        
        return RankingSearchResponse(
            total=total,
            rankings=paged_rankings,
            query=name,
            has_next=end_idx < total
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索榜单失败: {str(e)}")


@router.get("/{ranking_id}/books", response_model=RankingBooksResponse)
async def get_ranking_books(
    ranking_id: str = Path(..., description="榜单ID"),
    date: str = Query(None, description="指定日期 YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    ranking_service: RankingService = Depends(get_ranking_service)
):
    """
    获取特定榜单的书籍列表
    
    返回指定榜单在指定日期（默认最新）的书籍排名信息，
    包括排名变化对比
    """
    try:
        # 解析日期参数
        snapshot_time = None
        if date:
            try:
                snapshot_time = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")
        
        # 获取榜单书籍数据
        ranking_info, books_in_ranking, actual_snapshot_time = ranking_service.get_ranking_books(ranking_id, snapshot_time, limit, offset)
        
        if not ranking_info:
            raise HTTPException(status_code=404, detail=f"榜单 {ranking_id} 不存在")
        
        return RankingBooksResponse(
            ranking=RankingConfig(
                ranking_id=ranking_info.ranking_id,
                name=ranking_info.name,
                update_frequency=ranking_info.frequency.value
            ),
            total=len(books_in_ranking),  # TODO: 获取实际总数
            page=offset // limit + 1,
            limit=limit,
            books=[book.model_dump() for book in books_in_ranking]
        )
    finally:
        ranking_service.close()


@router.get("/{ranking_id}/history", response_model=RankingHistoryResponse)
async def get_ranking_history(
    ranking_id: str = Path(..., description="榜单ID"),
    days: int = Query(7, ge=1, le=30, description="历史天数"),
    ranking_service: RankingService = Depends(get_ranking_service)
):
    """
    获取榜单历史变化
    
    返回指定榜单在过去N天的快照数据，
    用于分析榜单变化趋势
    """
    try:
        ranking_info, summaries = ranking_service.get_ranking_history_summary(ranking_id, days)
        
        if not ranking_info:
            raise HTTPException(status_code=404, detail=f"榜单 {ranking_id} 不存在")
        
        return RankingHistoryResponse(
            ranking=RankingConfig(
                ranking_id=ranking_info.ranking_id,
                name=ranking_info.name,
                update_frequency=ranking_info.frequency.value
            ),
            days=days,
            snapshots=[summary.model_dump() for summary in summaries]
        )
    finally:
        ranking_service.close()