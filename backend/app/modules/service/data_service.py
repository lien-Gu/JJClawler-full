"""
综合数据服务
整合书籍和榜单数据，提供复合查询功能
"""
from datetime import datetime, timedelta, date
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from .book_service import BookService
from .ranking_service import RankingService


class DataService:
    """综合数据服务"""
    
    def __init__(self):
        self.book_service = BookService()
        self.ranking_service = RankingService()
    
    def get_dashboard_overview(self, db: Session) -> Dict[str, Any]:
        """获取仪表盘概览数据"""
        # 获取总体统计
        total_books = self.book_service.book_dao.count(db)
        total_rankings = self.ranking_service.ranking_dao.count(db)
        
        # 获取最近活跃的书籍（有最新快照的）
        recent_time = datetime.now() - timedelta(hours=24)
        active_books = self.book_service.book_dao.get_multi(
            db, limit=10, 
            filters={"updated_at": recent_time}  # 这里需要根据实际查询逻辑调整
        )
        
        # 获取最新的榜单快照统计
        recent_snapshots = {}
        rankings = self.ranking_service.ranking_dao.get_multi(db, limit=5)
        for ranking in rankings:
            latest_snapshots = self.ranking_service.ranking_snapshot_dao.get_latest_by_ranking_id(
                db, ranking.id, limit=10
            )
            recent_snapshots[ranking.name] = len(latest_snapshots)
        
        return {
            "total_books": total_books,
            "total_rankings": total_rankings,
            "active_books_24h": len(active_books),
            "recent_ranking_data": recent_snapshots,
            "last_updated": datetime.now()
        }
    
    def search_comprehensive(
        self, 
        db: Session, 
        keyword: str, 
        search_type: str = "all",  # "books", "rankings", "all"
        page: int = 1,
        size: int = 20
    ) -> Dict[str, Any]:
        """综合搜索"""
        result = {
            "keyword": keyword,
            "search_type": search_type,
            "books": [],
            "rankings": []
        }
        
        if search_type in ["books", "all"]:
            # 搜索书籍
            books = self.book_service.search_books(db, keyword, page, size)
            result["books"] = books
        
        if search_type in ["rankings", "all"]:
            # 搜索榜单（按名称）
            rankings = self.ranking_service.ranking_dao.get_multi(
                db, limit=size,
                filters={}  # 这里需要实现name模糊查询，当前BaseDAO不支持LIKE
            )
            # 简单过滤包含关键词的榜单
            filtered_rankings = [
                r for r in rankings 
                if keyword.lower() in r.name.lower()
            ]
            result["rankings"] = filtered_rankings[:size]
        
        return result
    
    def get_trending_books(
        self, 
        db: Session, 
        days: int = 7, 
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """获取趋势书籍（基于快照数据增长）"""
        # 这是一个复杂查询的示例，实际实现可能需要原生SQL
        # 目前返回最近有快照的书籍作为示例
        
        recent_time = datetime.now() - timedelta(days=days)
        books_with_snapshots = []
        
        # 获取最近的书籍
        books = self.book_service.book_dao.get_multi(db, limit=limit * 2)
        
        for book in books:
            snapshots = self.book_service.book_snapshot_dao.get_trend_by_book_id(
                db, book.id, start_time=recent_time, limit=2
            )
            if len(snapshots) >= 2:
                # 计算增长率
                latest = snapshots[0]
                previous = snapshots[-1]
                
                favorites_growth = 0
                clicks_growth = 0
                
                if previous.favorites > 0:
                    favorites_growth = ((latest.favorites - previous.favorites) / previous.favorites) * 100
                if previous.clicks > 0:
                    clicks_growth = ((latest.clicks - previous.clicks) / previous.clicks) * 100
                
                books_with_snapshots.append({
                    "book": book,
                    "latest_snapshot": latest,
                    "favorites_growth": favorites_growth,
                    "clicks_growth": clicks_growth,
                    "total_growth": (favorites_growth + clicks_growth) / 2
                })
        
        # 按总增长率排序
        books_with_snapshots.sort(key=lambda x: x["total_growth"], reverse=True)
        
        return books_with_snapshots[:limit]
    
    def get_ranking_insights(
        self, 
        db: Session, 
        ranking_id: int, 
        days: int = 30
    ) -> Dict[str, Any]:
        """获取榜单洞察数据"""
        ranking = self.ranking_service.get_ranking_by_id(db, ranking_id)
        if not ranking:
            return {}
        
        start_time = datetime.now() - timedelta(days=days)
        
        # 获取榜单基本统计
        stats = self.ranking_service.get_ranking_statistics(db, ranking_id)
        
        # 获取趋势数据
        trend_data = self.ranking_service.ranking_snapshot_dao.get_ranking_trend(
            db, ranking_id, start_time
        )
        
        # 获取最新快照
        latest_snapshots = self.ranking_service.ranking_snapshot_dao.get_latest_by_ranking_id(
            db, ranking_id, limit=50
        )
        
        # 分析榜单稳定性（前10名的变化频率）
        stability_score = 0
        if len(latest_snapshots) >= 10:
            top_10_books = {s.book_id for s in latest_snapshots[:10]}
            
            # 获取一周前的快照进行对比
            week_ago = datetime.now() - timedelta(days=7)
            old_snapshots = self.ranking_service.ranking_snapshot_dao.get_by_ranking_and_date(
                db, ranking_id, week_ago.date(), limit=10
            )
            
            if old_snapshots:
                old_top_10_books = {s.book_id for s in old_snapshots[:10]}
                common_books = len(top_10_books.intersection(old_top_10_books))
                stability_score = (common_books / 10) * 100
        
        return {
            "ranking": ranking,
            "statistics": stats,
            "trend_data": [
                {"date": snapshot_time, "book_count": book_count}
                for snapshot_time, book_count in trend_data
            ],
            "current_books_count": len(latest_snapshots),
            "stability_score": stability_score,
            "insights": {
                "most_stable_period": "需要更复杂的算法分析",
                "growth_rate": "需要计算增长率",
                "peak_activity": "需要分析峰值时间"
            }
        }
    
    def get_book_comprehensive_info(
        self, 
        db: Session, 
        book_id: int
    ) -> Optional[Dict[str, Any]]:
        """获取书籍的综合信息"""
        # 获取书籍基本信息和快照
        book_detail = self.book_service.get_book_detail_with_latest_snapshot(db, book_id)
        if not book_detail:
            return None
        
        # 获取排名历史
        ranking_history = self.ranking_service.get_book_ranking_history(db, book_id)
        
        # 获取趋势数据
        trend_data = self.book_service.get_book_trend(db, book_id, days=30)
        
        return {
            **book_detail,
            "ranking_history": ranking_history,
            "trend_data": trend_data,
            "performance_analysis": {
                "total_rankings": len(set(h["ranking_id"] for h in ranking_history)),
                "best_position": min([h["position"] for h in ranking_history]) if ranking_history else None,
                "average_position": sum([h["position"] for h in ranking_history]) / len(ranking_history) if ranking_history else None
            }
        }
    
    def get_data_quality_report(self, db: Session) -> Dict[str, Any]:
        """获取数据质量报告"""
        # 检查数据完整性和质量
        total_books = self.book_service.book_dao.count(db)
        books_with_snapshots = self.book_service.book_snapshot_dao.count(db)
        
        total_rankings = self.ranking_service.ranking_dao.count(db)
        rankings_with_snapshots = self.ranking_service.ranking_snapshot_dao.count(db)
        
        # 检查最近数据更新情况
        recent_time = datetime.now() - timedelta(hours=24)
        recent_book_snapshots = self.book_service.book_snapshot_dao.count(
            db, filters={}  # 需要支持时间范围过滤
        )
        recent_ranking_snapshots = self.ranking_service.ranking_snapshot_dao.count(
            db, filters={}  # 需要支持时间范围过滤
        )
        
        return {
            "data_overview": {
                "total_books": total_books,
                "books_with_snapshots": books_with_snapshots,
                "total_rankings": total_rankings,
                "rankings_with_snapshots": rankings_with_snapshots
            },
            "data_freshness": {
                "recent_book_snapshots_24h": recent_book_snapshots,
                "recent_ranking_snapshots_24h": recent_ranking_snapshots
            },
            "data_quality_score": {
                "book_coverage": (books_with_snapshots / total_books * 100) if total_books > 0 else 0,
                "ranking_coverage": (rankings_with_snapshots / total_rankings * 100) if total_rankings > 0 else 0
            },
            "recommendations": [
                "定期检查数据完整性",
                "监控爬虫运行状态",
                "清理过期数据"
            ],
            "generated_at": datetime.now()
        }