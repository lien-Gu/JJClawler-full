"""
爬取流程管理器 - 高效的并发爬取架构
"""
import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from app.config import settings
from app.database.connection import get_db
from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService

from .base import CrawlConfig, HttpClient
from .parser import DataType, Parser

logger = logging.getLogger(__name__)


class CrawlFlow:
    """
    爬取流程管理器
    
    功能：
    1. 并发爬取书籍详情，提升性能
    2. 创建书籍和榜单快照，记录变化
    3. 统一错误处理和日志记录
    4. 模块化设计，提高代码复用率
    """

    def __init__(self, request_delay: Optional[float] = None, 
                 concurrent_mode: Optional[bool] = None) -> None:
        """
        初始化爬取流程管理器
        
        Args:
            request_delay: 请求间隔时间（秒）
            concurrent_mode: 是否启用并发模式（None时使用配置文件设置）
        """
        self.config = CrawlConfig()
        self.parser = Parser()
        self.book_service = BookService()
        self.ranking_service = RankingService()
        
        # 从配置文件获取设置
        crawler_config = settings.crawler
        
        # 配置HTTP客户端
        if concurrent_mode is None:
            # 根据配置的并发请求数判断是否启用并发模式
            self.concurrent_mode = crawler_config.concurrent_requests > 1
        else:
            self.concurrent_mode = concurrent_mode
            
        if self.concurrent_mode:
            delay = request_delay or (crawler_config.request_delay / 10)  # 并发时减少延迟
            timeout = crawler_config.timeout / 2  # 并发时减少超时
        else:
            delay = request_delay or crawler_config.request_delay
            timeout = crawler_config.timeout
            
        self.client = HttpClient(request_delay=delay, timeout=timeout)
        
        # 初始化数据容器
        self._reset_data()
        
        # 统计信息
        self.stats = {
            'books_crawled': 0,
            'total_requests': 0,
            'start_time': 0.0,
            'end_time': 0.0
        }

    def _reset_data(self) -> None:
        """重置数据容器"""
        self.crawled_book_ids: Set[str] = set()
        self.books_data: List[Dict] = []
        self.rankings_data: List[Dict] = []
        self.pages_data: List[Dict] = []

    async def execute_crawl_task(self, page_id: str) -> Dict[str, Any]:
        """
        执行完整的爬取任务
        
        Args:
            page_id: 页面任务ID
            
        Returns:
            爬取结果
        """
        start_time = time.time()
        self.stats['start_time'] = start_time
        
        try:
            logger.info(f"开始爬取页面: {page_id}")
            
            # 生成页面URL
            page_url = self._generate_page_url(page_id)
            if not page_url:
                return self._create_error_result(page_id, "无法生成页面地址", start_time)
            
            # 爬取页面内容
            page_content = await self._crawl_page_content(page_url)
            if not page_content:
                return self._create_error_result(page_id, "页面内容爬取失败", start_time)
            
            # 解析榜单
            rankings = self._parse_rankings_from_page(page_content, page_id)
            logger.debug(f"发现 {len(rankings)} 个榜单")
            
            # 提取书籍ID
            book_ids = self._extract_unique_book_ids(rankings)
            logger.debug(f"发现 {len(book_ids)} 个唯一书籍ID")
            
            # 爬取书籍详情
            books = await self._crawl_books_details(book_ids)
            logger.debug(f"成功爬取 {len(books)} 个书籍详情")
            
            # 保存数据
            save_success = await self._save_crawl_result(rankings, books)
            
            # 返回结果
            execution_time = time.time() - start_time
            self.stats['end_time'] = time.time()
            
            if save_success:
                logger.info(f"页面 {page_id} 爬取成功，耗时 {execution_time:.2f} 秒")
                return self._create_success_result(page_id, len(books), execution_time)
            else:
                return self._create_error_result(page_id, "数据保存失败", start_time)
                
        except Exception as e:
            logger.error(f"页面 {page_id} 爬取异常: {e}")
            return self._create_error_result(page_id, f"爬取异常: {str(e)}", start_time)

    def _generate_page_url(self, task_id: str) -> Optional[str]:
        """生成页面URL"""
        try:
            task_config = self.config.get_task_config(task_id)
            if not task_config:
                logger.error(f"未找到任务配置: {task_id}")
                return None
            return self.config.build_url(task_config)
        except Exception as e:
            logger.error(f"生成URL失败: {e}")
            return None

    async def _crawl_page_content(self, url: str) -> Optional[Dict]:
        """爬取页面内容"""
        try:
            self.stats['total_requests'] += 1
            return await self.client.get(url)
        except Exception as e:
            logger.error(f"爬取页面内容失败: {e}")
            return None

    def _parse_rankings_from_page(self, page_content: Dict, page_id: str) -> List[Dict]:
        """从页面解析榜单数据"""
        try:
            context = {"page_id": page_id}
            parsed_items = self.parser.parse(page_content, context)
            
            rankings = []
            for item in parsed_items:
                if item.data_type == DataType.PAGE:
                    self.pages_data.append(item.data)
                elif item.data_type == DataType.RANKING:
                    rankings.append(item.data)
                    self.rankings_data.append(item.data)
            
            return rankings
        except Exception as e:
            logger.error(f"解析榜单数据失败: {e}")
            return []

    def _extract_unique_book_ids(self, rankings: List[Dict]) -> List[str]:
        """
        从榜单中提取唯一的书籍ID
        
        注意：这里只是去除当前会话中的重复ID，
        不跳过数据库中已存在的书籍，因为需要创建新的快照
        """
        all_book_ids = []
        
        for ranking in rankings:
            books = ranking.get('books', [])
            for book in books:
                book_id = book.get('book_id')
                if book_id:
                    all_book_ids.append(str(book_id))
        
        # 去除当前会话中的重复ID
        unique_ids = []
        for book_id in all_book_ids:
            if book_id not in self.crawled_book_ids:
                unique_ids.append(book_id)
                self.crawled_book_ids.add(book_id)
        
        return unique_ids

    async def _crawl_books_details(self, book_ids: List[str]) -> List[Dict]:
        """
        并发爬取书籍详情
        
        Args:
            book_ids: 书籍ID列表
            
        Returns:
            书籍详情列表
        """
        if not book_ids:
            return []
        
        logger.info(f"开始爬取 {len(book_ids)} 个书籍详情")
        
        if self.concurrent_mode:
            return await self._crawl_books_concurrent(book_ids)
        else:
            return await self._crawl_books_sequential(book_ids)

    async def _crawl_books_concurrent(self, book_ids: List[str]) -> List[Dict]:
        """并发模式爬取书籍"""
        books = []
        # 使用配置的并发请求数作为批处理大小
        batch_size = min(settings.crawler.concurrent_requests * 2, 10)  # 最多10个一批
        
        for i in range(0, len(book_ids), batch_size):
            batch_ids = book_ids[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(book_ids) - 1) // batch_size + 1
            
            logger.debug(f"处理第 {batch_num}/{total_batches} 批，{len(batch_ids)} 个书籍")
            
            batch_results = await self._crawl_books_batch(batch_ids)
            books.extend(batch_results)
            
            # 批次间延迟，使用配置的请求延迟
            if i + batch_size < len(book_ids):
                await asyncio.sleep(settings.crawler.request_delay)
        
        return books

    async def _crawl_books_sequential(self, book_ids: List[str]) -> List[Dict]:
        """顺序模式爬取书籍"""
        books = []
        for i, book_id in enumerate(book_ids, 1):
            logger.debug(f"爬取书籍 {i}/{len(book_ids)}: {book_id}")
            book_data = await self._crawl_single_book(book_id)
            if book_data:
                books.append(book_data)
        return books

    async def _crawl_books_batch(self, book_ids: List[str]) -> List[Dict]:
        """并发爬取一批书籍"""
        semaphore = asyncio.Semaphore(settings.crawler.concurrent_requests)
        
        async def crawl_with_semaphore(book_id: str) -> Optional[Dict]:
            async with semaphore:
                return await self._crawl_single_book(book_id)
        
        # 创建并发任务
        tasks = [crawl_with_semaphore(book_id) for book_id in book_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤有效结果
        books = []
        for result in results:
            if isinstance(result, dict):
                books.append(result)
            elif isinstance(result, Exception):
                logger.warning(f"爬取书籍时出现异常: {result}")
        
        return books

    async def _crawl_single_book(self, book_id: str) -> Optional[Dict]:
        """爬取单个书籍详情"""
        try:
            # 构建URL
            book_url = self.config.templates['novel_detail'].format(
                novel_id=book_id,
                **self.config.params
            )
            
            # 发起请求
            self.stats['total_requests'] += 1
            book_content = await self.client.get(book_url)
            
            # 解析数据
            parsed_items = self.parser.parse(book_content)
            
            for item in parsed_items:
                if item.data_type == DataType.BOOK:
                    self.books_data.append(item.data)
                    self.stats['books_crawled'] += 1
                    return item.data
            
            logger.warning(f"未能解析书籍 {book_id} 的详情数据")
            return None
            
        except Exception as e:
            logger.error(f"爬取书籍 {book_id} 失败: {e}")
            return None

    async def _save_crawl_result(self, rankings: List[Dict], 
                                books: List[Dict]) -> bool:
        """保存爬取结果到数据库"""
        try:
            for db in get_db():
                try:
                    snapshot_time = datetime.now()
                    await self._save_rankings(db, rankings, snapshot_time)
                    await self._save_books(db, books, snapshot_time)
                    
                    db.commit()
                    logger.info(f"成功保存 {len(rankings)} 个榜单和 {len(books)} 本书籍")
                    return True
                    
                except Exception as e:
                    db.rollback()
                    logger.error(f"保存数据失败: {e}")
                    raise
                break
                
        except Exception as e:
            logger.error(f"数据库操作失败: {e}")
            return False

    async def _save_rankings(self, db, rankings_data: List[Dict], 
                           snapshot_time: datetime) -> None:
        """保存榜单数据和快照"""
        for ranking_data in rankings_data:
            try:
                # 保存或更新榜单基本信息
                ranking_info = {
                    "rank_id": ranking_data.get("rank_id"),
                    "name": ranking_data.get("rank_name", ""),
                    "page_id": ranking_data.get("page_id", ""),
                    "rank_group_type": ranking_data.get("rank_group_type", ""),
                    "sub_ranking_name": ranking_data.get("sub_ranking_name")
                }
                
                ranking = self.ranking_service.create_or_update_ranking(db, ranking_info)
                
                # 创建榜单快照
                books = ranking_data.get("books", [])
                ranking_snapshots = []
                
                for book in books:
                    # 确保书籍存在
                    book_info = {
                        "novel_id": int(book.get("book_id")),
                        "title": book.get("title", "")
                    }
                    book_obj = self.book_service.create_or_update_book(db, book_info)
                    
                    # 创建榜单快照记录
                    snapshot_data = {
                        "ranking_id": ranking.id,
                        "book_id": book_obj.id,
                        "position": book.get("position", 0),
                        "score": book.get("score", 0.0),
                        "snapshot_time": snapshot_time
                    }
                    ranking_snapshots.append(snapshot_data)
                
                # 批量保存榜单快照
                if ranking_snapshots:
                    self.ranking_service.batch_create_ranking_snapshots(
                        db, ranking_snapshots
                    )
                
                logger.debug(f"保存榜单 '{ranking_data.get('rank_name')}' "
                           f"及其 {len(books)} 个书籍快照")
                
            except Exception as e:
                logger.error(f"保存榜单 '{ranking_data.get('rank_name')}' 失败: {e}")
                raise

    async def _save_books(self, db, books_data: List[Dict], 
                        snapshot_time: datetime) -> None:
        """保存书籍数据和快照"""
        if not books_data:
            return
        
        book_snapshots = []
        
        for book_data in books_data:
            try:
                # 保存或更新书籍基本信息
                book_info = {
                    "novel_id": int(book_data.get("book_id")),
                    "title": book_data.get("title", "")
                }
                
                book = self.book_service.create_or_update_book(db, book_info)
                
                # 创建书籍快照记录
                snapshot_data = {
                    "book_id": book.id,
                    "clicks": self._parse_number(book_data.get("clicks", 0)),
                    "favorites": self._parse_number(book_data.get("favorites", 0)),
                    "comments": self._parse_number(book_data.get("comments", 0)),
                    "recommendations": self._parse_number(book_data.get("nutrition", 0)),
                    "word_count": self._parse_number(book_data.get("word_count")),
                    "status": book_data.get("status"),
                    "snapshot_time": snapshot_time
                }
                book_snapshots.append(snapshot_data)
                
            except Exception as e:
                logger.error(f"处理书籍 '{book_data.get('title')}' 数据失败: {e}")
                continue
        
        # 批量保存书籍快照
        if book_snapshots:
            self.book_service.batch_create_book_snapshots(db, book_snapshots)
            logger.debug(f"保存 {len(book_snapshots)} 个书籍快照")

    def _parse_number(self, value: Any) -> Optional[int]:
        """
        解析数值字段，处理格式化字符串
        
        Args:
            value: 待解析的值
            
        Returns:
            解析后的整数，失败时返回None
        """
        if value is None:
            return None
        
        if isinstance(value, (int, float)):
            return int(value)
        
        if isinstance(value, str):
            # 提取数字，处理如 "85,221(章均)" -> "85221" 的格式
            numbers = re.findall(r'[\d,]+', value)
            if numbers:
                try:
                    number_str = numbers[0].replace(',', '')
                    return int(number_str)
                except ValueError:
                    pass
        
        return 0

    def _create_success_result(self, page_id: str, books_crawled: int, 
                              execution_time: float) -> Dict[str, Any]:
        """创建成功结果"""
        return {
            "success": True,
            "page_id": page_id,
            "books_crawled": books_crawled,
            "execution_time": execution_time,
        }

    def _create_error_result(self, page_id: str, error_msg: str, 
                           start_time: float) -> Dict[str, Any]:
        """创建错误结果"""
        execution_time = time.time() - start_time
        return {
            "success": False,
            "page_id": page_id,
            "books_crawled": 0,
            "execution_time": execution_time,
            "error_message": error_msg
        }

    def get_all_data(self) -> Dict[str, List]:
        """获取所有爬取的数据"""
        return {
            'books': self.books_data,
            'rankings': self.rankings_data,
            'pages': self.pages_data
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        if stats['start_time'] and stats['end_time']:
            stats['execution_time'] = stats['end_time'] - stats['start_time']
        stats['total_data_items'] = (
            len(self.pages_data) + len(self.rankings_data) + len(self.books_data)
        )
        return stats

    async def close(self) -> None:
        """关闭资源"""
        await self.client.close()