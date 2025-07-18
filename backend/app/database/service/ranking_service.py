"""
榜单业务逻辑服务 - 集成DAO功能的简化版本
"""
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy import select, and_, desc, func, delete, distinct
from sqlalchemy.orm import Session

from ..db.ranking import Ranking, RankingSnapshot
from ..db.book import Book


class RankingService:
    """榜单业务逻辑服务 - 直接操作数据库"""

    # ==================== 爬虫使用的方法 ====================
    
    def create_or_update_ranking(self, db: Session, ranking_data: Dict[str, Any]) -> Ranking:
        """根据rank_id创建或更新榜单"""
        rank_id = ranking_data.get("rank_id")
        if not rank_id:
            raise ValueError("rank_id is required")
        
        ranking = self.get_ranking_by_rank_id(db, rank_id)
        if ranking:
            return self.update_ranking(db, ranking, ranking_data)
        else:
            return self.create_ranking(db, ranking_data)

    def batch_create_ranking_snapshots(
        self, 
        db: Session, 
        snapshots: List[Dict[str, Any]]
    ) -> List[RankingSnapshot]:
        """批量创建榜单快照"""
        snapshot_objs = [RankingSnapshot(**snapshot) for snapshot in snapshots]
        db.add_all(snapshot_objs)
        db.commit()
        return snapshot_objs

    # ==================== API使用的方法 ====================
    
    def get_ranking_by_id(self, db: Session, ranking_id: int) -> Optional[Ranking]:
        """根据ID获取榜单"""
        return db.get(Ranking, ranking_id)
    
    def get_all_rankings(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """获取所有榜单（API使用）"""
        return self.get_rankings_with_pagination(db, page, size, filters)

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
    
    def get_ranking_detail(
        self, 
        db: Session, 
        ranking_id: int, 
        target_date: Optional[date] = None,
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """获取榜单详情"""
        ranking = self.get_ranking_by_id(db, ranking_id)
        if not ranking:
            return None
        
        # 获取快照数据
        if target_date:
            snapshots = self.get_snapshots_by_ranking_and_date(db, ranking_id, target_date, limit)
        else:
            snapshots = self.get_latest_snapshots_by_ranking_id(db, ranking_id, limit)
        
        # 构造详情数据
        books_data = []
        for snapshot in snapshots:
            # 获取书籍信息
            book = db.get(Book, snapshot.book_id)
            book_data = {
                "book_id": snapshot.book_id,
                "title": book.title if book else "未知书籍",
                "position": snapshot.position,
                "score": snapshot.score,
                "snapshot_time": snapshot.snapshot_time
            }
            books_data.append(book_data)
        
        return {
            "ranking": ranking,
            "books": books_data,
            "snapshot_time": snapshots[0].snapshot_time if snapshots else None,
            "total_books": len(books_data),
            "statistics": self.get_ranking_statistics(db, ranking_id)
        }
    
    def get_ranking_history(
        self, 
        db: Session, 
        ranking_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """获取榜单历史趋势"""
        start_time = None
        end_time = None
        
        if start_date:
            start_time = datetime.combine(start_date, datetime.min.time())
        if end_date:
            end_time = datetime.combine(end_date, datetime.max.time())
        
        trend_data = self.get_ranking_trend(db, ranking_id, start_time, end_time)
        
        return {
            "ranking_id": ranking_id,
            "start_date": start_date,
            "end_date": end_date,
            "trend_data": [
                {"snapshot_time": snapshot_time, "book_count": book_count}
                for snapshot_time, book_count in trend_data
            ]
        }
    
    def compare_rankings(
        self, 
        db: Session, 
        ranking_ids: List[int], 
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """对比多个榜单"""
        if len(ranking_ids) < 2:
            raise ValueError("至少需要2个榜单进行对比")
        
        # 获取榜单基本信息
        rankings = [self.get_ranking_by_id(db, rid) for rid in ranking_ids]
        rankings = [r for r in rankings if r is not None]
        
        if len(rankings) != len(ranking_ids):
            raise ValueError("部分榜单不存在")
        
        # 获取对比数据
        comparison_data = {}
        for ranking_id in ranking_ids:
            if target_date:
                snapshots = self.get_snapshots_by_ranking_and_date(db, ranking_id, target_date)
            else:
                snapshots = self.get_latest_snapshots_by_ranking_id(db, ranking_id)
            comparison_data[ranking_id] = snapshots
        
        # 分析共同书籍
        all_books = {}  # book_id -> book_info
        ranking_books = {}  # ranking_id -> set of book_ids
        
        for ranking_id, snapshots in comparison_data.items():
            book_ids = set()
            for snapshot in snapshots:
                book_ids.add(snapshot.book_id)
                # 获取书籍信息
                book = db.get(Book, snapshot.book_id)
                all_books[snapshot.book_id] = {
                    "id": book.id if book else None,
                    "book_id": snapshot.book_id,
                    "title": book.title if book else "未知书籍"
                }
            ranking_books[ranking_id] = book_ids
        
        # 找出共同书籍
        common_book_ids = set.intersection(*ranking_books.values()) if ranking_books else set()
        
        return {
            "rankings": [
                {
                    "ranking_id": r.id,
                    "name": r.name,
                    "page_id": r.page_id
                } for r in rankings
            ],
            "comparison_date": target_date or date.today(),
            "ranking_data": {
                ranking_id: [
                    {
                        "book_id": s.book_id,
                        "title": all_books.get(s.book_id, {}).get("title", "未知书籍"),
                        "position": s.position,
                        "score": s.score
                    } for s in snapshots
                ] for ranking_id, snapshots in comparison_data.items()
            },
            "common_books": [
                all_books[book_id] for book_id in common_book_ids
            ],
            "stats": {
                "total_unique_books": len(all_books),
                "common_books_count": len(common_book_ids)
            }
        }
    
    def get_book_ranking_history_with_details(
        self, 
        db: Session, 
        book_id: int, 
        ranking_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取书籍在榜单中的排名历史（包含详细信息）"""
        start_time = datetime.now() - timedelta(days=days)
        
        snapshots = self.get_book_ranking_history(db, book_id, ranking_id, start_time)
        
        history_data = []
        for snapshot in snapshots:
            # 获取榜单信息
            ranking = self.get_ranking_by_id(db, snapshot.ranking_id)
            history_data.append({
                "ranking_id": snapshot.ranking_id,
                "ranking_name": ranking.name if ranking else "未知榜单",
                "position": snapshot.position,
                "score": snapshot.score,
                "snapshot_time": snapshot.snapshot_time
            })
        
        return history_data

    # ==================== 内部依赖方法 ====================
    
    def get_ranking_by_rank_id(self, db: Session, rank_id: int) -> Optional[Ranking]:
        """根据rank_id获取榜单"""
        return db.scalar(select(Ranking).where(Ranking.rank_id == rank_id))
    
    def create_ranking(self, db: Session, ranking_data: Dict[str, Any]) -> Ranking:
        """创建榜单"""
        ranking = Ranking(**ranking_data)
        db.add(ranking)
        db.commit()
        db.refresh(ranking)
        return ranking
    
    def update_ranking(self, db: Session, ranking: Ranking, ranking_data: Dict[str, Any]) -> Ranking:
        """更新榜单"""
        for key, value in ranking_data.items():
            if hasattr(ranking, key):
                setattr(ranking, key, value)
        ranking.updated_at = datetime.now()
        db.add(ranking)
        db.commit()
        db.refresh(ranking)
        return ranking

    def get_rankings_with_pagination(
        self, 
        db: Session, 
        page: int = 1, 
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分页获取榜单列表"""
        skip = (page - 1) * size
        
        # 构建查询
        query = select(Ranking)
        count_query = select(func.count(Ranking.id))
        
        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(Ranking, key):
                    query = query.where(getattr(Ranking, key) == value)
                    count_query = count_query.where(getattr(Ranking, key) == value)
        
        # 获取数据
        rankings = list(db.execute(
            query.order_by(desc(Ranking.created_at))
            .offset(skip)
            .limit(size)
        ).scalars())
        
        total = db.scalar(count_query)
        
        return {
            "rankings": rankings,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size if total > 0 else 0
        }
    
    def get_latest_snapshots_by_ranking_id(
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
        
        result = db.execute(
            select(RankingSnapshot)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time == latest_time
                )
            )
            .order_by(RankingSnapshot.position)
            .limit(limit)
        )
        return list(result.scalars())
    
    def get_snapshots_by_ranking_and_date(
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
        
        result = db.execute(
            select(RankingSnapshot)
            .where(
                and_(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time == target_time
                )
            )
            .order_by(RankingSnapshot.position)
            .limit(limit)
        )
        return list(result.scalars())
    
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
        
        result = db.execute(
            query.order_by(desc(RankingSnapshot.snapshot_time)).limit(limit)
        )
        return list(result.scalars())
    
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