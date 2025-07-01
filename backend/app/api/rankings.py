"""
榜单相关接口

提供榜单数据查询和历史分析的API端点
"""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, Path, HTTPException, Depends
from app.modules.service import RankingService
from app.modules.service.crawl_service import get_crawl_service
from app.modules.models import RankingConfig
from app.utils.response_utils import ApiResponse, success_response, error_response, paginated_response
from app.utils.error_codes import StatusCode

router = APIRouter(prefix="/rankings", tags=["榜单数据"])


def get_ranking_service() -> RankingService:
    """获取Ranking服务实例"""
    return RankingService()


@router.get("", response_model=ApiResponse[dict])
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
        page = offset // limit + 1
        start_idx = offset
        end_idx = offset + limit
        paged_rankings = all_rankings[start_idx:end_idx]
        
        # 转换为字典格式
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
            
            ranking_item = {
                "ranking_id": ranking_info.ranking_id,
                "name": ranking_info.name,
                "update_frequency": ranking_info.frequency.value,
                "total_books": total_books,
                "last_updated": last_updated,
                "parent_id": ranking_info.parent_id
            }
            ranking_items.append(ranking_item)
        
        return paginated_response(
            data=ranking_items,
            page=page,
            page_size=limit,
            total_count=len(all_rankings),
            message="获取榜单列表成功"
        )
        
    except Exception as e:
        error_resp = error_response(
            code=StatusCode.INTERNAL_ERROR,
            message="获取榜单列表失败"
        )
        raise HTTPException(
            status_code=500,
            detail=error_resp.model_dump()
        )
    finally:
        ranking_service.close()


@router.get("/hot", response_model=ApiResponse[dict])
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
            
            hot_ranking = {
                "ranking_id": ranking_info.ranking_id,
                "name": ranking_info.name,
                "update_frequency": ranking_info.frequency.value,
                "recent_activity": recent_activity,
                "total_books": total_books,
                "last_updated": last_updated
            }
            hot_rankings.append(hot_ranking)
        
        # 按活跃度降序排序，取前N个
        hot_rankings.sort(key=lambda x: x["recent_activity"], reverse=True)
        top_hot_rankings = hot_rankings[:limit]
        
        return success_response(
            data={
                "rankings": top_hot_rankings,
                "total": len(top_hot_rankings)
            },
            message="获取热门榜单成功"
        )
        
    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="获取热门榜单失败")
        raise HTTPException(
            status_code=500, 
            detail=error_resp.model_dump()
        )
    finally:
        ranking_service.close()


@router.get("/search", response_model=ApiResponse[dict])
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
        crawl_service = get_crawl_service()
        all_task_configs = crawl_service.get_all_task_configs()
        
        # 收集所有榜单（基于爬取任务配置）
        all_rankings = []
        for task in all_task_configs:
            all_rankings.append({
                'ranking_id': task.id,
                'name': task.name,
                'update_frequency': task.frequency,
                'interval': task.interval,
                'page_name': task.parent_id or 'root'
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
        
        return success_response(
            data={
                "rankings": paged_rankings,
                "total": total,
                "query": name,
                "has_next": end_idx < total,
                "page": offset // limit + 1,
                "limit": limit
            },
            message="搜索榜单成功"
        )
        
    except Exception as e:
        error_resp = error_response(code=StatusCode.INTERNAL_ERROR, message="搜索榜单失败")
        raise HTTPException(
            status_code=500, 
            detail=error_resp.model_dump()
        )


@router.get("/{ranking_id}/books", response_model=ApiResponse[dict])
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
                error_resp = error_response(code=StatusCode.PARAMETER_INVALID, message="日期格式错误，请使用 YYYY-MM-DD")
                raise HTTPException(
                    status_code=400, 
                    detail=error_resp.model_dump()
                )
        
        # 获取榜单书籍数据
        ranking_info, books_in_ranking, actual_snapshot_time = ranking_service.get_ranking_books(ranking_id, snapshot_time, limit, offset)
        
        if not ranking_info:
            error_resp = error_response(code=StatusCode.RANKING_NOT_FOUND, message="榜单不存在")
            raise HTTPException(
                status_code=404, 
                detail=error_resp.model_dump()
            )
        
        return success_response(
            data={
                "ranking": {
                    "ranking_id": ranking_info.ranking_id,
                    "name": ranking_info.name,
                    "update_frequency": ranking_info.frequency.value
                },
                "books": [book.model_dump() for book in books_in_ranking],
                "total": len(books_in_ranking),
                "page": offset // limit + 1,
                "limit": limit,
                "date": date,
                "actual_snapshot_time": actual_snapshot_time
            },
            message="获取榜单书籍成功"
        )
    finally:
        ranking_service.close()


@router.get("/{ranking_id}/history", response_model=ApiResponse[dict])
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
            error_resp = error_response(code=StatusCode.RANKING_NOT_FOUND, message="榜单不存在")
            raise HTTPException(
                status_code=404, 
                detail=error_resp.model_dump()
            )
        
        return success_response(
            data={
                "ranking": {
                    "ranking_id": ranking_info.ranking_id,
                    "name": ranking_info.name,
                    "update_frequency": ranking_info.frequency.value
                },
                "days": days,
                "snapshots": [summary.model_dump() for summary in summaries]
            },
            message="获取榜单历史成功"
        )
    finally:
        ranking_service.close()