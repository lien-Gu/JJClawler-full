"""
爬虫管理API接口 - 简化的任务触发器
"""

from typing import List

from fastapi import APIRouter, Query
import random
from ..models.base import DataResponse, PaginationData
from datetime import datetime, timedelta
from ..logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=DataResponse)
async def get_books_list(
        page: int = Query(1, ge=1, description="页码"),
        size: int = Query(20, ge=1, le=100, description="每页数量")
) -> DataResponse[PaginationData]:
    """
    获取报告列表（尚未实现）
    :param page:
    :param size:
    :return:
    """
    report_result, total = [], 3
    items = random.randint(1, size)
    for idx in range(items):
        report_result.append({
            "id": size * (page - 1) + idx,
            "report_title": "report" + str(idx),
            "report_content": "who cares?"
        })

    return DataResponse(
        data=PaginationData(
            data_list=report_result,
            page=page,
            size=size,
            total_pages=total
        ),
        message="获取书籍列表成功"
    )


@router.get("/latest/{ranking_id}", response_model=DataResponse)
async def get_ranking_report(ranking_id: int) -> DataResponse:
    """
    获取榜单最新的报告
    :param ranking_id:
    :return:
    """
    ranking_report = {
        "ranking_id": ranking_id,
        "report_title": "report" + str(ranking_id),
        "report_content": "who cares?",
        "report_date": datetime.today(),
    }

    return DataResponse(
        data=ranking_report,
        message="获取书籍详情成功"
    )


@router.get("/history/{ranking_id}", response_model=DataResponse)
async def get_ranking_report_list(ranking_id: int, days: int = 10) -> DataResponse:
    """
    获取榜单前N天历史报告
    :param ranking_id:
    :param days:
    :return:
    """
    report_list = []
    for d in range(days):
        report_list.append({
            "ranking_id": ranking_id,
            "report_title": "report" + str(ranking_id),
            "report_content": "who cares?",
            "report_date": datetime.today() - timedelta(days=d),
        })

    return DataResponse(
        data=report_list,
        message="获取书籍详情成功"
    )
