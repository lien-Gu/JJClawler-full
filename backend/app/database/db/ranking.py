"""
数据库模型定义
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Integer, String, Float, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import mapped_column, relationship, Mapped

from .base import Base


class Ranking(Base):
    """榜单配置表"""
    __tablename__ = "rankings"

    # 主键
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # 基本信息
    rank_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    rank_name: Mapped[str] = mapped_column(String(100), index=True)
    rank_group_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    page_id: Mapped[str] = mapped_column(String(50), index=True)

    # 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关系在应用层处理，不使用数据库外键

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
    ranking_id: Mapped[int] = mapped_column(Integer, index=True)
    novel_id: Mapped[int] = mapped_column(Integer, index=True)

    # 排名信息
    position: Mapped[int] = mapped_column(Integer, index=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # 时间戳
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True)

    # 关系在应用层处理，不使用数据库外键

    # 复合索引
    __table_args__ = (
        Index("idx_ranking_snapshot_time", "ranking_id", "snapshot_time"),
        Index("idx_ranking_snapshot_position", "ranking_id", "position", "snapshot_time"),
        Index("idx_book_ranking_snapshot", "novel_id", "ranking_id", "snapshot_time"),
        UniqueConstraint("ranking_id", "novel_id", "snapshot_time", name="uq_ranking_book_snapshot"),
    )
