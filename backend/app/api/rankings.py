"""
榜单相关API接口
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..database.service.ranking_service import RankingService
from ..models.base import DataResponse, PaginationData
from ..models.ranking import RankingBasic, RankingDetail, RankingHistory

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


@router.get("detail/day/{ranking_id}", response_model=DataResponse[RankingDetail])
async def get_ranking_detail_by_day(
        ranking_id: int,
        target_date: date | None = Query(None, description="指定日期，默认为最新"),
        db: Session = Depends(get_db),
) -> DataResponse:
    """
    获取榜单详情

    :param ranking_id: 榜单内部ID
    :param target_date: 指定日期，精确到天
    :param db: 数据库会话对象
    :return: 榜单详情
    """
    if not target_date:
        target_date = date.today()
    ranking_detail = ranking_service.get_ranking_detail_by_day(db, ranking_id, target_date)
    if not ranking_detail:
        raise HTTPException(status_code=404, detail="榜单不存在")
    return DataResponse(
        data=ranking_detail,
        message="榜单详情获取成功"
    )


@router.get("detail/hour/{ranking_id}", response_model=DataResponse[RankingDetail])
async def get_jiazi_detail_by_hour(
        ranking_id: int,
        target_date: date | None = Query(None, description="指定日期，默认为最新"),
        hour: int | None = Query(None, ge=0, le=23, description="指定小时（0-23），24小时制，默认为最新"),
        db: Session = Depends(get_db),
) -> DataResponse[RankingDetail]:
    """
    获取榜单小时级别详情，事实上只用于夹子榜单使用
    如果指定日期，没有指定小时，就获取那天最后一次快照，和函数get_ranking_detail一样
    如果指定小时，没有指定日期，那就获取当天这个小时的快照数据

    :param ranking_id: 榜单内部ID
    :param target_date: 指定日期，如果为None则获取最新数据
    :param hour: 指定小时（0-23），如果为None则获取当天最新数据
    :param db: 数据库会话对象
    :return: 夹子榜单详情
    """

    if not target_date:
        target_date = date.today()
    if not hour:
        hour = datetime.now().hour if target_date == date.today() else 24
    ranking_detail = ranking_service.get_ranking_detail_by_hour(db, ranking_id, target_date, hour)

    if not ranking_detail:
        raise HTTPException(status_code=404, detail="夹子榜单不存在或指定时间没有数据")

    return DataResponse(
        data=ranking_detail,
        message="夹子榜单详情获取成功"
    )


@router.get(
    "/history/day/{ranking_id}", response_model=DataResponse[RankingHistory]
)
async def get_ranking_history_by_day(
        ranking_id: int,
        start_date: date = Query(..., description="开始日期"),
        end_date: date = Query(date.today(), description="结束日期"),
        db: Session = Depends(get_db),
) -> DataResponse:
    """
    获取榜单历史数据，如果start_date必须小于end_date。
    每天的快照选择当天最后一次更新的快照内容。

    :param ranking_id: 榜单ID
    :param start_date: 开始日期，不能为空
    :param end_date: 结束日期，若为空，则默认为当天
    :param db: 数据库会话对象
    :return: 榜单历史数据
    """
    # 参数验证
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期必须小于或等于结束日期")

    try:
        history_data = ranking_service.get_ranking_history_by_day(
            db, ranking_id, start_date, end_date
        )
        if not history_data:
            raise HTTPException(status_code=404, detail="榜单不存在")

        return DataResponse(
            data=history_data,
            message=f"成功获取榜单历史数据，时间范围：{start_date} 至 {end_date}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/history/hour/{ranking_id}", response_model=DataResponse[RankingHistory]
)
async def get_ranking_history_by_hour(
        ranking_id: int,
        start_time: datetime = Query(..., description="开始时间，分和秒都为0"),
        end_time: datetime = Query(None, description="结束时间，分和秒都为0。若为空，则默认为此时此刻"),
        db: Session = Depends(get_db),
) -> DataResponse:
    """
    获取小时级别榜单历史数据，如果start_time必须小于end_time
    每小时的快照选择当小时最后一次更新的快照内容。

    :param ranking_id: 榜单ID
    :param start_time: 开始时间，不能为空，这个数据的分和秒都为0
    :param end_time: 结束时间，这个数据的分和秒都为0。若为空，则默认为此时此刻
    :param db: 数据库会话对象
    :return: 榜单小时级历史数据
    """
    # 如果没有提供结束时间，使用当前时间（将分和秒设为0）
    if not end_time:
        now = datetime.now()
        end_time = now.replace(minute=0, second=0, microsecond=0)

    # 参数验证：确保分和秒都为0
    if start_time.minute != 0 or start_time.second != 0:
        raise HTTPException(status_code=400, detail="开始时间的分和秒必须为0")
    if end_time.minute != 0 or end_time.second != 0:
        raise HTTPException(status_code=400, detail="结束时间的分和秒必须为0")

    # 时间范围验证
    if start_time > end_time:
        raise HTTPException(status_code=400, detail="开始时间必须小于或等于结束时间")

    try:
        history_data = ranking_service.get_ranking_history_by_hour(
            db, ranking_id, start_time, end_time
        )
        if not history_data:
            raise HTTPException(status_code=404, detail="榜单不存在")

        return DataResponse(
            data=history_data,
            message=f"成功获取榜单小时级历史数据，时间范围：{start_time} 至 {end_time}"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
