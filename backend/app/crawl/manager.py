"""
爬虫管理器 - 简化版本
"""
import logging
from typing import Dict, List, Any, Union
from datetime import datetime

from .crawl_flow import CrawlFlow
from app.config import settings
from app.database.connection import get_db
from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService
from app.crawl.parser import DataType


class CrawlerManager:
    """爬虫管理器，基于流程设计"""
    
    def __init__(self, request_delay: float = None):
        """
        初始化爬虫管理器
        
        Args:
            request_delay: 请求间隔时间（秒）
        """
        self.request_delay = request_delay or settings.crawler.request_delay
        self.flow = CrawlFlow()
        
        # 初始化数据服务
        self.book_service = BookService()
        self.ranking_service = RankingService()
        
        # 配置日志
        self.logger = logging.getLogger(__name__)
    
    async def crawl(self, task_ids: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        执行爬取任务并存储到数据库
        
        Args:
            task_ids: 任务ID或任务ID列表
            
        Returns:
            爬取结果列表
        """
        # 执行爬取
        if isinstance(task_ids, str):
            results = [await self.flow.execute_crawl_task(task_ids)]
        else:
            results = await self.flow.execute_multiple_tasks(task_ids)
        
        # 存储爬取结果到数据库
        await self._save_crawl_results(results)
        
        return results

    
    async def crawl_all_tasks(self) -> List[Dict[str, Any]]:
        """爬取所有配置的任务"""
        from .base import CrawlConfig
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        task_ids = [task["id"] for task in all_tasks]
        return await self.crawl(task_ids)
    
    async def crawl_tasks_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据分类爬取任务"""
        from .base import CrawlConfig
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        
        matching_tasks = []
        for task in all_tasks:
            task_id = task["id"]
            if task_id == category or task_id.startswith(f"{category}."):
                matching_tasks.append(task_id)
        
        return await self.crawl(matching_tasks) if matching_tasks else []
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.flow.get_stats()
    
    def get_data(self) -> Dict[str, List]:
        """获取爬取数据"""
        return self.flow.get_all_data()
    
    async def close(self):
        """关闭连接"""
        await self.flow.close()
    
    async def _save_crawl_results(self, results: List[Dict[str, Any]]) -> None:
        """
        保存爬取结果到数据库
        
        Args:
            results: 爬取结果列表
        """
        for result in results:
            if not result.get("success", False):
                continue
                
            try:
                # 使用数据库会话上下文管理器
                for db in get_db():
                    try:
                        # 保存榜单数据
                        if "rankings" in result:
                            await self._save_rankings(db, result["rankings"], result.get("timestamp"))
                        
                        # 保存书籍数据
                        if "books" in result:
                            await self._save_books(db, result["books"], result.get("timestamp"))
                        
                        # 提交事务
                        db.commit()
                        
                        self.logger.info(f"成功保存任务 {result.get('task_id')} 的爬取数据")
                        
                    except Exception as e:
                        # 回滚事务
                        db.rollback()
                        self.logger.error(f"保存任务 {result.get('task_id')} 数据失败: {e}")
                        raise
                    
                    # 只循环一次，使用 break 退出
                    break
                    
            except Exception as e:
                self.logger.error(f"处理任务 {result.get('task_id')} 结果时出错: {e}")
    
    async def _save_rankings(self, db, rankings_data: List[Dict[str, Any]], timestamp: float = None) -> None:
        """
        保存榜单数据
        
        Args:
            db: 数据库会话
            rankings_data: 榜单数据列表
            timestamp: 时间戳
        """
        snapshot_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        
        for ranking_data in rankings_data:
            try:
                # 创建或更新榜单
                ranking_info = {
                    "rank_id": ranking_data.get("rank_id"),
                    "rank_name": ranking_data.get("rank_name", ""),
                    "page_id": ranking_data.get("page_id", ""),
                    "rank_group_type": ranking_data.get("rank_group_type", "")
                }
                
                ranking = self.ranking_service.create_or_update_ranking(db, ranking_info)
                
                # 保存榜单快照 - 书籍排名信息
                books = ranking_data.get("books", [])
                ranking_snapshots = []
                
                for book in books:
                    # 先确保书籍存在
                    book_info = {
                        "novel_id": book.get("book_id"),
                        "title": book.get("title", "")
                    }
                    book_obj = self.book_service.create_or_update_book(db, book_info)
                    
                    # 创建榜单快照
                    snapshot_data = {
                        "ranking_id": ranking.id,
                        "book_id": book_obj.id,
                        "position": book.get("position", 0),
                        "score": book.get("score", 0.0),
                        "snapshot_time": snapshot_time
                    }
                    ranking_snapshots.append(snapshot_data)
                
                # 批量创建榜单快照
                if ranking_snapshots:
                    self.ranking_service.batch_create_ranking_snapshots(db, ranking_snapshots)
                    
                self.logger.debug(f"保存榜单 {ranking_data.get('rank_name')} 数据，包含 {len(books)} 本书")
                
            except Exception as e:
                self.logger.error(f"保存榜单 {ranking_data.get('rank_name')} 数据失败: {e}")
                raise
    
    async def _save_books(self, db, books_data: List[Dict[str, Any]], timestamp: float = None) -> None:
        """
        保存书籍数据
        
        Args:
            db: 数据库会话
            books_data: 书籍数据列表
            timestamp: 时间戳
        """
        snapshot_time = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
        book_snapshots = []
        
        for book_data in books_data:
            try:
                # 创建或更新书籍基本信息
                book_info = {
                    "novel_id": book_data.get("novel_id"),
                    "title": book_data.get("title", "")
                }
                
                book = self.book_service.create_or_update_book(db, book_info)
                
                # 创建书籍快照数据（动态统计信息）
                snapshot_data = {
                    "novel_id": book.id,  # 外键引用书籍ID
                    "clicks": book_data.get("clicks", 0),
                    "favorites": book_data.get("favorites", 0),
                    "comments": book_data.get("comments", 0),
                    "recommendations": book_data.get("recommendations", 0),
                    "word_count": book_data.get("word_count"),
                    "status": book_data.get("status"),
                    "snapshot_time": snapshot_time
                }
                book_snapshots.append(snapshot_data)
                
            except Exception as e:
                self.logger.error(f"处理书籍 {book_data.get('title')} 数据失败: {e}")
                continue
        
        # 批量创建书籍快照
        if book_snapshots:
            self.book_service.batch_create_book_snapshots(db, book_snapshots)
            self.logger.debug(f"保存 {len(book_snapshots)} 个书籍快照数据")