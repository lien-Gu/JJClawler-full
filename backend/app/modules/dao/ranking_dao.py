"""
榜单相关DAO
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, and_, desc, func, distinct
from sqlalchemy.orm import Session, joinedload

from .base_dao import BaseDAO
from ..database.models import Ranking, RankingSnapshot, Book


class RankingDAO(BaseDAO[Ranking]):
    """榜单数据访问对象"""
    
    def __init__(self):
        super().__init__(Ranking)
    
    def get_by_rank_id(self, db: Session, rank_id: int) -> Optional[Ranking]:
        """根据rank_id获取榜单"""
        return db.scalar(select(Ranking).where(Ranking.rank_id == rank_id))
    
    def get_by_page_id(self, db: Session, page_id: str) -> List[Ranking]:
        """根据page_id获取榜单列表"""
        return db.scalars(
            select(Ranking).where(Ranking.page_id == page_id)
        ).all()
    
    def get_by_group_type(self, db: Session, group_type: str) -> List[Ranking]:
        """根据榜单分组类型获取榜单"""
        return db.scalars(
            select(Ranking).where(Ranking.rank_group_type == group_type)
        ).all()
    
    def create_or_update_by_rank_id(self, db: Session, obj_in: Dict[str, Any]) -> Ranking:
        """根据rank_id创建或更新榜单"""
        rank_id = obj_in.get("rank_id")
        if not rank_id:
            raise ValueError("rank_id is required")
        
        db_obj = self.get_by_rank_id(db, rank_id)
        if db_obj:
            # 更新现有记录
            obj_in["updated_at"] = datetime.now()
            return self.update(db, db_obj=db_obj, obj_in=obj_in)
        else:
            # 创建新记录
            return self.create(db, obj_in)


class RankingSnapshotDAO(BaseDAO[RankingSnapshot]):
    """榜单快照数据访问对象"""
    
    def __init__(self):
        super().__init__(RankingSnapshot)
    
    def get_latest_by_ranking_id(
        self, 
        db: Session, 
        ranking_id: int, 
        limit: int = 50
    ) -> List[RankingSnapshot]:
        """获取榜单最新快照"""
        # 获取最新时间
        latest_time = db.scalar(
            select(func.max(RankingSnapshot.snapshot_time))
            .where(RankingSnapshot.ranking_id == ranking_id)
        )
        
        if not latest_time:
            return []
        
        return db.scalars(
            select(RankingSnapshot)
            .options(joinedload(RankingSnapshot.book))
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time == latest_time
                )
            )
            .order_by(RankingSnapshot.position)
            .limit(limit)
        ).all()
    
    def get_by_ranking_and_date(
        self, 
        db: Session, 
        ranking_id: int, 
        target_date: date,
        limit: int = 50
    ) -> List[RankingSnapshot]:
        """获取指定日期的榜单快照"""
        # 查找目标日期最接近的快照时间
        target_time = db.scalar(
            select(RankingSnapshot.snapshot_time)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    func.date(RankingSnapshot.snapshot_time) == target_date
                )
            )
            .order_by(desc(RankingSnapshot.snapshot_time))
            .limit(1)
        )
        
        if not target_time:
            return []
        
        return db.scalars(
            select(RankingSnapshot)
            .options(joinedload(RankingSnapshot.book))
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time == target_time
                )
            )
            .order_by(RankingSnapshot.position)
            .limit(limit)
        ).all()
    
    def get_book_ranking_history(
        self, 
        db: Session, 
        book_id: int, 
        ranking_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 30
    ) -> List[RankingSnapshot]:
        """获取书籍排名历史"""
        query = select(RankingSnapshot).where(RankingSnapshot.book_id == book_id)
        
        if ranking_id:
            query = query.where(RankingSnapshot.ranking_id == ranking_id)
        if start_time:
            query = query.where(RankingSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(RankingSnapshot.snapshot_time <= end_time)
        
        return db.scalars(
            query.options(joinedload(RankingSnapshot.ranking))
            .order_by(desc(RankingSnapshot.snapshot_time))
            .limit(limit)
        ).all()
    
    def get_ranking_statistics(self, db: Session, ranking_id: int) -> Dict[str, Any]:
        """获取榜单统计信息"""
        result = db.execute(
            select(
                func.count(distinct(RankingSnapshot.snapshot_time)).label("total_snapshots"),
                func.count(distinct(RankingSnapshot.book_id)).label("unique_books"),
                func.min(RankingSnapshot.snapshot_time).label("first_snapshot_time"),
                func.max(RankingSnapshot.snapshot_time).label("last_snapshot_time")
            ).where(RankingSnapshot.ranking_id == ranking_id)
        ).first()
        
        if result:
            return {
                "total_snapshots": result.total_snapshots or 0,
                "unique_books": result.unique_books or 0,
                "first_snapshot_time": result.first_snapshot_time,
                "last_snapshot_time": result.last_snapshot_time
            }
        return {}
    
    def get_ranking_trend(
        self, 
        db: Session, 
        ranking_id: int, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Tuple[datetime, int]]:
        """获取榜单变化趋势（每个快照时间的书籍数量）"""
        query = select(
            RankingSnapshot.snapshot_time,
            func.count(RankingSnapshot.book_id).label("book_count")
        ).where(RankingSnapshot.ranking_id == ranking_id)
        
        if start_time:
            query = query.where(RankingSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(RankingSnapshot.snapshot_time <= end_time)
        
        result = db.execute(
            query.group_by(RankingSnapshot.snapshot_time)
            .order_by(RankingSnapshot.snapshot_time)
        ).all()
        
        return [(row.snapshot_time, row.book_count) for row in result]
    
    def bulk_create(self, db: Session, snapshots: List[Dict[str, Any]]) -> List[RankingSnapshot]:
        """批量创建快照"""
        db_objs = [RankingSnapshot(**snapshot) for snapshot in snapshots]
        db.add_all(db_objs)
        db.commit()
        return db_objs
    
    def delete_old_snapshots(
        self, 
        db: Session, 
        ranking_id: int, 
        before_time: datetime,
        keep_days: int = 30
    ) -> int:
        """删除旧快照，保留指定天数的记录"""
        # 获取要保留的快照时间列表
        keep_times = db.scalars(
            select(distinct(RankingSnapshot.snapshot_time))
            .where(RankingSnapshot.ranking_id == ranking_id)
            .order_by(desc(RankingSnapshot.snapshot_time))
            .limit(keep_days)
        ).all()
        
        # 删除旧快照
        deleted = db.execute(
            delete(RankingSnapshot)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time < before_time,
                    ~RankingSnapshot.snapshot_time.in_(keep_times)
                )
            )
        )
        db.commit()
        return deleted.rowcount
    
    def get_books_comparison(
        self, 
        db: Session, 
        ranking_ids: List[int], 
        target_date: Optional[date] = None
    ) -> Dict[int, List[RankingSnapshot]]:
        """获取多个榜单的书籍对比数据"""
        if target_date:
            # 指定日期的对比
            result = {}
            for ranking_id in ranking_ids:
                result[ranking_id] = self.get_by_ranking_and_date(db, ranking_id, target_date)
            return result
        else:
            # 最新数据的对比
            result = {}
            for ranking_id in ranking_ids:
                result[ranking_id] = self.get_latest_by_ranking_id(db, ranking_id)
            return result