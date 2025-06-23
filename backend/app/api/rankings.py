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
    RankingSearchResponse,
    RankingsListResponse,
    HotRankingsResponse,
    RankingListItem,
    HotRankingItem
)

router = APIRouter(prefix="/rankings", tags=["榜单数据"])


def get_ranking_service() -> RankingService:
    """获取Ranking服务实例"""
    return RankingService()


@router.get("", response_model=RankingsListResponse)
async def get_rankings_list(
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量"),
    ranking_service: RankingService = Depends(get_ranking_service)
):
    """
    获取榜单列表
    
    返回系统中所有榜单的基本信息，支持分页
    """
    try:
        # 获取所有榜单信息
        all_rankings = ranking_service.get_all_rankings()
        
        # 计算分页
        total = len(all_rankings)
        start_idx = offset
        end_idx = offset + limit
        paged_rankings = all_rankings[start_idx:end_idx]
        
        # 转换为RankingListItem格式
        ranking_items = []
        for ranking_info in paged_rankings:
            # 获取该榜单的书籍数量 (简化实现，实际应该从快照中统计)
            total_books = 0
            last_updated = None
            try:
                _, books, snapshot_time = ranking_service.get_ranking_books(ranking_info.ranking_id, limit=1)
                # For general list, we just estimate - in a real implementation this would come from DB stats
                total_books = len(books) * 50 if books else 0
                last_updated = snapshot_time
            except:
                pass
            
            ranking_item = RankingListItem(
                ranking_id=ranking_info.ranking_id,
                name=ranking_info.name,
                update_frequency=ranking_info.frequency.value,
                total_books=total_books,
                last_updated=last_updated,
                parent_id=ranking_info.parent_id
            )
            ranking_items.append(ranking_item)
        
        return RankingsListResponse(
            rankings=ranking_items,
            total=total,
            page=offset // limit + 1,
            limit=limit,
            has_next=end_idx < total
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取榜单列表失败: {str(e)}")
    finally:
        ranking_service.close()


@router.get("/hot", response_model=HotRankingsResponse)
async def get_hot_rankings(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    ranking_service: RankingService = Depends(get_ranking_service)
):
    """
    获取热门榜单
    
    根据最近活跃度返回热门榜单列表，
    活跃度基于最近的快照数量和更新频率计算
    """
    try:
        # 获取所有榜单信息
        all_rankings = ranking_service.get_all_rankings()
        
        # 计算每个榜单的热度并排序
        hot_rankings = []
        for ranking_info in all_rankings:
            # 获取榜单基本信息和最近活跃度
            total_books = 0
            last_updated = None
            recent_activity = 0
            
            try:
                # 获取榜单最新快照信息
                _, books, snapshot_time = ranking_service.get_ranking_books(ranking_info.ranking_id, limit=1)
                # For hot rankings, estimate total books from sample
                total_books = len(books) * 50 if books else 0
                last_updated = snapshot_time
                
                # 获取最近7天的趋势数据来计算活跃度
                trend_data = ranking_service.get_ranking_trend_data(ranking_info.ranking_id, days=7)
                recent_activity = sum(item.get("snapshot_count", 0) for item in trend_data)
                
                # 如果没有趋势数据，根据榜单类型给予基础分数
                if recent_activity == 0:
                    if ranking_info.frequency.value == "daily":
                        recent_activity = 7  # 每日榜单基础分数
                    elif ranking_info.frequency.value == "hourly":
                        recent_activity = 24  # 小时榜单基础分数
                    else:
                        recent_activity = 1
                        
            except Exception as e:
                # 如果获取失败，给予最低分数
                recent_activity = 0
            
            hot_ranking = HotRankingItem(
                ranking_id=ranking_info.ranking_id,
                name=ranking_info.name,
                update_frequency=ranking_info.frequency.value,
                recent_activity=recent_activity,
                total_books=total_books,
                last_updated=last_updated
            )
            hot_rankings.append(hot_ranking)
        
        # 按活跃度降序排序，取前N个
        hot_rankings.sort(key=lambda x: x.recent_activity, reverse=True)
        top_hot_rankings = hot_rankings[:limit]
        
        return HotRankingsResponse(
            rankings=top_hot_rankings,
            total=len(top_hot_rankings)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取热门榜单失败: {str(e)}")
    finally:
        ranking_service.close()


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