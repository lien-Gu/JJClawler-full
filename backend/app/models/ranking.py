"""
榜单相关数据模型
"""

from datetime import date as Date
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from app.models import BookRankingInfo
from base import BaseSchema


class RankingBasic(BaseSchema):
    """榜单基础信息响应"""
    id: int = Field(..., description="榜单的内部唯一ID")
    ranking_id: str = Field(..., description="榜单ID")
    channel_name: str = Field(..., description="榜单名称")
    sub_channel_name: str = Field(..., description="子榜单名称")
    page_id: str = Field(..., description="页面ID")
    rank_group_type: str = Field(..., description="榜单分组类型")


class RankingSnapshot(BaseSchema, BookRankingInfo):
    """
    榜单快照信息
    """
    books: List[BookRankingInfo] = Field([], description="榜单书籍列表")
    snapshot_time: datetime = Field(..., description="快照时间")


class RankingDetail(RankingBasic, RankingSnapshot):
    """榜单详情响应"""






