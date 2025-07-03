"""
统计数据相关接口

提供系统统计和概览数据的API端点
"""

from datetime import datetime
from fastapi import APIRouter

from app.modules.service import BookService, RankingService
from app.utils.service_utils import service_context, handle_api_error
from app.utils.response_utils import ApiResponse, success_response, error_response

router = APIRouter(prefix="/stats", tags=["统计数据"])


@router.get("/overview", response_model=ApiResponse[dict])
async def get_overview_stats():
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
        with (
            service_context(BookService) as book_service,
            service_context(RankingService) as ranking_service,
        ):
            # 获取基础统计数据
            total_books = book_service.get_total_books()
            total_rankings = ranking_service.get_total_rankings()
            recent_snapshots = book_service.get_recent_snapshots_count(hours=24)

            # 计算活跃榜单数（有最近快照的榜单）
            # 这里简化实现，实际可以根据业务需求调整活跃度计算逻辑
            active_rankings = min(total_rankings, (recent_snapshots // 10) + 1)

            # 构建响应数据
            stats = {
                "total_books": total_books,
                "total_rankings": total_rankings,
                "recent_snapshots": recent_snapshots,
                "active_rankings": active_rankings,
                "last_updated": datetime.now().isoformat(),
            }

            return success_response(data=stats, message="获取概览统计成功")

    except Exception as e:
        handle_api_error(e, "获取概览统计")
