"""
Book领域数据模型

包含Book和BookSnapshot的数据库表模型定义
"""
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, Index


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
    total_clicks: Optional[int] = Field(default=None, description="非V章点击量(novip_clicks)")
    total_favorites: Optional[int] = Field(default=None, description="总收藏量")
    comment_count: Optional[int] = Field(default=None, description="评论数")
    chapter_count: Optional[int] = Field(default=None, description="总章节数")
    vip_chapter_count: Optional[int] = Field(default=None, description="VIP章节数")
    word_count: Optional[int] = Field(default=None, description="字数")
    nutrition_count: Optional[int] = Field(default=None, description="营养液数量")
    snapshot_time: datetime = Field(index=True, description="快照时间")
    
    # 关系字段
    book: Optional[Book] = Relationship(back_populates="book_snapshots")
    
    __table_args__ = (
        Index("idx_book_snapshot_time", "book_id", "snapshot_time"),
    )