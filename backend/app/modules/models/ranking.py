"""
Ranking领域数据模型

包含Ranking和RankingSnapshot的数据库表模型定义
"""

from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Index
from .base import UpdateFrequency


class Ranking(SQLModel, table=True):
    """榜单配置表"""

    __tablename__ = "rankings"

    id: Optional[int] = Field(default=None, primary_key=True)
    ranking_id: str = Field(unique=True, index=True, description="榜单ID")
    name: str = Field(description="榜单中文名")
    channel: str = Field(description="API频道参数")
    frequency: UpdateFrequency = Field(description="更新频率")
    update_interval: int = Field(description="更新间隔(小时)")
    parent_id: Optional[str] = Field(default=None, description="父级榜单ID")

    # 关系字段
    ranking_snapshots: List["RankingSnapshot"] = Relationship(back_populates="ranking")


class RankingSnapshot(SQLModel, table=True):
    """榜单快照表（存储榜单维度的数据）"""

    __tablename__ = "ranking_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    ranking_id: int = Field(foreign_key="rankings.id", index=True, description="榜单ID")
    book_id: str = Field(foreign_key="books.book_id", index=True, description="书籍ID")
    position: int = Field(description="榜单位置")
    snapshot_time: datetime = Field(index=True, description="快照时间")

    # 关系字段
    ranking: Optional[Ranking] = Relationship(back_populates="ranking_snapshots")
    book: Optional["Book"] = Relationship(back_populates="ranking_snapshots")

    __table_args__ = (
        Index("idx_ranking_time", "ranking_id", "snapshot_time"),
        Index("idx_book_ranking_time", "book_id", "snapshot_time"),
        Index("idx_ranking_position", "ranking_id", "position", "snapshot_time"),
    )
