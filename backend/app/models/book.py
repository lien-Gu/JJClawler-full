"""
书籍相关数据模型
"""

from datetime import datetime

from pydantic import BaseModel, Field

from ..database.db.book import Book, BookSnapshot
from ..database.db.ranking import RankingSnapshot, Ranking


class BookResponse(BaseModel):
    """书籍基础信息响应"""

    id: int = Field(..., description="书籍ID")
    novel_id: int = Field(gt=0, description="网站上的小说ID")
    title: str = Field(min_length=1, description="书名")

    @classmethod
    def from_book(cls, book_t: Book) -> "BookResponse":
        """
        从Book数据库模型创建BookResponse实例

        Args:
            book_t: Book数据库模型实例

        Returns:
            BookResponse: 响应模型实例
        """
        return cls(id=book_t.id, novel_id=book_t.novel_id, title=book_t.title)


class BookSnapshotResponse(BaseModel):
    """书籍快照响应模型"""

    book_id: int = Field(..., description="书籍ID")
    snapshot_time: datetime = Field(..., description="快照时间")
    favorites: int = Field(default=0, description="收藏数")
    clicks: int = Field(default=0, description="点击数")
    comments: int = Field(default=0, description="评论数")
    word_count: int | None = Field(None, description="字数")
    status: str | None = Field(None, description="状态")

    @classmethod
    def from_snapshot(cls, snapshot: BookSnapshot) -> "BookSnapshotResponse":
        """
        从BookSnapshot数据库模型创建BookSnapshotResponse实例

        Args:
            snapshot: BookSnapshot数据库模型实例

        Returns:
            BookSnapshotResponse: 快照响应模型实例
        """
        return cls(
            book_id=snapshot.book_id,
            snapshot_time=snapshot.snapshot_time,
            favorites=snapshot.favorites or 0,
            clicks=snapshot.clicks or 0,
            comments=snapshot.comments or 0,
            word_count=snapshot.word_count,
            status=snapshot.status
        )


class BookDetailResponse(BookResponse, BookSnapshotResponse):
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
            book_id=book_t.id,
            snapshot_time=snapshot.snapshot_time if snapshot else None,
            favorites=snapshot.favorites if snapshot else 0,
            clicks=snapshot.clicks if snapshot else 0,
            comments=snapshot.comments if snapshot else 0,
            word_count=snapshot.word_count if snapshot else None,
            status=snapshot.status if snapshot else None,
        )


class BookRankingInfoResponse(BaseModel):
    """书籍排名信息"""

    book_id: int = Field(..., description="书籍ID")
    ranking_id: int = Field(..., description="榜单ID")
    ranking_name: str = Field(..., description="榜单名称")
    sub_ranking_name: str = Field(..., description="子榜单名称")
    ranking_page_id: str = Field(..., description="榜单页面ID")
    position: int = Field(..., description="排名位置")
    snapshot_time: datetime = Field(..., description="快照时间")

    @classmethod
    def from_snapshot(cls, book_id: int, ranking: Ranking, snapshot: RankingSnapshot) -> "BookRankingInfoResponse":
        """
        从RankingSnapshot和Ranking对象创建BookRankingInfoResponse实例

        :param book_id: 书籍ID
        :param snapshot: 排名快照对象
        :param ranking: 榜单对象
        :return: 书籍排名信息响应实例
        """
        return cls(
            book_id=book_id,
            ranking_id=snapshot.ranking_id,
            ranking_name=ranking.name,
            sub_ranking_name=ranking.sub_ranking_name,
            ranking_page_id=ranking.page_id,
            position=snapshot.position,
            snapshot_time=snapshot.snapshot_time,
        )
