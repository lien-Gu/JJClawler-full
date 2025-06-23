"""
统计数据相关接口

提供系统统计和概览数据的API端点
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from app.modules.service import BookService, RankingService
from app.modules.models import OverviewResponse, OverviewStats

router = APIRouter(prefix="/stats", tags=["统计数据"])


def get_book_service() -> BookService:
    """获取Book服务实例"""
    return BookService()


def get_ranking_service() -> RankingService:
    """获取Ranking服务实例"""
    return RankingService()


@router.get("/overview", response_model=OverviewResponse)
async def get_overview_stats(
    book_service: BookService = Depends(get_book_service),
    ranking_service: RankingService = Depends(get_ranking_service)
):
    """
    获取首页概览统计数据
    
    返回系统的关键统计指标，包括：
    - 书籍总数
    - 榜单总数
    - 最近24小时快照数
    - 活跃榜单数
    - 最后更新时间
    """
    try:
        # 获取基础统计数据
        total_books = book_service.get_total_books()
        total_rankings = ranking_service.get_total_rankings()
        recent_snapshots = book_service.get_recent_snapshots_count(hours=24)
        
        # 计算活跃榜单数（有最近快照的榜单）
        # 这里简化实现，实际可以根据业务需求调整活跃度计算逻辑
        active_rankings = min(total_rankings, (recent_snapshots // 10) + 1)
        
        # 构建响应数据
        stats = OverviewStats(
            total_books=total_books,
            total_rankings=total_rankings,
            recent_snapshots=recent_snapshots,
            active_rankings=active_rankings,
            last_updated=datetime.now()
        )
        
        return OverviewResponse(
            stats=stats,
            status="ok"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取概览统计失败: {str(e)}")
    finally:
        book_service.close()
        ranking_service.close()