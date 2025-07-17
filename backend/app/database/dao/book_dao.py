"""
书籍相关DAO
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import select, and_, desc, func, delete
from sqlalchemy.orm import Session, joinedload

from .base_dao import BaseDAO
from ..db.book import Book, BookSnapshot


class BookDAO(BaseDAO[Book]):
    """书籍数据访问对象"""

    def __init__(self):
        super().__init__(Book)

    def get_by_novel_id(self, db: Session, novel_id: int) -> Optional[Book]:
        """根据novel_id获取书籍"""
        return db.scalar(select(Book).where(Book.novel_id == novel_id))

    def search_by_title(self, db: Session, title: str, limit: int = 20) -> List[Book]:
        """根据标题搜索书籍"""
        result = db.execute(
            select(Book)
            .where(Book.title.like(f"%{title}%"))
            .limit(limit)
        )
        return list(result.scalars())


    def get_all(self, db: Session, skip: int = 0, limit: int = 1000) -> List[Book]:
        """获取所有书籍"""
        result = db.execute(
            select(Book)
            .offset(skip)
            .limit(limit)
            .order_by(desc(Book.created_at))
        )
        return list(result.scalars())

    def create_or_update_by_novel_id(self, db: Session, obj_in: Dict[str, Any]) -> Book:
        """根据novel_id创建或更新书籍"""
        novel_id = obj_in.get("novel_id")
        if not novel_id:
            raise ValueError("novel_id is required")

        db_obj = self.get_by_novel_id(db, novel_id)
        if db_obj:
            # 更新现有记录
            obj_in["updated_at"] = datetime.now()
            return self.update(db, db_obj=db_obj, obj_in=obj_in)
        else:
            # 创建新记录
            return self.create(db, obj_in)


class BookSnapshotDAO(BaseDAO[BookSnapshot]):
    """书籍快照数据访问对象"""

    def __init__(self):
        super().__init__(BookSnapshot)

    def get_latest_by_book_id(self, db: Session, novel_id: int) -> Optional[BookSnapshot]:
        """获取书籍最新快照"""
        return db.scalar(
            select(BookSnapshot)
            .where(BookSnapshot.novel_id == novel_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(1)
        )

    def get_trend_by_book_id(
            self,
            db: Session,
            novel_id: int,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            limit: int = 30
    ) -> List[BookSnapshot]:
        """获取书籍趋势数据"""
        query = select(BookSnapshot).where(BookSnapshot.novel_id == novel_id)

        if start_time:
            query = query.where(BookSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(BookSnapshot.snapshot_time <= end_time)

        result = db.execute(
            query.order_by(desc(BookSnapshot.snapshot_time)).limit(limit)
        )
        return list(result.scalars())

    def _execute_trend_query(
            self,
            db: Session,
            novel_id: int,
            start_time: datetime,
            end_time: datetime,
            time_group: str
    ) -> List[Dict[str, Any]]:
        """
        执行趋势数据查询的通用方法
        
        Args:
            db: 数据库会话
            novel_id: 书籍ID
            start_time: 开始时间
            end_time: 结束时间
            time_group: 时间分组表达式
            
        Returns:
            List[Dict]: 聚合后的趋势数据
        """
        from sqlalchemy import text
        query = text(f"""
            SELECT 
                {time_group} as time_period,
                AVG(favorites) as avg_favorites,
                AVG(clicks) as avg_clicks,
                AVG(comments) as avg_comments,
                AVG(recommendations) as avg_recommendations,
                MAX(favorites) as max_favorites,
                MAX(clicks) as max_clicks,
                MIN(favorites) as min_favorites,
                MIN(clicks) as min_clicks,
                COUNT(*) as snapshot_count,
                MIN(snapshot_time) as period_start,
                MAX(snapshot_time) as period_end
            FROM book_snapshots
            WHERE novel_id = :book_id 
                AND snapshot_time >= :start_time 
                AND snapshot_time <= :end_time
            GROUP BY {time_group}
            ORDER BY period_start DESC
        """)

        result = db.execute(query, {
            "book_id": novel_id,
            "start_time": start_time,
            "end_time": end_time
        })

        trend_data = []
        for row in result:
            trend_data.append({
                "time_period": row.time_period,
                "avg_favorites": round(row.avg_favorites or 0, 2),
                "avg_clicks": round(row.avg_clicks or 0, 2),
                "avg_comments": round(row.avg_comments or 0, 2),
                "avg_recommendations": round(row.avg_recommendations or 0, 2),
                "max_favorites": row.max_favorites or 0,
                "max_clicks": row.max_clicks or 0,
                "min_favorites": row.min_favorites or 0,
                "min_clicks": row.min_clicks or 0,
                "snapshot_count": row.snapshot_count,
                "period_start": row.period_start,
                "period_end": row.period_end
            })

        return trend_data

    def get_hourly_trend_by_book_id(
            self,
            db: Session,
            novel_id: int,
            start_time: datetime,
            end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        按小时获取书籍趋势数据
        
        Args:
            db: 数据库会话
            novel_id: 书籍ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict]: 按小时聚合的趋势数据
        """
        time_group = "strftime('%Y-%m-%d %H', book_snapshots.snapshot_time)"
        return self._execute_trend_query(db, novel_id, start_time, end_time, time_group)

    def get_daily_trend_by_book_id(
            self,
            db: Session,
            novel_id: int,
            start_time: datetime,
            end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        按天获取书籍趋势数据
        
        Args:
            db: 数据库会话
            novel_id: 书籍ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict]: 按天聚合的趋势数据
        """
        time_group = "strftime('%Y-%m-%d', book_snapshots.snapshot_time)"
        return self._execute_trend_query(db, novel_id, start_time, end_time, time_group)

    def get_weekly_trend_by_book_id(
            self,
            db: Session,
            novel_id: int,
            start_time: datetime,
            end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        按周获取书籍趋势数据
        
        Args:
            db: 数据库会话
            novel_id: 书籍ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict]: 按周聚合的趋势数据
        """
        time_group = "strftime('%Y-W%W', book_snapshots.snapshot_time)"
        return self._execute_trend_query(db, novel_id, start_time, end_time, time_group)

    def get_monthly_trend_by_book_id(
            self,
            db: Session,
            novel_id: int,
            start_time: datetime,
            end_time: datetime
    ) -> List[Dict[str, Any]]:
        """
        按月获取书籍趋势数据
        
        Args:
            db: 数据库会话
            novel_id: 书籍ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Dict]: 按月聚合的趋势数据
        """
        time_group = "strftime('%Y-%m', book_snapshots.snapshot_time)"
        return self._execute_trend_query(db, novel_id, start_time, end_time, time_group)

    def get_trend_by_book_id_with_interval(
            self,
            db: Session,
            novel_id: int,
            start_time: datetime,
            end_time: datetime,
            interval: str = "day"
    ) -> List[Dict[str, Any]]:
        """
        按指定时间间隔获取书籍趋势数据（统一入口函数）
        
        Args:
            db: 数据库会话
            novel_id: 书籍ID
            start_time: 开始时间
            end_time: 结束时间
            interval: 时间间隔 ('hour', 'day', 'week', 'month')
            
        Returns:
            List[Dict]: 聚合后的趋势数据
        """
        if interval == "hour":
            return self.get_hourly_trend_by_book_id(db, novel_id, start_time, end_time)
        elif interval == "day":
            return self.get_daily_trend_by_book_id(db, novel_id, start_time, end_time)
        elif interval == "week":
            return self.get_weekly_trend_by_book_id(db, novel_id, start_time, end_time)
        elif interval == "month":
            return self.get_monthly_trend_by_book_id(db, novel_id, start_time, end_time)
        else:
            raise ValueError(f"不支持的时间间隔: {interval}")

    def get_statistics_by_book_id(self, db: Session, novel_id: int) -> Dict[str, Any]:
        """获取书籍统计信息"""
        result = db.execute(
            select(
                func.count(BookSnapshot.id).label("total_snapshots"),
                func.max(BookSnapshot.favorites).label("max_favorites"),
                func.max(BookSnapshot.clicks).label("max_clicks"),
                func.max(BookSnapshot.comments).label("max_comments"),
                func.min(BookSnapshot.snapshot_time).label("first_snapshot_time"),
                func.max(BookSnapshot.snapshot_time).label("last_snapshot_time")
            ).where(BookSnapshot.novel_id == novel_id)
        ).first()

        if result and result.total_snapshots > 0:
            return {
                "total_snapshots": result.total_snapshots or 0,
                "max_favorites": result.max_favorites or 0,
                "max_clicks": result.max_clicks or 0,
                "max_comments": result.max_comments or 0,
                "first_snapshot_time": result.first_snapshot_time,
                "last_snapshot_time": result.last_snapshot_time
            }
        return {}

    def bulk_create(self, db: Session, snapshots: List[Dict[str, Any]]) -> List[BookSnapshot]:
        """批量创建快照"""
        db_objs = [BookSnapshot(**snapshot) for snapshot in snapshots]
        db.add_all(db_objs)
        db.commit()
        return db_objs

    def delete_old_snapshots(self,db: Session,novel_id: int,before_time: datetime,keep_count: int = 100) -> int:
        """删除旧快照，保留指定数量的最新记录"""
        # 获取要保留的快照IDs
        result = db.execute(
            select(BookSnapshot.id)
            .where(BookSnapshot.novel_id == novel_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(keep_count)
        )
        keep_ids = list(result.scalars())

        # 删除旧快照
        deleted = db.execute(
            delete(BookSnapshot)
            .where(
                and_(
                    BookSnapshot.novel_id == novel_id,
                    BookSnapshot.snapshot_time < before_time,
                    ~BookSnapshot.id.in_(keep_ids)
                )
            )
        )
        db.commit()
        return deleted.rowcount
