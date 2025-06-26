"""
Ranking数据访问对象

封装Ranking和RankingSnapshot的数据库操作
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlmodel import select, func, and_, desc

from app.modules.base import BaseDAO
from app.modules.models import Ranking, RankingSnapshot, Book


class RankingDAO(BaseDAO):
    """Ranking数据访问对象"""

    # ==================== Ranking基础CRUD ====================
    
    def get_by_id(self, ranking_id: str) -> Optional[Ranking]:
        """根据榜单ID获取榜单信息"""
        statement = select(Ranking).where(Ranking.ranking_id == ranking_id)
        return self.session.exec(statement).first()
    
    def get_all(self) -> List[Ranking]:
        """获取所有榜单配置"""
        statement = select(Ranking).order_by(Ranking.ranking_id)
        return list(self.session.exec(statement))
    
    def create(self, ranking_data: Dict[str, Any]) -> Ranking:
        """创建新榜单配置"""
        ranking = Ranking(**ranking_data)
        self.session.add(ranking)
        self.session.commit()
        self.session.refresh(ranking)
        return ranking
    
    def update(self, ranking_id: str, update_data: Dict[str, Any]) -> Optional[Ranking]:
        """更新榜单配置"""
        ranking = self.get_by_id(ranking_id)
        if ranking:
            for field, value in update_data.items():
                if hasattr(ranking, field):
                    setattr(ranking, field, value)
            self.session.commit()
            self.session.refresh(ranking)
        return ranking

    # ==================== RankingSnapshot操作 ====================
    
    def get_latest_snapshot_time(self, ranking_id: str) -> Optional[datetime]:
        """获取榜单最新快照时间"""
        statement = (
            select(RankingSnapshot.snapshot_time)
            .where(RankingSnapshot.ranking_id == ranking_id)
            .order_by(RankingSnapshot.snapshot_time.desc())
            .limit(1)
        )
        return self.session.exec(statement).first()
    
    def get_ranking_books(
        self, 
        ranking_id: str, 
        snapshot_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[tuple[RankingSnapshot, Book]], Optional[datetime]]:
        """获取榜单书籍列表"""
        # 如果没有指定时间，使用最新快照
        if snapshot_time is None:
            snapshot_time = self.get_latest_snapshot_time(ranking_id)
            if not snapshot_time:
                return [], None
        
        # 获取指定时间的榜单数据
        statement = (
            select(RankingSnapshot, Book)
            .join(Book, RankingSnapshot.book_id == Book.book_id)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time == snapshot_time
                )
            )
            .order_by(RankingSnapshot.position.asc())
            .offset(offset)
            .limit(limit)
        )
        
        results = list(self.session.exec(statement))
        return results, snapshot_time
    
    def get_book_ranking_history(
        self, 
        book_id: str, 
        days: int = 30
    ) -> List[tuple[RankingSnapshot, Ranking]]:
        """获取书籍榜单历史"""
        start_date = datetime.now() - timedelta(days=days)
        
        statement = (
            select(RankingSnapshot, Ranking)
            .join(Ranking, RankingSnapshot.ranking_id == Ranking.ranking_id)
            .where(
                and_(
                    RankingSnapshot.book_id == book_id,
                    RankingSnapshot.snapshot_time >= start_date
                )
            )
            .order_by(RankingSnapshot.snapshot_time.desc())
        )
        
        return list(self.session.exec(statement))
    
    def get_ranking_history_summary(
        self, 
        ranking_id: str, 
        days: int = 7
    ) -> List[tuple[datetime, int, Optional[str]]]:
        """获取榜单历史摘要"""
        start_date = datetime.now() - timedelta(days=days)
        
        # 按快照时间分组统计
        statement = (
            select(
                RankingSnapshot.snapshot_time,
                func.count(RankingSnapshot.id).label("total_books")
            )
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time >= start_date
                )
            )
            .group_by(RankingSnapshot.snapshot_time)
            .order_by(RankingSnapshot.snapshot_time.desc())
        )
        
        results = list(self.session.exec(statement))
        
        # 获取每个快照的第一名书籍
        summaries = []
        for row in results:
            # 查询第一名书籍
            top_book_stmt = (
                select(Book.title)
                .join(RankingSnapshot, Book.book_id == RankingSnapshot.book_id)
                .where(
                    and_(
                        RankingSnapshot.ranking_id == ranking_id,
                        RankingSnapshot.snapshot_time == row.snapshot_time,
                        RankingSnapshot.position == 1
                    )
                )
                .limit(1)
            )
            top_book_title = self.session.exec(top_book_stmt).first()
            
            summaries.append((row.snapshot_time, row.total_books, top_book_title))
        
        return summaries
    
    def create_snapshot(self, snapshot_data: Dict[str, Any]) -> RankingSnapshot:
        """创建榜单快照"""
        snapshot = RankingSnapshot(**snapshot_data)
        self.session.add(snapshot)
        self.session.commit()
        self.session.refresh(snapshot)
        return snapshot
    
    def batch_create_snapshots(self, snapshots_data: List[Dict[str, Any]]) -> List[RankingSnapshot]:
        """批量创建榜单快照"""
        snapshots = [RankingSnapshot(**data) for data in snapshots_data]
        self.session.add_all(snapshots)
        self.session.commit()
        for snapshot in snapshots:
            self.session.refresh(snapshot)
        return snapshots

    # ==================== 业务查询方法 ====================
    
    def get_current_book_rankings(self, book_id: str) -> List[tuple[RankingSnapshot, Ranking]]:
        """获取书籍当前在榜情况"""
        # 获取书籍在各榜单的最新排名
        subquery = (
            select(
                RankingSnapshot.ranking_id,
                func.max(RankingSnapshot.snapshot_time).label("latest_time")
            )
            .where(RankingSnapshot.book_id == book_id)
            .group_by(RankingSnapshot.ranking_id)
        ).subquery()
        
        statement = (
            select(RankingSnapshot, Ranking)
            .join(Ranking, RankingSnapshot.ranking_id == Ranking.ranking_id)
            .join(
                subquery,
                and_(
                    RankingSnapshot.ranking_id == subquery.c.ranking_id,
                    RankingSnapshot.snapshot_time == subquery.c.latest_time
                )
            )
            .where(RankingSnapshot.book_id == book_id)
            .order_by(RankingSnapshot.position.asc())
        )
        
        return list(self.session.exec(statement))
    
    def get_snapshots_by_date_range(
        self,
        ranking_id: str,
        start_date: datetime,
        end_date: Optional[datetime] = None
    ) -> List[RankingSnapshot]:
        """获取指定日期范围的榜单快照"""
        if end_date is None:
            end_date = datetime.now()
        
        statement = (
            select(RankingSnapshot)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time >= start_date,
                    RankingSnapshot.snapshot_time <= end_date
                )
            )
            .order_by(RankingSnapshot.snapshot_time.desc())
        )
        
        return list(self.session.exec(statement))
    def count_rankings(self) -> int:
        """获取榜单总数"""
        statement = select(func.count(Ranking.ranking_id))
        return self.session.exec(statement).first() or 0
    
    def count_ranking_books(self, ranking_id: str, snapshot_time: Optional[datetime] = None) -> int:
        """获取指定榜单在指定时间的书籍总数"""
        # 如果没有指定时间，使用最新快照时间
        if snapshot_time is None:
            snapshot_time = self.get_latest_snapshot_time(ranking_id)
            if not snapshot_time:
                return 0
        
        statement = (
            select(func.count(RankingSnapshot.id))
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time == snapshot_time
                )
            )
        )
        
        return self.session.exec(statement).first() or 0
