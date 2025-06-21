"""
爬虫服务模块 - 爬虫与数据库集成

将爬虫模块与数据库Service层集成，提供完整的数据抓取到存储流程：
- 数据抓取
- 数据清洗和验证
- 数据库存储
- 重复数据处理
- 统计信息生成

设计原则：
1. 事务安全：确保数据存储的原子性
2. 错误处理：完整的异常处理和回滚机制
3. 性能优化：批量操作和索引优化
4. 数据完整性：重复数据检测和更新策略
"""

import logging
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from contextlib import asynccontextmanager

from app.modules.crawler import JiaziCrawler, PageCrawler
from app.modules.service import BookService, RankingService
from app.modules.models import Book, BookSnapshot, Ranking, RankingSnapshot
from app.modules.database import get_session_sync

# 配置日志
logger = logging.getLogger(__name__)


class CrawlerService:
    """
    爬虫服务类
    
    集成爬虫功能和数据存储，提供完整的数据采集服务：
    - 协调爬虫模块和Service层
    - 管理数据存储事务
    - 处理数据冲突和更新
    - 生成采集统计报告
    """
    
    def __init__(self):
        """初始化爬虫服务"""
        self.jiazi_crawler = None
        self.page_crawler = None
        self.book_service = BookService()
        self.ranking_service = RankingService()
    
    @asynccontextmanager
    async def _get_jiazi_crawler(self):
        """获取甲子榜爬虫的上下文管理器"""
        self.jiazi_crawler = JiaziCrawler()
        try:
            yield self.jiazi_crawler
        finally:
            await self.jiazi_crawler.close()
            self.jiazi_crawler = None
    
    @asynccontextmanager
    async def _get_page_crawler(self):
        """获取分类页面爬虫的上下文管理器"""
        self.page_crawler = PageCrawler()
        try:
            yield self.page_crawler
        finally:
            await self.page_crawler.close()
            self.page_crawler = None
    
    async def crawl_and_save_jiazi(self) -> Dict[str, Any]:
        """
        抓取并保存甲子榜数据
        
        Returns:
            采集结果统计
        """
        logger.info("开始甲子榜数据采集任务")
        
        try:
            # 抓取数据
            async with self._get_jiazi_crawler() as crawler:
                books, book_snapshots = await crawler.crawl()
            
            # 保存数据
            result = await self._save_crawled_data(
                books, book_snapshots, 
                ranking_name="甲子榜", 
                ranking_type="jiazi"
            )
            
            logger.info(f"甲子榜数据采集完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"甲子榜数据采集失败: {e}")
            raise
    
    async def crawl_and_save_page(self, channel: str) -> Dict[str, Any]:
        """
        抓取并保存分类页面数据
        
        Args:
            channel: 分类频道标识
            
        Returns:
            采集结果统计
        """
        logger.info(f"开始分类页面数据采集任务: {channel}")
        
        try:
            # 抓取数据
            async with self._get_page_crawler() as crawler:
                books, book_snapshots = await crawler.crawl(channel)
            
            # 保存数据
            result = await self._save_crawled_data(
                books, book_snapshots,
                ranking_name=f"分类页面-{channel}",
                ranking_type="page",
                channel=channel
            )
            
            logger.info(f"分类页面数据采集完成 ({channel}): {result}")
            return result
            
        except Exception as e:
            logger.error(f"分类页面数据采集失败 ({channel}): {e}")
            raise
    
    async def _save_crawled_data(self, 
                               books: List[Book], 
                               book_snapshots: List[BookSnapshot],
                               ranking_name: str,
                               ranking_type: str,
                               channel: Optional[str] = None) -> Dict[str, Any]:
        """
        保存抓取的数据到数据库
        
        Args:
            books: 书籍信息列表
            book_snapshots: 书籍快照列表
            ranking_name: 榜单名称
            ranking_type: 榜单类型
            channel: 频道标识
            
        Returns:
            保存结果统计
        """
        if not books or not book_snapshots:
            logger.warning("没有数据需要保存")
            return {
                "books_new": 0,
                "books_updated": 0,
                "snapshots_created": 0,
                "ranking_updated": False,
                "errors": ["没有数据"]
            }
        
        try:
            # 使用事务保存数据
            with get_session_sync() as session:
                # 1. 确保榜单记录存在
                ranking = self._ensure_ranking_exists(
                    session, ranking_name, ranking_type, channel
                )
                
                # 2. 保存书籍数据
                books_result = self._save_books(session, books)
                
                # 3. 保存书籍快照
                snapshots_result = self._save_book_snapshots(session, book_snapshots)
                
                # 4. 创建榜单快照（如果需要）
                ranking_snapshots = self._create_ranking_snapshots(
                    session, ranking.ranking_id, books, datetime.now()
                )
                
                # 5. 提交事务
                session.commit()
                
                logger.info(f"数据保存成功: {books_result['new']} 新书籍, "
                          f"{books_result['updated']} 更新书籍, "
                          f"{snapshots_result} 快照记录")
                
                return {
                    "books_new": books_result['new'],
                    "books_updated": books_result['updated'],
                    "snapshots_created": snapshots_result,
                    "ranking_snapshots_created": len(ranking_snapshots),
                    "ranking_updated": True,
                    "ranking_id": ranking.ranking_id,
                    "errors": []
                }
                
        except Exception as e:
            logger.error(f"数据保存失败: {e}")
            return {
                "books_new": 0,
                "books_updated": 0,
                "snapshots_created": 0,
                "ranking_updated": False,
                "errors": [str(e)]
            }
    
    def _ensure_ranking_exists(self, session, ranking_name: str, ranking_type: str, channel: Optional[str]) -> Ranking:
        """
        确保榜单记录存在
        
        Args:
            session: 数据库会话
            ranking_name: 榜单名称
            ranking_type: 榜单类型
            channel: 频道标识
            
        Returns:
            Ranking: 榜单记录
        """
        # 生成榜单ID
        ranking_id = f"{ranking_type}_{channel}" if channel else ranking_type
        
        # 查找现有榜单
        from sqlmodel import select
        statement = select(Ranking).where(Ranking.ranking_id == ranking_id)
        existing_ranking = session.exec(statement).first()
        
        if existing_ranking:
            # 更新最后更新时间
            existing_ranking.last_updated = datetime.now()
            session.add(existing_ranking)
            return existing_ranking
        else:
            # 创建新榜单
            new_ranking = Ranking(
                ranking_id=ranking_id,
                name=ranking_name,
                channel=channel or ranking_type,
                frequency="hourly" if ranking_type == "jiazi" else "daily",
                update_interval=1 if ranking_type == "jiazi" else 24,
                parent_id=None,
                created_at=datetime.now(),
                last_updated=datetime.now()
            )
            session.add(new_ranking)
            session.flush()  # 获取生成的ID
            return new_ranking
    
    def _save_books(self, session, books: List[Book]) -> Dict[str, int]:
        """
        保存书籍信息
        
        Args:
            session: 数据库会话
            books: 书籍列表
            
        Returns:
            保存结果统计
        """
        new_count = 0
        updated_count = 0
        
        from sqlmodel import select
        
        for book in books:
            # 查找现有书籍
            statement = select(Book).where(Book.book_id == book.book_id)
            existing_book = session.exec(statement).first()
            
            if existing_book:
                # 更新现有书籍
                existing_book.title = book.title
                existing_book.author_name = book.author_name
                existing_book.novel_class = book.novel_class
                existing_book.tags = book.tags
                existing_book.last_updated = datetime.now()
                session.add(existing_book)
                updated_count += 1
            else:
                # 添加新书籍
                session.add(book)
                new_count += 1
        
        return {"new": new_count, "updated": updated_count}
    
    def _save_book_snapshots(self, session, snapshots: List[BookSnapshot]) -> int:
        """
        保存书籍快照
        
        Args:
            session: 数据库会话
            snapshots: 快照列表
            
        Returns:
            保存的快照数量
        """
        for snapshot in snapshots:
            session.add(snapshot)
        
        return len(snapshots)
    
    def _create_ranking_snapshots(self, 
                                session, 
                                ranking_id: str, 
                                books: List[Book], 
                                snapshot_time: datetime) -> List[RankingSnapshot]:
        """
        创建榜单快照
        
        Args:
            session: 数据库会话
            ranking_id: 榜单ID
            books: 书籍列表（按排名顺序）
            snapshot_time: 快照时间
            
        Returns:
            创建的榜单快照列表
        """
        ranking_snapshots = []
        
        for position, book in enumerate(books, 1):
            ranking_snapshot = RankingSnapshot(
                ranking_id=ranking_id,
                book_id=book.book_id,
                position=position,
                snapshot_time=snapshot_time
            )
            session.add(ranking_snapshot)
            ranking_snapshots.append(ranking_snapshot)
        
        return ranking_snapshots
    
    async def get_crawl_statistics(self) -> Dict[str, Any]:
        """
        获取爬虫统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取书籍统计
            total_books = self.book_service.get_total_books()
            
            # 获取榜单统计
            total_rankings = self.ranking_service.get_total_rankings()
            
            # 获取最近快照统计
            recent_snapshots = self.book_service.get_recent_snapshots_count(hours=24)
            
            return {
                "total_books": total_books,
                "total_rankings": total_rankings,
                "recent_snapshots_24h": recent_snapshots,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取爬虫统计失败: {e}")
            return {
                "total_books": 0,
                "total_rankings": 0,
                "recent_snapshots_24h": 0,
                "error": str(e)
            }
        finally:
            self.book_service.close()
            self.ranking_service.close()
    
    def close(self):
        """关闭服务资源"""
        if self.book_service:
            self.book_service.close()
        if self.ranking_service:
            self.ranking_service.close()


# 全局爬虫服务实例
_crawler_service: Optional[CrawlerService] = None


def get_crawler_service() -> CrawlerService:
    """
    获取全局爬虫服务实例
    
    Returns:
        CrawlerService: 爬虫服务实例
    """
    global _crawler_service
    if _crawler_service is None:
        _crawler_service = CrawlerService()
    return _crawler_service


# 便捷函数
async def crawl_jiazi() -> Dict[str, Any]:
    """
    便捷函数：抓取甲子榜数据
    
    Returns:
        采集结果统计
    """
    service = get_crawler_service()
    try:
        return await service.crawl_and_save_jiazi()
    finally:
        service.close()


async def crawl_page(channel: str) -> Dict[str, Any]:
    """
    便捷函数：抓取分类页面数据
    
    Args:
        channel: 分类频道标识
        
    Returns:
        采集结果统计
    """
    service = get_crawler_service()
    try:
        return await service.crawl_and_save_page(channel)
    finally:
        service.close()