"""
榜单相关数据模型
包含榜单配置表和排名快照表
"""

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Ranking(Base):
    """榜单配置表

    存储各种榜单的基本配置信息：
    - 榜单基本信息（ID、名称、分组）
    - 页面配置信息
    - 榜单层级关系

    注意：具体的排名数据存储在RankingSnapshot表中
    """

    __tablename__ = "rankings"

    # 榜单基本信息
    rank_id: Mapped[str] = mapped_column(
        String(100),
        index=True,
        comment="榜单唯一标识ID，来源于晋江文学城的榜单ID",
    )
    hash_id: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        comment="榜单哈希唯一标识，基于rank_id|channel_name|channel_id|page_id|sub_channel_id生成的MD5值",
    )
    channel_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        comment="榜单中文名称，如：夹子相关、总收藏榜、总推荐榜等",
    )
    rank_group_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="榜单分组类型，如：热门、分类、专题等，用于榜单分类管理",
    )
    channel_id: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="频道id，如：热门、分类、专题等，用于榜单分类管理",
    )
    page_id: Mapped[str] = mapped_column(
        String(50), index=True, comment="页面标识ID，用于关联爬取配置和URL生成"
    )
    sub_channel_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="子榜单名称，用于处理嵌套榜单结构"
    )

    # 索引优化
    __table_args__ = (
        Index("idx_ranking_rank_id", "rank_id"),
        Index("idx_ranking_hash_id", "hash_id"),
        Index("idx_ranking_channel_name", "channel_name"),
        Index("idx_ranking_page_id", "page_id"),
        Index("idx_ranking_group_type", "rank_group_type"),
        Index("idx_ranking_sub_channel_name", "sub_channel_name"),
    )


class RankingSnapshot(Base):
    """榜单排名快照表

    记录特定时间点的榜单排名情况：
    - 书籍在榜单中的位置
    - 排名分数（如有）
    - 快照时间用于趋势分析

    每次爬取榜单都会创建新的快照记录，用于分析排名变化趋势
    """

    __tablename__ = "ranking_snapshots"

    # 关联信息
    ranking_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("rankings.id"),
        index=True,
        comment="关联的榜单ID，对应Ranking表的主键id",
    )
    novel_id: Mapped[int] =mapped_column(
        Integer,
        ForeignKey("books.novel_id"),
        index=True,
        comment="晋江app上的书籍id，可用于后续构建url"
    )
    batch_id: Mapped[str] = mapped_column(
        String(36),
        index=True,
        comment="批次ID，用于标识同一次爬取任务产生的数据，确保数据时间一致性"
    )
    # 排名信息
    position: Mapped[int] = mapped_column(
        Integer, index=True, comment="书籍在榜单中的排名位置，数字越小排名越高，从1开始"
    )

    # 快照时间
    snapshot_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        index=True,
        comment="快照记录时间，用于趋势分析和排名历史查询",
    )

    # 覆盖Base类的时间戳字段（实际数据库表中没有这些字段）
    created_at = None
    updated_at = None

    # 复合索引和约束 - 优化查询性能和数据完整性
    __table_args__ = (
        # 榜单时间索引 - 用于获取特定榜单的历史快照
        Index("idx_ranking_snapshot_time", "ranking_id", "snapshot_time"),
        # 排名位置索引 - 用于按排名查询
        Index(
            "idx_ranking_snapshot_position", "ranking_id", "position", "snapshot_time"
        ),
        # 书籍排名索引 - 用于查询书籍的排名历史
        Index("idx_book_ranking_snapshot", "novel_id", "ranking_id", "snapshot_time"),
        # 批次ID索引 - 用于快速查询同一批次的数据
        Index("idx_ranking_batch_id", "batch_id"),
        # 批次榜单索引 - 用于获取特定批次的榜单快照
        Index("idx_ranking_batch_ranking", "ranking_id", "batch_id"),
        # 唯一约束 - 确保同一批次中同一榜单每本书只有一个排名
        UniqueConstraint(
            "ranking_id", "novel_id", "batch_id", name="uq_ranking_book_batch"
        ),
    )
