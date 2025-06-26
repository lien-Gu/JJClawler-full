"""
Ranking业务服务

封装Ranking相关的业务逻辑
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from app.modules.base import BaseService, handle_service_error
from app.modules.dao import RankingDAO, BookDAO
from app.modules.models import (
    RankingInfo, BookInRanking, RankingSnapshotSummary,
    Ranking, RankingSnapshot
)


class RankingService(BaseService):
    """Ranking业务服务类"""
    
    def __init__(self):
        super().__init__()
        self.ranking_dao = RankingDAO()
        self.book_dao = BookDAO()
        self.add_dao(self.ranking_dao)
        self.add_dao(self.book_dao)
    
    def get_total_rankings(self) -> int:
        """获取榜单总数"""
        try:
            return self.ranking_dao.count_rankings()
        except Exception as e:
            return handle_service_error(self.logger, "获取榜单总数", e, 0)
    
    def get_ranking_info(self, ranking_id: str) -> Optional[RankingInfo]:
        """获取榜单信息"""
        ranking = self.ranking_dao.get_by_id(ranking_id)
        if not ranking:
            return None
        
        return RankingInfo(
            id=ranking.id,
            ranking_id=ranking.ranking_id,
            name=ranking.name,
            channel=ranking.channel,
            frequency=ranking.frequency,
            update_interval=ranking.update_interval,
            parent_id=ranking.parent_id
        )
    
    def get_all_rankings(self) -> List[RankingInfo]:
        """获取所有榜单配置"""
        rankings = self.ranking_dao.get_all()
        if not rankings:
            logger.info("数据库中暂无榜单数据，需要先执行爬虫任务")
            return []
            
        return [
            RankingInfo(
                id=ranking.id,
                ranking_id=ranking.ranking_id,
                name=ranking.name,
                channel=ranking.channel,
                frequency=ranking.frequency,
                update_interval=ranking.update_interval,
                parent_id=ranking.parent_id
            )
            for ranking in rankings
        ]
    
    def get_ranking_books(
        self, 
        ranking_id: str, 
        snapshot_time: Optional[datetime] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[Optional[RankingInfo], List[BookInRanking], Optional[datetime]]:
        """获取榜单书籍列表"""
        # 获取榜单信息
        ranking_info = self.get_ranking_info(ranking_id)
        if not ranking_info:
            return None, [], None
        
        # 获取榜单书籍数据
        results, actual_snapshot_time = self.ranking_dao.get_ranking_books(
            ranking_id, snapshot_time, limit, offset
        )
        
        if not results:
            logger.info(f"榜单 {ranking_id} 暂无数据，可能需要先执行爬虫任务")
            return ranking_info, [], actual_snapshot_time
        
        # 转换为BookInRanking
        books_in_ranking = []
        for ranking_snapshot, book in results:
            # TODO: 计算排名变化
            position_change = self._calculate_position_change(
                ranking_id, book.book_id, ranking_snapshot.position, actual_snapshot_time
            )
            
            book_in_ranking = BookInRanking(
                book_id=book.book_id,
                title=book.title,
                author_name=book.author_name,
                author_id=book.author_id,
                novel_class=book.novel_class,
                tags=book.tags,
                position=ranking_snapshot.position,
                position_change=position_change
            )
            books_in_ranking.append(book_in_ranking)
        
        return ranking_info, books_in_ranking, actual_snapshot_time
    
    def get_ranking_history_summary(
        self, 
        ranking_id: str, 
        days: int = 7
    ) -> Tuple[Optional[RankingInfo], List[RankingSnapshotSummary]]:
        """获取榜单历史摘要"""
        # 获取榜单信息
        ranking_info = self.get_ranking_info(ranking_id)
        if not ranking_info:
            return None, []
        
        # 获取历史摘要数据
        summary_data = self.ranking_dao.get_ranking_history_summary(ranking_id, days)
        
        summaries = []
        for snapshot_time, total_books, top_book_title in summary_data:
            summaries.append(RankingSnapshotSummary(
                snapshot_time=snapshot_time,
                total_books=total_books,
                top_book_title=top_book_title
            ))
        
        return ranking_info, summaries
    
    def create_ranking_snapshot(self, snapshot_data: Dict[str, Any]) -> RankingSnapshot:
        """创建榜单快照"""
        return self.ranking_dao.create_snapshot(snapshot_data)
    
    def batch_create_ranking_snapshots(self, snapshots_data: List[Dict[str, Any]]) -> List[RankingSnapshot]:
        """批量创建榜单快照"""
        return self.ranking_dao.batch_create_snapshots(snapshots_data)
    
    def create_or_update_ranking(self, ranking_data: Dict[str, Any]) -> Ranking:
        """创建或更新榜单配置"""
        ranking_id = ranking_data["ranking_id"]
        existing_ranking = self.ranking_dao.get_by_id(ranking_id)
        
        if existing_ranking:
            return self.ranking_dao.update(ranking_id, ranking_data)
        else:
            return self.ranking_dao.create(ranking_data)
    
    def _calculate_position_change(
        self, 
        ranking_id: str, 
        book_id: str, 
        current_position: int,
        current_time: datetime
    ) -> Optional[str]:
        """计算排名变化"""
        # 获取前一次快照时间（简化实现，实际应该获取前一个快照）
        previous_time = current_time - timedelta(hours=1)
        
        try:
            # 查询前一次排名
            previous_snapshots = self.ranking_dao.get_snapshots_by_date_range(
                ranking_id, previous_time - timedelta(minutes=30), previous_time + timedelta(minutes=30)
            )
            
            previous_position = None
            for snapshot in previous_snapshots:
                if snapshot.book_id == book_id:
                    previous_position = snapshot.position
                    break
            
            if previous_position is None:
                return "new"  # 新上榜
            
            position_diff = previous_position - current_position
            if position_diff > 0:
                return f"+{position_diff}"  # 上升
            elif position_diff < 0:
                return f"{position_diff}"   # 下降
            else:
                return "="  # 无变化
                
        except Exception as e:
            logger.warning(f"计算排名变化失败: {e}")
            return None
    
    def get_ranking_trend_data(
        self,
        ranking_id: str,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """获取榜单趋势数据"""
        start_date = datetime.now() - timedelta(days=days)
        snapshots = self.ranking_dao.get_snapshots_by_date_range(ranking_id, start_date)
        
        # 按日期分组统计
        daily_stats = {}
        for snapshot in snapshots:
            date_key = snapshot.snapshot_time.date().isoformat()
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    "date": date_key,
                    "total_books": 0,
                    "books": set()
                }
            daily_stats[date_key]["books"].add(snapshot.book_id)
        
        # 转换为列表并计算统计
        trend_data = []
        for date_str, stats in sorted(daily_stats.items()):
            trend_data.append({
                "date": date_str,
                "total_books": len(stats["books"]),
                "snapshot_count": len([s for s in snapshots if s.snapshot_time.date().isoformat() == date_str])
            })
        
        return trend_data