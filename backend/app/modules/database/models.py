"""
数据库模型定义
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Integer, String, Boolean, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Book(Base):
    """书籍基础信息表"""
    __tablename__ = "books"
    
    # 主键和基本信息
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    novel_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    author: Mapped[str] = mapped_column(String(100), index=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    snapshots: Mapped[List["BookSnapshot"]] = relationship(back_populates="book", cascade="all, delete-orphan")
    ranking_snapshots: Mapped[List["RankingSnapshot"]] = relationship(back_populates="book", cascade="all, delete-orphan")


class BookSnapshot(Base):
    """书籍动态统计快照表"""
    __tablename__ = "book_snapshots"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"), index=True)
    
    # 统计数据
    favorites: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    comments: Mapped[int] = mapped_column(Integer, default=0)
    recommendations: Mapped[int] = mapped_column(Integer, default=0)
    word_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 时间戳
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    
    # 关系
    book: Mapped["Book"] = relationship(back_populates="snapshots")
    
    # 复合索引
    __table_args__ = (
        Index("idx_book_snapshot_time", "book_id", "snapshot_time"),
    )


class Ranking(Base):
    """榜单配置表"""
    __tablename__ = "rankings"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # 基本信息
    rank_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    page_id: Mapped[str] = mapped_column(String(50), index=True)
    rank_group_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关系
    ranking_snapshots: Mapped[List["RankingSnapshot"]] = relationship(back_populates="ranking", cascade="all, delete-orphan")
    
    # 索引
    __table_args__ = (
        Index("idx_ranking_page_id", "page_id"),
        Index("idx_ranking_group_type", "rank_group_type"),
    )


class RankingSnapshot(Base):
    """榜单排名快照表"""
    __tablename__ = "ranking_snapshots"
    
    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ranking_id: Mapped[int] = mapped_column(Integer, ForeignKey("rankings.id"), index=True)
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"), index=True)
    
    # 排名信息
    position: Mapped[int] = mapped_column(Integer, index=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # 时间戳
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)
    
    # 关系
    ranking: Mapped["Ranking"] = relationship(back_populates="ranking_snapshots")
    book: Mapped["Book"] = relationship(back_populates="ranking_snapshots")
    
    # 复合索引
    __table_args__ = (
        Index("idx_ranking_snapshot_time", "ranking_id", "snapshot_time"),
        Index("idx_ranking_snapshot_position", "ranking_id", "position", "snapshot_time"),
        Index("idx_book_ranking_snapshot", "book_id", "ranking_id", "snapshot_time"),
        UniqueConstraint("ranking_id", "book_id", "snapshot_time", name="uq_ranking_book_snapshot"),
    )