"""
书籍相关数据模型
"""

from datetime import datetime

from pydantic import Field

from base import BaseSchema


class BookBasic(BaseSchema):
    """书籍基础信息响应"""

    novel_id: int = Field(gt=0, description="网站上的小说ID")
    title: str = Field(min_length=1, description="书名")


class BookSnapshot(BaseSchema):
    """书籍快照响应模型"""

    snapshot_time: datetime = Field(..., description="快照时间")
    favorites: int = Field(default=0, description="收藏数")
    clicks: int = Field(default=0, description="非V章点击数")
    comments: int = Field(default=0, description="评论数")
    nutrition: int = Field(default=0, description="营养液数量")
    word_counts: int | None = Field(None, description="字数")
    chapter_counts: int = Field(None, description="章节统计")
    status: str | None = Field(None, description="状态")


class BookDetail(BookBasic, BookSnapshot):
    """书籍详情响应，总是获取最新时间的point"""
    vip_chapter_id: int = Field(default=0, description="入v的章节，0表示没有入V")

class BookRankingInfo(BaseSchema):
    """书籍排名信息"""

    book_id: int = Field(..., description="书籍ID")
    position: int = Field(..., description="排名位置")
    snapshot_time: datetime = Field(..., description="快照时间")
    page_id: str = Field(..., description="榜单页面ID")
    channel_name: str = Field(..., description="榜单名称")
    sub_channel_name: str | None = Field(..., description="子榜单名称")
