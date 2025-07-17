"""
爬取流程管理器 - 重新设计的爬取架构（整合 manager 功能）
"""
import logging
import time
from typing import Dict, List, Set, Optional, Any
from datetime import datetime

from app.config import settings
from app.database.connection import get_db
from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService
from .base import CrawlConfig, HttpClient
from .parser import Parser, DataType

crawl_settings = settings.crawler


class CrawlFlow:
    """
    爬取流程管理器（整合 manager 功能）
    
    流程设计：
    1. 生成页面地址 (_generate_page_url)
    2. 爬取页面内容 (_crawl_page_content)
    3. 解析页面中的榜单 (_parse_rankings_from_page)
    4. 从榜单中提取书籍ID (_extract_book_ids_from_rankings)
    5. 去重后爬取书籍详情 (_crawl_books_details)
    6. 存储数据到数据库 (_save_crawl_result)
    """

    def __init__(self, request_delay: float = None):
        """
        初始化爬取流程管理器
        
        Args:
            request_delay: 请求间隔时间（秒）
        """
        # 初始化组件
        self.config = CrawlConfig()
        self.client = HttpClient(request_delay=request_delay or crawl_settings.request_delay)
        self.parser = Parser()
        
        # 初始化数据服务
        self.book_service = BookService()
        self.ranking_service = RankingService()

        # 书籍去重集合
        self.crawled_book_ids: Set[str] = set()
        # 数据存储
        self.books_data: List[Dict] = []
        self.pages_data: List[Dict] = []
        self.rankings_data: List[Dict] = []

        # 简化统计
        self.stats = {
            'books_crawled': 0,
            'total_requests': 0,
            'start_time': 0.0,
            'end_time': 0.0
        }

        # 配置日志
        self.logger = logging.getLogger(__name__)

    async def execute_crawl_task(self, page_id: str) -> Dict[str, Any]:
        """
        执行完整的爬取任务
        
        Args:
            page_id: 页面任务ID
            
        Returns:
            爬取结果（适用于调度模块的格式）
        """
        start_time = time.time()
        self.stats['start_time'] = start_time

        try:
            self.logger.info(f"开始爬取页面: {page_id}")

            # 第一步：生成页面地址
            page_url = self._generate_page_url(page_id)
            if not page_url:
                return self._format_error_result(page_id, "无法生成页面地址", start_time)

            # 第二步：爬取页面内容
            page_content = await self._crawl_page_content(page_url)
            if not page_content:
                return self._format_error_result(page_id, "页面内容爬取失败", start_time)

            # 第三步：解析页面中的榜单
            rankings = self._parse_rankings_from_page(page_content)
            self.logger.debug(f"发现 {len(rankings)} 个榜单")

            # 第四步：从榜单中提取书籍ID
            book_ids = self._extract_book_ids_from_rankings(rankings)
            self.logger.debug(f"发现 {len(book_ids)} 个书籍ID")

            # 第五步：去重后爬取书籍详情
            books = await self._crawl_books_details(book_ids)
            self.logger.debug(f"爬取完成: {self.stats['books_crawled']} 个书籍详情")

            # 第六步：存储数据到数据库
            save_success = await self._save_crawl_result(rankings, books)

            # 计算执行时间
            execution_time = time.time() - start_time
            self.stats['end_time'] = time.time()

            # 返回适用于调度模块的格式
            if save_success:
                self.logger.info(f"页面 {page_id} 爬取成功，爬取书籍 {len(books)} 本，耗时 {execution_time:.2f} 秒")
                return self._format_success_result(
                    page_id=page_id,
                    books_crawled=len(books),
                    execution_time=execution_time,
                    data={'url': page_url, 'rankings_count': len(rankings)}
                )
            else:
                return self._format_error_result(page_id, "数据保存失败", start_time)

        except Exception as e:
            self.logger.error(f"页面 {page_id} 爬取异常: {e}")
            return self._format_error_result(page_id, f"页面爬取异常: {str(e)}", start_time)

    def _format_success_result(self, page_id: str, books_crawled: int, execution_time: float, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """格式化成功结果"""
        result = {
            "success": True,
            "page_id": page_id,
            "books_crawled": books_crawled,
            "execution_time": execution_time,
        }
        if data:
            result["data"] = data
        return result

    def _format_error_result(self, page_id: str, error_msg: str, start_time: float) -> Dict[str, Any]:
        """格式化错误结果"""
        execution_time = time.time() - start_time
        self.logger.error(f"页面 {page_id} 爬取失败: {error_msg}")
        return {
            "success": False,
            "page_id": page_id,
            "books_crawled": 0,
            "execution_time": execution_time,
            "error_message": error_msg
        }

    def _generate_page_url(self, task_id: str) -> Optional[str]:
        """生成页面地址"""
        try:
            task_config = self.config.get_task_config(task_id)
            if not task_config:
                return None
            return self.config.build_url(task_config)
        except Exception:
            return None

    async def _crawl_page_content(self, url: str) -> Optional[Dict]:
        """爬取页面内容"""
        try:
            self.stats['total_requests'] += 1
            return await self.client.get(url)
        except Exception:
            return None

    def _parse_rankings_from_page(self, page_content: Dict) -> List[Dict]:
        """从页面中解析榜单"""
        try:
            parsed_items = self.parser.parse(page_content)

            rankings = []
            for item in parsed_items:
                if item.data_type == DataType.PAGE:
                    self.pages_data.append(item.data)
                elif item.data_type == DataType.RANKING:
                    rankings.append(item.data)
                    self.rankings_data.append(item.data)

            return rankings
        except Exception:
            return []

    def _extract_book_ids_from_rankings(self, rankings: List[Dict]) -> List[str]:
        """从榜单中提取书籍ID"""
        book_ids = []

        for ranking in rankings:
            books_in_ranking = ranking.get('books', [])
            for book in books_in_ranking:
                book_id = book.get('book_id')
                if book_id:
                    book_ids.append(str(book_id))

        # 去除重复id
        unique_ids = []

        for book_id in book_ids:
            if book_id not in self.crawled_book_ids:
                unique_ids.append(book_id)
                self.crawled_book_ids.add(book_id)

        print(f"去除重复书籍ID: {len(book_ids) - len(unique_ids)} 个")

        return unique_ids

    async def _crawl_books_details(self, book_ids: List[str]) -> List[Dict]:
        """顺序爬取书籍详情（简化版，无并发控制）"""
        if not book_ids:
            return []

        print(f"开始爬取 {len(book_ids)} 个书籍详情...")

        books = []
        for book_id in book_ids:
            try:
                result = await self.crawl_book_detail(book_id)
                if result:
                    books.append(result)
                    self.books_data.append(result)
                    self.stats['books_crawled'] += 1
            except Exception as e:
                print(f"爬取书籍 {book_id} 失败: {e}")
                continue

        return books

    async def _save_crawl_result(self, rankings: List[dict], books: List[dict]) -> bool:
        """第六步：存储数据到数据库"""
        try:
            # 使用数据库会话上下文管理器
            for db in get_db():
                try:
                    snapshot_time = datetime.now()
                    
                    # 保存榜单数据
                    if rankings:
                        await self._save_rankings(db, rankings, snapshot_time)
                    
                    # 保存书籍数据
                    if books:
                        await self._save_books(db, books, snapshot_time)
                    
                    # 提交事务
                    db.commit()
                    self.logger.info(f"成功保存 {len(rankings)} 个榜单和 {len(books)} 本书籍的数据")
                    return True
                    
                except Exception as e:
                    # 回滚事务
                    db.rollback()
                    self.logger.error(f"保存数据失败: {e}")
                    raise
                
                # 只循环一次，使用 break 退出
                break
                
        except Exception as e:
            self.logger.error(f"处理爬取结果时出错: {e}")
            return False

    async def _save_rankings(self, db, rankings_data: List[Dict], snapshot_time: datetime) -> None:
        """保存榜单数据"""
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
                
                # 保存榜单快照
                books = ranking_data.get("books", [])
                ranking_snapshots = []
                
                for book in books:
                    # 先确保书籍存在
                    book_info = {
                        "book_id": book.get("book_id"),
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

    async def _save_books(self, db, books_data: List[Dict], snapshot_time: datetime) -> None:
        """保存书籍数据"""
        book_snapshots = []
        
        for book_data in books_data:
            try:
                # 创建或更新书籍基本信息
                book_info = {
                    "book_id": book_data.get("book_id"),
                    "title": book_data.get("title", "")
                }
                
                book = self.book_service.create_or_update_book(db, book_info)
                
                # 创建书籍快照数据
                snapshot_data = {
                    "book_id": book.id,
                    "clicks": book_data.get("clicks", 0),
                    "favorites": book_data.get("favorites", 0),
                    "comments": book_data.get("comments", 0),
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

    async def crawl_book_detail(self, book_id: str) -> Optional[Dict]:
        """爬取单个书籍详情"""
        try:
            # 构建书籍详情URL
            book_url = self.config.templates['novel_detail'].format(
                book_id=book_id,
                **self.config.params
            )

            # 爬取书籍内容
            self.stats['total_requests'] += 1
            book_content = await self.client.get(book_url)

            # 解析书籍详情
            parsed_items = self.parser.parse(book_content)

            for item in parsed_items:
                if item.data_type == DataType.BOOK:
                    return item.data

            return None

        except Exception as e:
            print(f"爬取书籍详情失败 {book_id}: {e}")
            return None

    def _create_success_result(self, task_id: str, url: str, rankings: List[Dict], books: List[Dict]) -> Dict[str, Any]:
        """创建成功结果"""
        return {
            'task_id': task_id,
            'success': True,
            'url': url,
            'rankings': rankings,
            'books': books,
            'books_crawled': len(books),
            'stats': self.stats.copy(),
            'timestamp': time.time()
        }

    def _create_error_result(self, task_id: str, error: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'task_id': task_id,
            'success': False,
            'error': error,
            'stats': self.stats.copy(),
            'timestamp': time.time()
        }

    def get_all_data(self) -> Dict[str, List]:
        """获取爬取的所有数据"""
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
        stats['total_data_items'] = len(self.pages_data) + len(self.rankings_data) + len(self.books_data)
        return stats

    async def close(self):
        """关闭资源"""
        await self.client.close()
