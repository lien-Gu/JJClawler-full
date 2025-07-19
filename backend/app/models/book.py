"""
书籍相关数据模型
"""

from datetime import datetime

from pydantic import BaseModel, Field

from ..database.db.book import Book, BookSnapshot


class BookResponse(BaseModel):
    """书籍基础信息响应"""

    id: int = Field(..., description="书籍ID")
    novel_id: int = Field(gt=0, description="网站上的小说ID")
    title: str = Field(min_length=1, description="书名")

    @classmethod
    def from_book_table(cls, book_t: Book) -> "BookResponse":
        """
        从Book数据库模型创建BookResponse实例

        Args:
            book_t: Book数据库模型实例

        Returns:
            BookResponse: 响应模型实例
        """
        return cls(id=book_t.id, novel_id=book_t.novel_id, title=book_t.title)


class BookTrendPoint(BaseModel):
    """书籍趋势数据点"""

    snapshot_time: datetime = Field(..., description="日期")
    clicks: int | None = Field(None, description="点击数")
    favorites: int | None = Field(None, description="收藏数")
    comments: int | None = Field(None, description="评论数")

    @classmethod
    def from_snapshot(cls, snapshot: BookSnapshot) -> "BookTrendPoint":
        """
        从BookSnapshot数据库模型创建BookTrendPoint实例

        Args:
            snapshot: BookSnapshot数据库模型实例

        Returns:
            BookTrendPoint: 趋势数据点实例
        """
        return cls(
            snapshot_time=snapshot.snapshot_time,
            clicks=snapshot.clicks,
            favorites=snapshot.favorites,
            comments=snapshot.comments,
        )


class BookTrendAggregatedPoint(BaseModel):
    """书籍聚合趋势数据点"""

    time_period: str = Field(..., description="时间周期")
    avg_favorites: float = Field(..., description="平均收藏数")
    avg_clicks: float = Field(..., description="平均点击数")
    avg_comments: float = Field(..., description="平均评论数")
    max_favorites: int = Field(..., description="最大收藏数")
    max_clicks: int = Field(..., description="最大点击数")
    min_favorites: int = Field(..., description="最小收藏数")
    min_clicks: int = Field(..., description="最小点击数")
    snapshot_count: int = Field(..., description="快照数量")
    period_start: datetime = Field(..., description="周期开始时间")
    period_end: datetime = Field(..., description="周期结束时间")


class BookDetailResponse(BookResponse, BookTrendPoint):
    """书籍详情响应，总是获取最新时间的point"""

    @classmethod
    def from_book_and_snapshot(
        cls, book_t: Book, snapshot: BookSnapshot = None
    ) -> "BookDetailResponse":
        """
        从Book和BookSnapshot数据库模型创建BookDetailResponse实例

        Args:
            book_t: Book数据库模型实例
            snapshot: BookSnapshot数据库模型实例，可选

        Returns:
            BookDetailResponse: 详情响应模型实例
        """
        return cls(
            id=book_t.id,
            novel_id=book_t.novel_id,
            title=book_t.title,
            snapshot_time=snapshot.snapshot_time if snapshot else datetime.now(),
            clicks=snapshot.clicks if snapshot else None,
            favorites=snapshot.favorites if snapshot else None,
            comments=snapshot.comments if snapshot else None,
        )


class BookRankingInfo(BaseModel):
    """书籍排名信息"""

    book_id: int = Field(..., description="书籍ID")
    ranking_id: int = Field(..., description="榜单ID")
    ranking_name: str = Field(..., description="榜单名称")
    position: int = Field(..., description="排名位置")
    snapshot_time: datetime = Field(..., description="快照时间")

    @classmethod
    def from_history_dict(cls, book_id: int, history_dict: dict) -> "BookRankingInfo":
        """
        从历史数据字典创建BookRankingInfo实例

        Args:
            book_id: 书籍ID
            history_dict: 包含排名历史信息的字典

        Returns:
            BookRankingInfo: 书籍排名信息实例
        """
        return cls(
            book_id=book_id,
            ranking_id=history_dict["ranking_id"],
            ranking_name=history_dict["ranking_name"],
            position=history_dict["position"],
            snapshot_time=history_dict["snapshot_time"],
        )


class BookRankingHistoryResponse(BaseModel):
    """书籍排名历史响应"""

    book_id: int = Field(..., description="书籍ID")
    ranking_history: list[BookRankingInfo] = Field([], description="排名历史")
