"""
榜单相关接口

提供榜单数据查询和历史分析的API端点
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Query, Path, HTTPException
from app.schemas.rankings import (
    RankingBooksResponse, 
    RankingHistoryResponse,
    BookInRanking,
    RankingInfo,
    RankingSnapshot
)

router = APIRouter(prefix="/rankings", tags=["榜单数据"])


@router.get("/{ranking_id}/books", response_model=RankingBooksResponse)
async def get_ranking_books(
    ranking_id: str = Path(..., description="榜单ID"),
    date: str = Query(None, description="指定日期 YYYY-MM-DD"),
    limit: int = Query(50, ge=1, le=100, description="每页数量"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取特定榜单的书籍列表
    
    返回指定榜单在指定日期（默认最新）的书籍排名信息，
    包括排名变化对比
    """
    # 验证榜单ID
    valid_rankings = ["jiazi", "yq_gy", "yq_xy", "ca_ds", "ca_gd"]
    if ranking_id not in valid_rankings:
        raise HTTPException(status_code=404, detail=f"榜单 {ranking_id} 不存在")
    
    # Mock数据
    ranking_names = {
        "jiazi": "夹子",
        "yq_gy": "言情-古言", 
        "yq_xy": "言情-现言",
        "ca_ds": "纯爱-都市",
        "ca_gd": "纯爱-古代"
    }
    
    channels = {
        "jiazi": "favObservation",
        "yq_gy": "gywx",
        "yq_xy": "dsyq", 
        "ca_ds": "xddm",
        "ca_gd": "gddm"
    }
    
    # 生成Mock书籍数据
    mock_books = []
    for i in range(min(limit, 50)):  # 最多50本书
        if i >= offset:
            mock_books.append(BookInRanking(
                book_id=f"{ranking_id}_book_{i+1:03d}",
                title=f"测试小说{i+1}",
                author_name=f"作者{i+1}",
                author_id=f"author_{i+1:03d}",
                position=i+1,
                novel_class="原创-言情-架空历史" if "yq" in ranking_id else "原创-纯爱-近代现代",
                tags="甜文,轻松,情有独钟",
                position_change="new" if i < 5 else (f"+{i%3}" if i%2 == 0 else f"-{i%2}")
            ))
    
    snapshot_time = datetime.now()
    if date:
        try:
            snapshot_time = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 YYYY-MM-DD")
    
    return RankingBooksResponse(
        ranking=RankingInfo(
            ranking_id=ranking_id,
            name=ranking_names[ranking_id],
            channel=channels[ranking_id]
        ),
        snapshot_time=snapshot_time,
        total_books=50,
        books=mock_books
    )


@router.get("/{ranking_id}/history", response_model=RankingHistoryResponse)
async def get_ranking_history(
    ranking_id: str = Path(..., description="榜单ID"),
    days: int = Query(7, ge=1, le=30, description="历史天数")
):
    """
    获取榜单历史变化
    
    返回指定榜单在过去N天的快照数据，
    用于分析榜单变化趋势
    """
    # 验证榜单ID
    valid_rankings = ["jiazi", "yq_gy", "yq_xy", "ca_ds", "ca_gd"]
    if ranking_id not in valid_rankings:
        raise HTTPException(status_code=404, detail=f"榜单 {ranking_id} 不存在")
    
    ranking_names = {
        "jiazi": "夹子",
        "yq_gy": "言情-古言",
        "yq_xy": "言情-现言", 
        "ca_ds": "纯爱-都市",
        "ca_gd": "纯爱-古代"
    }
    
    channels = {
        "jiazi": "favObservation",
        "yq_gy": "gywx",
        "yq_xy": "dsyq",
        "ca_ds": "xddm", 
        "ca_gd": "gddm"
    }
    
    # 生成Mock历史数据
    mock_snapshots = []
    for i in range(days):
        snapshot_date = datetime.now() - timedelta(days=i)
        mock_snapshots.append(RankingSnapshot(
            snapshot_time=snapshot_date,
            total_books=50 - (i % 5),  # 模拟榜单书籍数量的小幅变化
            top_book_title=f"当日热门小说{(i+1)%10}" if i < 10 else None
        ))
    
    return RankingHistoryResponse(
        ranking=RankingInfo(
            ranking_id=ranking_id,
            name=ranking_names[ranking_id],
            channel=channels[ranking_id]
        ),
        days=days,
        snapshots=list(reversed(mock_snapshots))  # 按时间正序返回
    )