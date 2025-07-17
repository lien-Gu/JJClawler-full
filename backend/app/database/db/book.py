from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Integer, String, ForeignKey, Index
from sqlalchemy.orm import mapped_column, relationship, Mapped

from .base import Base


class Book(Base):
    """书籍基础信息表"""
    __tablename__ = "books"

    # 主键和基本信息
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    novel_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    author_name: Mapped[str] = mapped_column(String(100), index=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系在应用层处理，不使用数据库外键


class BookSnapshot(Base):
    """书籍动态统计快照表"""
    __tablename__ = "book_snapshots"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    novel_id: Mapped[int] = mapped_column(Integer, index=True)

    # 统计数据
    favorites: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    recommendations: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # 时间戳
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

    # 关系在应用层处理，不使用数据库外键

    # 复合索引
    __table_args__ = (
        Index("idx_book_snapshot_time", "novel_id", "snapshot_time"),
    )
