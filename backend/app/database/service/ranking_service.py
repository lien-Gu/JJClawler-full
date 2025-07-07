"""
榜单业务逻辑服务
"""
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from ..dao.ranking_dao import RankingDAO, RankingSnapshotDAO
from ..dao.book_dao import BookDAO
from ..db.ranking import Ranking, RankingSnapshot


class RankingService:
    """榜单业务逻辑服务"""
    
    def __init__(self):
        self.ranking_dao = RankingDAO()
        self.ranking_snapshot_dao = RankingSnapshotDAO()
        self.book_dao = BookDAO()
    
    def get_ranking_by_id(self, db: Session, ranking_id: int) -> Optional[Ranking]:
        """根据ID获取榜单"""
        return self.ranking_dao.get_by_id(db, ranking_id)
    
    def get_ranking_by_rank_id(self, db: Session, rank_id: int) -> Optional[Ranking]:
        """根据rank_id获取榜单"""
        return self.ranking_dao.get_by_rank_id(db, rank_id)
    
    def get_rankings_by_page_id(self, db: Session, page_id: str) -> List[Ranking]:
        """根据页面ID获取榜单列表"""
        return self.ranking_dao.get_by_page_id(db, page_id)
    
    def get_rankings_by_group_type(self, db: Session, group_type: str) -> List[Ranking]:
        """根据分组类型获取榜单"""
        return self.ranking_dao.get_by_group_type(db, group_type)
    
    def get_all_rankings(
        self, 
        db: Session, 
        page: int = 1, 
        size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """分页获取所有榜单"""
        skip = (page - 1) * size
        
        rankings = self.ranking_dao.get_multi(db, skip=skip, limit=size, filters=filters)
        total = self.ranking_dao.count(db, filters=filters)
        
        return {
            "rankings": rankings,
            "total": total,
            "page": page,
            "size": size,
            "total_pages": (total + size - 1) // size
        }
    
    def get_ranking_detail(
        self, 
        db: Session, 
        ranking_id: int, 
        target_date: Optional[date] = None,
        limit: int = 50
    ) -> Optional[Dict[str, Any]]:
        """获取榜单详情"""
        ranking = self.ranking_dao.get_by_id(db, ranking_id)
        if not ranking:
            return None
        
        if target_date:
            snapshots = self.ranking_snapshot_dao.get_by_ranking_and_date(
                db, ranking_id, target_date, limit
            )
        else:
            snapshots = self.ranking_snapshot_dao.get_latest_by_ranking_id(
                db, ranking_id, limit
            )
        
        # 构造详情数据
        books_data = []
        for snapshot in snapshots:
            book_data = {
                "book_id": snapshot.book.id,
                "title": snapshot.book.title,
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
            "statistics": self.ranking_snapshot_dao.get_ranking_statistics(db, ranking_id)
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
        
        trend_data = self.ranking_snapshot_dao.get_ranking_trend(
            db, ranking_id, start_time, end_time
        )
        
        return {
            "ranking_id": ranking_id,
            "start_date": start_date,
            "end_date": end_date,
            "trend_data": [
                {"snapshot_time": snapshot_time, "book_count": book_count}
                for snapshot_time, book_count in trend_data
            ]
        }
    
    def get_book_ranking_history(
        self, 
        db: Session, 
        book_id: int, 
        ranking_id: Optional[int] = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """获取书籍在榜单中的排名历史"""
        start_time = datetime.now() - timedelta(days=days)
        
        snapshots = self.ranking_snapshot_dao.get_book_ranking_history(
            db, book_id, ranking_id, start_time
        )
        
        history_data = []
        for snapshot in snapshots:
            history_data.append({
                "ranking_id": snapshot.ranking.id,
                "ranking_name": snapshot.ranking.rank_name,
                "position": snapshot.position,
                "score": snapshot.score,
                "snapshot_time": snapshot.snapshot_time
            })
        
        return history_data
    
    def create_or_update_ranking(self, db: Session, ranking_data: Dict[str, Any]) -> Ranking:
        """创建或更新榜单"""
        return self.ranking_dao.create_or_update_by_rank_id(db, ranking_data)
    
    def create_ranking_snapshot(
        self, 
        db: Session, 
        snapshot_data: Dict[str, Any]
    ) -> RankingSnapshot:
        """创建榜单快照"""
        return self.ranking_snapshot_dao.create(db, snapshot_data)
    
    def batch_create_ranking_snapshots(
        self, 
        db: Session, 
        snapshots: List[Dict[str, Any]]
    ) -> List[RankingSnapshot]:
        """批量创建榜单快照"""
        return self.ranking_snapshot_dao.bulk_create(db, snapshots)
    
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
        rankings = [self.ranking_dao.get_by_id(db, rid) for rid in ranking_ids]
        rankings = [r for r in rankings if r is not None]
        
        if len(rankings) != len(ranking_ids):
            raise ValueError("部分榜单不存在")
        
        # 获取对比数据
        comparison_data = self.ranking_snapshot_dao.get_books_comparison(
            db, ranking_ids, target_date
        )
        
        # 分析共同书籍
        all_books = {}  # book_id -> book_info
        ranking_books = {}  # ranking_id -> set of book_ids
        
        for ranking_id, snapshots in comparison_data.items():
            book_ids = set()
            for snapshot in snapshots:
                book_ids.add(snapshot.book_id)
                all_books[snapshot.book_id] = {
                    "id": snapshot.book.id,
                    "title": snapshot.book.title
                }
            ranking_books[ranking_id] = book_ids
        
        # 找出共同书籍
        common_book_ids = set.intersection(*ranking_books.values()) if ranking_books else set()
        
        return {
            "rankings": [
                {
                    "ranking_id": r.id,
                    "name": r.rank_name,
                    "page_id": r.page_id
                } for r in rankings
            ],
            "comparison_date": target_date or date.today(),
            "ranking_data": {
                ranking_id: [
                    {
                        "book_id": s.book_id,
                        "title": s.book.title,
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
    
    def cleanup_old_ranking_snapshots(
        self, 
        db: Session, 
        ranking_id: int, 
        keep_days: int = 30
    ) -> int:
        """清理旧的榜单快照"""
        cutoff_time = datetime.now() - timedelta(days=keep_days)
        return self.ranking_snapshot_dao.delete_old_snapshots(
            db, ranking_id, cutoff_time, keep_days
        )
    
    def get_ranking_statistics(self, db: Session, ranking_id: int) -> Dict[str, Any]:
        """获取榜单统计信息"""
        return self.ranking_snapshot_dao.get_ranking_statistics(db, ranking_id)