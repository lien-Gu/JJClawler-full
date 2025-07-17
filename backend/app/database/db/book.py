"""
书籍相关数据模型
包含书籍基础信息表和动态统计快照表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Index
from sqlalchemy.orm import mapped_column, Mapped

from .base import Base


class Book(Base):
    """书籍基础信息表
    
    存储书籍的静态基本信息，包括：
    - 书籍ID和标题等基本信息
    - 作者信息
    - 分类标签
    
    注意：动态统计数据（点击量、收藏量等）存储在BookSnapshot表中
    """
    __tablename__ = "books"

    # 书籍基本信息
    novel_id: Mapped[int] = mapped_column(
        Integer, 
        unique=True, 
        index=True,
        comment="书籍唯一标识ID，来源于晋江文学城的小说ID"
    )
    
    title: Mapped[str] = mapped_column(
        String(200), 
        index=True,
        comment="书籍标题，中文名称"
    )
    
    author_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        comment="作者ID，来源于晋江文学城的作者ID"
    )
    
    # 分类信息
    novel_class: Mapped[Optional[str]] = mapped_column(
        String(50), 
        nullable=True,
        comment="小说分类，如：现代言情、古代言情、纯爱小说等"
    )
    
    tags: Mapped[Optional[str]] = mapped_column(
        String(500), 
        nullable=True,
        comment="标签，多个标签用逗号分隔，如：都市,职场,甜文"
    )

    # 索引优化
    __table_args__ = (
        Index("idx_book_novel_id", "novel_id"),
        Index("idx_book_title", "title"),
        Index("idx_book_author", "author_id"),
        Index("idx_book_class", "novel_class"),
    )


class BookSnapshot(Base):
    """书籍动态统计快照表
    
    记录书籍在特定时间点的动态统计数据：
    - 点击量、收藏量等互动数据
    - 字数、状态等可变信息
    - 快照时间用于趋势分析
    
    每次爬取都会创建新的快照记录，用于分析书籍数据的变化趋势
    """
    __tablename__ = "book_snapshots"

    # 关联信息
    novel_id: Mapped[int] = mapped_column(
        Integer, 
        index=True,
        comment="关联的书籍ID，对应Book表的novel_id"
    )

    # 互动统计数据
    favorites: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="收藏数量，读者收藏该书籍的总数"
    )
    
    clicks: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="点击量，书籍详情页的访问次数"
    )
    
    comments: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="评论数量，读者对该书籍的评论总数"
    )
    
    recommendations: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        comment="推荐数，读者推荐该书籍的次数"
    )

    # 内容信息  
    word_count: Mapped[Optional[int]] = mapped_column(
        Integer, 
        nullable=True,
        comment="字数统计，书籍当前的总字数"
    )

    # 快照时间
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.now, 
        index=True,
        comment="快照记录时间，用于趋势分析和数据版本控制"
    )

    # 复合索引 - 优化查询性能
    __table_args__ = (
        Index("idx_book_snapshot_time", "novel_id", "snapshot_time"),
        Index("idx_book_snapshot_novel", "novel_id", "snapshot_time"),
    )
