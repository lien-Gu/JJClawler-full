"""
书籍相关DAO
"""
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import select, and_, desc, func
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

    def search_by_author(self, db: Session, author: str, limit: int = 20) -> List[Book]:
        """根据作者搜索书籍"""
        result = db.execute(
            select(Book)
            .where(Book.author.like(f"%{author}%"))
            .limit(limit)
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

    def get_latest_by_book_id(self, db: Session, book_id: int) -> Optional[BookSnapshot]:
        """获取书籍最新快照"""
        return db.scalar(
            select(BookSnapshot)
            .where(BookSnapshot.book_id == book_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(1)
        )

    def get_trend_by_book_id(
            self,
            db: Session,
            book_id: int,
            start_time: Optional[datetime] = None,
            end_time: Optional[datetime] = None,
            limit: int = 30
    ) -> List[BookSnapshot]:
        """获取书籍趋势数据"""
        query = select(BookSnapshot).where(BookSnapshot.book_id == book_id)

        if start_time:
            query = query.where(BookSnapshot.snapshot_time >= start_time)
        if end_time:
            query = query.where(BookSnapshot.snapshot_time <= end_time)

        result = db.execute(
            query.order_by(desc(BookSnapshot.snapshot_time)).limit(limit)
        )
        return list(result.scalars())

    def get_statistics_by_book_id(self, db: Session, book_id: int) -> Dict[str, Any]:
        """获取书籍统计信息"""
        result = db.execute(
            select(
                func.count(BookSnapshot.id).label("total_snapshots"),
                func.max(BookSnapshot.favorites).label("max_favorites"),
                func.max(BookSnapshot.clicks).label("max_clicks"),
                func.max(BookSnapshot.comments).label("max_comments"),
                func.min(BookSnapshot.snapshot_time).label("first_snapshot_time"),
                func.max(BookSnapshot.snapshot_time).label("last_snapshot_time")
            ).where(BookSnapshot.book_id == book_id)
        ).first()

        if result:
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

    def delete_old_snapshots(self,db: Session,book_id: int,before_time: datetime,keep_count: int = 100) -> int:
        """删除旧快照，保留指定数量的最新记录"""
        # 获取要保留的快照IDs
        result = db.execute(
            select(BookSnapshot.id)
            .where(BookSnapshot.book_id == book_id)
            .order_by(desc(BookSnapshot.snapshot_time))
            .limit(keep_count)
        )
        keep_ids = list(result.scalars())

        # 删除旧快照
        deleted = db.execute(
            delete(BookSnapshot)
            .where(
                and_(
                    BookSnapshot.book_id == book_id,
                    BookSnapshot.snapshot_time < before_time,
                    ~BookSnapshot.id.in_(keep_ids)
                )
            )
        )
        db.commit()
        return deleted.rowcount
