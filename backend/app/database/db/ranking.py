"""
榜单相关数据模型
包含榜单配置表和排名快照表
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Float, Index, UniqueConstraint, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped

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
    rank_id: Mapped[int] = mapped_column(Integer, unique=True, index=True,comment="榜单唯一标识ID，来源于晋江文学城的榜单ID")
    rank_name: Mapped[str] = mapped_column(String(100), index=True, comment="榜单中文名称，如：夹子相关、总收藏榜、总推荐榜等")
    rank_group_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, comment="榜单分组类型，如：热门、分类、专题等，用于榜单分类管理")
    page_id: Mapped[str] = mapped_column(String(50), index=True, comment="页面标识ID，用于关联爬取配置和URL生成")

    # 索引优化
    __table_args__ = (
        Index("idx_ranking_rank_id", "rank_id"),
        Index("idx_ranking_name", "rank_name"),
        Index("idx_ranking_page_id", "page_id"),
        Index("idx_ranking_group_type", "rank_group_type"),
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
    ranking_id: Mapped[int] = mapped_column(Integer, ForeignKey("rankings.id"), index=True, comment="关联的榜单ID，对应Ranking表的主键id")
    book_id: Mapped[int] = mapped_column(Integer, ForeignKey("books.id"), index=True, comment="关联的书籍ID，对应Book表的主键id")
    # 排名信息
    position: Mapped[int] = mapped_column(Integer, index=True, comment="书籍在榜单中的排名位置，数字越小排名越高，从1开始")
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True, comment="排名分数，某些榜单会提供具体的评分数据，可选字段")

    # 快照时间
    snapshot_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, index=True, comment="快照记录时间，用于趋势分析和排名历史查询")

    # 复合索引和约束 - 优化查询性能和数据完整性
    __table_args__ = (
        # 榜单时间索引 - 用于获取特定榜单的历史快照
        Index("idx_ranking_snapshot_time", "ranking_id", "snapshot_time"),
        # 排名位置索引 - 用于按排名查询
        Index("idx_ranking_snapshot_position", "ranking_id", "position", "snapshot_time"),
        # 书籍排名索引 - 用于查询书籍的排名历史
        Index("idx_book_ranking_snapshot", "book_id", "ranking_id", "snapshot_time"),
        # 唯一约束 - 确保同一时间点同一榜单中每本书只有一个排名
        UniqueConstraint("ranking_id", "book_id", "snapshot_time", name="uq_ranking_book_snapshot"),
    )
