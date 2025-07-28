"""
榜单相关API接口
"""

from datetime import date as Date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database.connection import get_db
from ..database.service.ranking_service import RankingService
from ..models.base import DataResponse, PaginationData
from ..models.ranking import RankingBasic, RankingDetail

router = APIRouter()

# 初始化服务
ranking_service = RankingService()


@router.get("/", response_model=DataResponse[PaginationData[RankingBasic]])
async def get_rankings(
        page_id: str | None = Query(None, description="榜单页面ID筛选"),
        name: str | None = Query(None, description="榜单名称筛选"),
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量"),
        db: Session = Depends(get_db),
) -> DataResponse:
    """
    查询榜单列表，首先根据page id查找榜单，如果page id为空或者没有查找到就使用name在Ranking
    表格中的channel name 和 sub channel name中进行模糊匹配。
    
    :param page_id: 榜单页面ID筛选
    :param name: 榜单名称筛选
    :param page: 页码
    :param size: 每页数量
    :param db: 数据库会话对象
    :return: 榜单列表
    """
    data_list = None
    total_pages = 0
    if page_id:
        data_list, total_pages = ranking_service.get_ranges_by_page_with_pagination(db, page_id, page, size)
    if not data_list and name is not None:
        data_list, total_pages = ranking_service.get_rankings_by_name_with_pagination(db, name, page, size)
    return DataResponse(
        data=PaginationData(
            data_list=data_list, page=page, size=size, total_pages=total_pages
        ),
        message="榜单列表获取成功"
    )


@router.get("/{rank_id}", response_model=DataResponse[RankingDetail])
async def get_ranking_detail(
        ranking_id: int = Query(0, description="榜单的内部ID"),
        date: Date | None = Query(None, description="指定日期，默认为最新"),
        db: Session = Depends(get_db),
)->DataResponse:
    """
    获取榜单详情

    :param ranking_id: 榜单内部ID
    :param date: 指定日期，精确到天
    :param db:
    :return: 榜单详情
    """
    # 使用原有的方法
    ranking_detail = ranking_service.get_ranking_detail(db, ranking_id, date)
    if not ranking_detail:
        raise HTTPException(status_code=404, detail="榜单不存在")
    return DataResponse(
        success=True,
        code=200,
        data=ranking_detail,
        message="榜单详情获取成功"
    )


@router.get("/jiazi", response_model=DataResponse[RankingDetail])
async def get_jiazi_detail(
        date: Date | None = Query(None, description="指定日期，默认为最新"),
        hour: int | None = Query(None, description="指定小时，24小时制，默认为最新"),
        db: Session = Depends(get_db),
) -> DataResponse[RankingDetail]:
    """
    获取夹子榜单详情，支持获取小时级别的榜单数据

    :param date:
    :param hour:
    :param db:
    :return:
    """
    pass

@router.get(
    "/{ranking_id}/history", response_model=DataResponse[RankingHistoryResponse]
)
async def get_ranking_history(
        ranking_id: int,
        start_date: Date | None = Query(None, description="开始日期"),
        end_date: Date | None = Query(None, description="结束日期"),
        db: Session = Depends(get_db),
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
    history_data = ranking_service.get_ranking_history(
        db, ranking_id, start_date, end_date
    )

    # 转换为响应模型
    from ..models.ranking import RankingHistoryPoint

    history_points = []
    for trend_point in history_data["trend_data"]:
        # 简化的历史点数据，实际应该包含更多信息
        history_points.append(
            RankingHistoryPoint(
                date=trend_point["snapshot_time"].date(),
                book_id=0,  # 占位符，实际需要更复杂的逻辑
                title="",
                position=0,
                score=None,
            )
        )

    response_data = RankingHistoryResponse(
        ranking_id=ranking_id,
        ranking_name="榜单名称",  # 需要从数据库获取
        start_date=start_date or Date.today(),
        end_date=end_date or Date.today(),
        history_data=history_points,
    )

    return DataResponse(data=response_data, message="榜单历史数据获取成功")


@router.get("/{ranking_id}/batches", response_model=DataResponse[RankingBatchListResponse])
async def get_ranking_batches(
        ranking_id: int,
        date: Date = Query(..., description="查询日期"),
        db: Session = Depends(get_db),
):
    """
    获取指定日期的可用批次列表
    
    Args:
        ranking_id: 榜单ID
        date: 查询日期
        
    Returns:
        RankingBatchListResponse: 可用批次列表
    """
    # 获取可用的batch_id列表
    batch_ids = ranking_service.get_available_batch_ids_by_date(db, ranking_id, date)

    if not batch_ids:
        raise HTTPException(status_code=404, detail=f"日期 {date} 没有可用的批次数据")

    # 为每个batch_id获取详细信息
    batch_info_list = []
    for batch_id in batch_ids:
        # 获取该批次的快照数据以统计书籍数量和时间
        snapshots = ranking_service.get_snapshots_by_batch_id(db, ranking_id, batch_id, limit=1000)
        if snapshots:
            batch_info = BatchInfoResponse(
                batch_id=batch_id,
                snapshot_time=snapshots[0].snapshot_time,
                total_books=len(snapshots)
            )
            batch_info_list.append(batch_info)

    response_data = RankingBatchListResponse(
        ranking_id=ranking_id,
        target_date=date,
        available_batches=batch_info_list
    )

    return DataResponse(
        success=True,
        code=200,
        data=response_data,
        message=f"获取到 {len(batch_info_list)} 个可用批次"
    )
