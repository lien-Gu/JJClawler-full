"""
爬取流程管理器 - 高效的并发爬取架构
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List
from typing import Tuple

import httpx
from sqlalchemy.orm import Session
from tenacity import before_sleep_log, retry, retry_if_exception_type, retry_if_exception, stop_after_attempt, stop_after_delay, wait_exponential

from app.config import get_settings
from app.crawl.crawl_task import get_crawl_task, PageTask
from app.database.connection import SessionLocal
from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService
from app.logger import get_logger
from app.crawl.http_client import HttpClient
from app.crawl.parser import NovelPageParser, PageParser, RankingParser
from app.models.base import BaseResult
from app.utils import generate_batch_id

logger = get_logger(__name__)


@dataclass
class PagesResult(BaseResult[PageParser]):
    """多页面爬取结果"""

    @property
    def rankings(self) -> List[RankingParser]:
        res = []
        for page in self.success_items:
            res.extend(page.rankings)
        return res

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_pages_num": self.total_num,
            "failed_pages": self.failed_ids
        }


@dataclass
class NovelsResult(BaseResult[NovelPageParser]):
    """
    多书籍页面爬取结果
    """

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_novels_num": self.total_num,
            "failed_novels": self.failed_ids
        }


crawler_config = get_settings().crawler
book_service = BookService()
ranking_service = RankingService()
crawl_task = get_crawl_task()


def create_smart_retry_decorator():
    """
    创建基于配置的智能重试装饰器
    
    特性：
    - 使用配置文件参数
    - 最大重试时间限制  
    - 特殊处理503错误
    - 指数退避策略
    """
    def is_503_error(exception):
        """检查是否为503错误 - 增强版本"""
        error_str = str(exception).lower()
        is_503 = ("503" in error_str or 
                  "service temporarily unavailable" in error_str or
                  "service unavailable" in error_str)
        
        # 添加调试日志来确认检测是否生效
        if is_503:
            logger.warning(f"检测到503错误，将进行重试: {str(exception)[:100]}...")
        
        return is_503
    
    # 针对503错误使用更宽松的重试策略
    retry_attempts = max(5, crawler_config.retry_times)  # 至少5次重试
    max_time = max(60.0, crawler_config.max_retry_time)  # 调整为60秒，更合理
    
    return retry(
        # 停止条件：达到最大重试次数 OR 超过最大重试时间
        stop=stop_after_attempt(retry_attempts) | stop_after_delay(max_time),
        
        # 等待策略：指数退避，针对503错误优化
        wait=wait_exponential(
            multiplier=1.5,  # 更温和的倍数，避免等待时间过长
            min=2.0,         # 503错误需要更长的基础等待时间
            max=15.0         # 降低单次等待上限，平衡总时间
        ),
        
        # 重试条件：HTTP异常 OR 503错误
        retry=(
            retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, httpx.TimeoutException, json.JSONDecodeError)) |
            retry_if_exception(is_503_error)
        ),
        
        # 日志记录 - 使用INFO级别确保能看到重试日志
        before_sleep=before_sleep_log(logger, logging.INFO),
        reraise=True
    )



class CrawlFlow:
    """
    统一并发爬取流程管理器 - 两阶段处理架构
    
    阶段 1: 获取所有页面内容
    阶段 2: 获取所有书籍内容  
    全局统一并发控制
    """

    def __init__(self) -> None:
        """
        初始化爬取流程管理器
        """
        # 每个实例创建独立的HTTP客户端和并发控制
        self.client = HttpClient()
        self.request_semaphore = asyncio.Semaphore(crawler_config.max_concurrent_requests)

    async def execute_crawl_task(self, page_ids: List[str]) -> Dict[str, Any]:
        """
        执行统一并发爬取任务 - 两阶段处理架构
        
        Args:
            page_ids: 页面ID或页面ID列表
            
        Returns:
            爬取结果
        """
        page_tasks = crawl_task.get_tasks_by_words(page_ids)

        start_time = time.time()
        logger.info(f"开始统一并发爬取 {len(page_ids)} 个页面: {page_ids}")
        try:
            # 阶段 1: 获取所有页面内容
            page_data = await self._fetch_pages(page_tasks)

            # 阶段 2: 获取所有书籍内容
            book_data = await self._fetch_books(page_data)

            # 阶段 3: 保存数据
            save_results = await self._save_data(page_data, book_data)

            execution_time = time.time() - start_time
            logger.info(f"统一并发爬取总耗时 {execution_time:.2f}s")

            # 使用类型安全的结果构建
            return {
                "success": True,
                "page_results": page_data.to_dict(),
                "book_results": book_data.to_dict(),
                "store_results": save_results,
                "execution_time": execution_time
            }

        except Exception as e:
            logger.error(f"爬取任务执行失败: {e}")
            return {
                "success": False,
                "exception": e
            }

    async def _fetch_pages(self, page_tasks: List[PageTask]) -> PagesResult:
        """
        阶段 1: 并发获取所有页面内容
        
        Args:
            page_tasks: 页面ID列表
            
        Returns:
            类型安全的页面结果
        """
        logger.info(f"阶段 1: 开始获取 {len(page_tasks)} 个页面内容")

        # 创建所有页面的获取任务
        tasks = [self._fetch_and_parse_page(t) for t in page_tasks]
        pages = await asyncio.gather(*tasks, return_exceptions=True)

        # 使用类型安全的结果类
        pages_result = PagesResult()

        for t, result in zip(page_tasks, pages):
            if isinstance(result, Exception):
                pages_result.failed_items[t.id] = result
            else:
                pages_result.success_items.append(result)

        logger.info(f"阶段 1 完成: 成功 {len(pages_result.success_items)}/{pages_result.total_num} 个页面")
        return pages_result

    @create_smart_retry_decorator()
    async def _fetch_and_parse_page(self, page_task: PageTask) -> PageParser | Exception:
        async with self.request_semaphore:
            try:
                logger.info(f"开始爬取页面: {page_task.name}")

                # 获取页面内容
                page_content = await self.client.run(page_task.url)

                if not page_content or page_content.get("status") == "error":
                    raise Exception(f"页面内容获取失败: {page_content.get('error', '未知错误')}")

                # 解析榜单信息
                page_parser = PageParser(page_content, page_id=page_task.id)

                logger.info(
                    f"页面 {page_task} 内容获取完成: 解析榜单 {len(page_parser.rankings)}个")

                return page_parser
            except Exception as e:
                logger.error(f"页面 {page_task} 内容获取异常: {e}")
                return e

    async def _fetch_books(self, pages_result: PagesResult) -> NovelsResult:
        """
        阶段 2: 并发获取所有书籍内容
        
        Args:
            pages_result: 类型安全的页面结果
            
        Returns:
            类型安全的书籍结果
        """
        # 收集所有成功页面的书籍ID
        all_novel_ids = set()
        for page_result in pages_result.success_items:
            all_novel_ids.update(page_result.get_novel_ids())
        all_novel_ids = list(all_novel_ids)
        if not all_novel_ids:
            logger.info("阶段 2: 无书籍ID需要获取")
            return NovelsResult()

        logger.info(f"阶段 2: 开始获取 {len(all_novel_ids)} 个书籍内容")

        # 并发获取所有书籍内容
        book_tasks = [self._fetch_and_parse_book(book_id) for book_id in all_novel_ids]
        book_results = await asyncio.gather(*book_tasks, return_exceptions=True)

        # 使用类型安全的结果类
        books_result = NovelsResult()
        for novel_id, result in zip(all_novel_ids, book_results):
            if isinstance(result, Exception):
                books_result.failed_items[novel_id] = result
                logger.error(f"书籍 {novel_id} 获取失败: {result}")
            else:
                books_result.success_items.append(result)

        logger.info(f"阶段 2 完成: 成功 {len(books_result.success_items)}/{books_result.total_num} 个书籍")

        return books_result

    @create_smart_retry_decorator()
    async def _fetch_and_parse_book(self, novel_id: str) -> NovelPageParser | Exception:
        """
        书籍获取

        :param novel_id: 书籍ID
        :return: 书籍响应数据
        """
        async with self.request_semaphore:
            try:
                book_url = crawl_task.build_novel_url(novel_id)
                result = await self.client.run(book_url)
                # 检查HTTP请求是否有错误
                if result.get("status") == "error":
                    error_msg = result.get("error", "HTTP request failed")
                    raise Exception(f"Book {book_url} fetch failed with status: {error_msg}")
                
                # 检查是否是有效的书籍数据（晋江API返回包含novelId的JSON数据）
                if not result.get("novelId"):
                    raise Exception(f"Invalid book data: missing novelId in response")
                
                novel_parser = NovelPageParser(result)
                return novel_parser
            except Exception as e:
                logger.error(f"书籍页面 {novel_id} 内容获取异常: {e}")
                return e

    async def _save_data(self, pages_result: PagesResult, novels_result: NovelsResult) -> Dict[str, int]:
        """
        阶段 3: 保存所有数据 - 容错保存机制
        
        Args:
            pages_result: 类型安全的页面结果
            novels_result: 类型安全的书籍结果
            
        Returns:
            保存结果统计
        """
        logger.info("阶段 3: 开始保存所有数据")

        # 收集所有榜单数据
        all_rankings = pages_result.rankings
        books = novels_result.success_items

        ranking_snapshots_num = 0
        books_snapshots_num = 0

        # 创建独立的数据库会话并保存数据
        db = SessionLocal()
        try:
            # 使用现有的Service方法保存数据
            if all_rankings:
                _, ranking_snapshots_num = self.save_ranking_parsers(all_rankings, db)
                logger.info(f"保存了 {len(all_rankings)} 个榜单，{ranking_snapshots_num} 个榜单快照")
            else:
                logger.info("没有榜单数据需要保存")

            if books:
                books_snapshots_num = self.save_novel_parsers(books, db)
                logger.info(f"保存了 {len(books)} 个书籍，{books_snapshots_num} 个书籍快照")
            else:
                logger.info("没有书籍数据需要保存")

            db.commit()
            
            # 更准确的完成日志
            total_saved = len(all_rankings) + len(books) + ranking_snapshots_num + books_snapshots_num
            if total_saved > 0:
                logger.info(f"阶段 3 完成: 成功保存 {total_saved} 条数据记录")
            else:
                logger.warning("阶段 3 完成: 没有数据被保存到数据库")

            return {
                "rankings": len(all_rankings),
                "ranking_snapshots": ranking_snapshots_num,
                "books": len(books),
                "books_snapshots": books_snapshots_num,
            }
        except Exception as db_error:
            db.rollback()
            logger.error(f"数据库操作失败: {db_error}")
            return db_error
        finally:
            db.close()

    @staticmethod
    def save_ranking_parsers(rankings: List[RankingParser], db: Session) -> Tuple[int, int]:
        """
        保存从榜单网页中爬取的榜单记录、榜单中的书籍记录、榜单快照记录
        :param rankings:
        :param db:
        :return: 保存的榜单数量，保存的榜单快照数量
        """
        stored_ranking_snapshots = 0
        for ranking in rankings:
            # 保存或更新榜单信息
            rank_record = ranking_service.create_or_update_ranking(
                db, ranking.ranking_info
            )
            ranking_snapshots = []
            batch_id = generate_batch_id()
            stored_ranking_snapshots += len(ranking.book_snapshots)
            for book in ranking.book_snapshots:
                try:
                    # 保存书籍
                    book_record = book_service.create_or_update_book(db, book)
                    # 创建榜单快照记录
                    snapshot_data = {
                        "ranking_id": rank_record.id,
                        "book_id": book_record.id,
                        "batch_id": batch_id,
                        **book
                    }
                    ranking_snapshots.append(snapshot_data)
                except Exception as e:
                    logger.error(f"书籍保存异常，跳过该记录: {book.get('novel_id', 'unknown')}, 错误: {e}")
                    continue

            # 批量保存榜单快照
            if ranking_snapshots:
                ranking_service.batch_create_ranking_snapshots(
                    db, ranking_snapshots, batch_id
                )
        return len(rankings), stored_ranking_snapshots

    @staticmethod
    def save_novel_parsers(books: List[NovelPageParser], db: Session) -> int:
        """
        保存书籍快照
        :param books:
        :param db:
        :return:
        """
        # 保存书籍快照
        book_snapshots = []
        for book_data in books:
            try:
                # 保存或更新书籍基本信息
                book_info = book_data.book_detail
                book_record = book_service.create_or_update_book(db, book_info)
                
                if book_record is None:
                    logger.warning(f"书籍保存失败，跳过该记录: {book_info.get('novel_id', 'unknown')}")
                    continue

                # 创建书籍快照记录
                snapshot_data = {
                    "book_id": book_record.id,
                    **book_info
                }
                book_snapshots.append(snapshot_data)
            except Exception as e:
                # 回滚当前事务，重新开始
                db.rollback()
                logger.error(f"书籍保存异常，跳过该记录: {book_info.get('novel_id', 'unknown')}, 错误: {e}")
                continue
        # 批量保存书籍快照
        if book_snapshots:
            book_service.batch_create_book_snapshots(db, book_snapshots)
        return len(book_snapshots)

    async def close(self) -> None:
        """关闭资源"""
        await self.client.close()


# 全局爬虫实例管理
_craw_flow: CrawlFlow | None = None


def get_crawl_flow() -> CrawlFlow:
    """获取爬虫程序实例（单例模式）"""
    global _craw_flow
    if _craw_flow is None:
        _craw_flow = CrawlFlow()
    return _craw_flow


def crawl_task_wrapper(page_ids: List[str]) -> Dict[str, Any]:
    """
    APScheduler任务包装函数 - 在同步上下文中运行异步任务
    
    修复Event loop问题：每次任务执行时创建新的CrawlFlow实例
    
    Args:
        page_ids: 页面ID列表
        
    Returns:
        爬取结果字典
    """
    import asyncio

    async def async_crawl_task():
        # 每次任务执行时创建新的CrawlFlow实例，避免事件循环冲突
        crawl_flow = CrawlFlow()
        try:
            result = await crawl_flow.execute_crawl_task(page_ids)
            return result
        finally:
            # 确保资源清理
            await crawl_flow.close()
    
    try:
        # 在同步上下文中运行异步任务
        result = asyncio.run(async_crawl_task())
        
        logger.info(f"爬取任务包装函数执行完成：成功={result.get('success', False)}")
        return result
        
    except Exception as e:
        error_msg = f"爬取任务包装函数执行失败: {str(e)}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "exception_type": type(e).__name__
        }


if __name__ == '__main__':
    import asyncio
    
    async def debug_book_fetch():
        c = get_crawl_flow()
        result = await c._fetch_and_parse_book("3980442")
        print(f"调试结果: {result}")
        
        # 如果获取成功，显示解析的书籍信息
        if hasattr(result, 'book_detail'):
            print(f"书籍详情: {result.book_detail}")
        
        await c.close()
    
    asyncio.run(debug_book_fetch())