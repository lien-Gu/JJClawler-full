"""
数据库表模型定义

定义SQLModel数据库表结构
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


class Book(SQLModel, table=True):
    """书籍信息表（仅静态信息）"""
    __tablename__ = "books"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: str = Field(unique=True, index=True, description="书籍ID")
    title: str = Field(description="书名")
    author_id: str = Field(index=True, description="作者ID")
    author_name: str = Field(index=True, description="作者名")
    novel_class: Optional[str] = Field(default=None, description="小说分类")
    tags: Optional[str] = Field(default=None, description="标签(JSON字符串)")
    first_seen: datetime = Field(default_factory=datetime.now, description="首次发现时间")
    last_updated: datetime = Field(default_factory=datetime.now, description="最后更新时间")
    
    # 关系字段
    book_snapshots: List["BookSnapshot"] = Relationship(back_populates="book")
    ranking_snapshots: List["RankingSnapshot"] = Relationship(back_populates="book")


class BookSnapshot(SQLModel, table=True):
    """书籍快照表（存储书籍级别的动态信息）"""
    __tablename__ = "book_snapshots"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: str = Field(foreign_key="books.book_id", index=True, description="书籍ID")
    total_clicks: Optional[int] = Field(default=None, description="总点击量")
    total_favorites: Optional[int] = Field(default=None, description="总收藏量")
    comment_count: Optional[int] = Field(default=None, description="评论数")
    chapter_count: Optional[int] = Field(default=None, description="章节数")
    snapshot_time: datetime = Field(index=True, description="快照时间")
    
    # 关系字段
    book: Optional[Book] = Relationship(back_populates="book_snapshots")
    
    __table_args__ = (
        Index("idx_book_snapshot_time", "book_id", "snapshot_time"),
    )


class RankingSnapshot(SQLModel, table=True):
    """榜单快照表（存储榜单维度的数据）"""
    __tablename__ = "ranking_snapshots"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    ranking_id: str = Field(foreign_key="rankings.ranking_id", index=True, description="榜单ID")
    book_id: str = Field(foreign_key="books.book_id", index=True, description="书籍ID")
    position: int = Field(description="榜单位置")
    snapshot_time: datetime = Field(index=True, description="快照时间")
    
    # 关系字段
    ranking: Optional[Ranking] = Relationship(back_populates="ranking_snapshots")
    book: Optional[Book] = Relationship(back_populates="ranking_snapshots")
    
    __table_args__ = (
        Index("idx_ranking_time", "ranking_id", "snapshot_time"),
        Index("idx_book_ranking_time", "book_id", "snapshot_time"),
        Index("idx_ranking_position", "ranking_id", "position", "snapshot_time"),
    )