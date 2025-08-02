"""
爬虫模块内部结果数据类

使用 dataclass 提供轻量级的类型安全返回结构
仅供爬虫模块内部使用，不暴露给外部API
"""
import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .parser import NovelPageParser, RankingParser


@dataclass
class PageResult:
    """单页面爬取结果"""
    page_id: str
    rankings: Optional[List[RankingParser]] = field(default_factory=list)
    exception: Optional[Exception] = None

    @property
    def novel_ids(self):
        if not self.rankings:
            return []
        return list(set(itertools.chain.from_iterable(ranking.get_novel_ids() for ranking in self.rankings)))

    @classmethod
    def failed_res(cls, page_id: str, exception: exception) -> "PageResult":
        """创建失败结果"""
        return cls(
            page_id=page_id,
            exception=exception,
        )

    @classmethod
    def success_res(cls, page_id: str, rankings: List[RankingParser]) -> "PageResult":
        """创建成功结果"""
        return cls(
            page_id=page_id,
            rankings=rankings,
        )


@dataclass
class PagesResult:
    """多页面爬取结果"""
    page_data: Dict[str, PageResult] = field(default_factory=dict)

    @property
    def total_pages(self) -> int:
        return len(self.page_data)

    @property
    def successful_pages(self) -> int:
        return sum(1 for result in self.page_data.values() if not result.exception)

    @property
    def failed_pages(self) -> int:
        return self.total_pages - self.successful_pages

    @property
    def successful_rankings(self) -> int:
        rankings_num = 0
        for page in self.page_data.values():
            if not page.exception:
                rankings_num += len(page.rankings)
        return rankings_num


@dataclass
class BooksResult:
    """书籍爬取结果"""
    books: List[NovelPageParser] = field(default_factory=list)
    failed_novels: List[str] = field(default_factory=list)

    @property
    def total_novels(self) -> int:
        return len(self.books) + len(self.failed_novels)

    @property
    def successful_novels(self) -> int:
        return len(self.books)


@dataclass
class SaveResult:
    """数据保存结果"""
    rankings_saved: int = 0
    books_saved: int = 0
    exception: Optional[Exception] = None

    @classmethod
    def failed_res(cls, error: Exception) -> "SaveResult":
        """创建失败结果"""
        return cls(exception=error)

    @classmethod
    def success_res(cls, rankings_saved: int, books_saved: int) -> "SaveResult":
        """创建成功结果"""
        return cls(
            rankings_saved=rankings_saved,
            books_saved=books_saved
        )


@dataclass
class CrawlTaskResult:
    """爬取任务最终结果"""
    success: bool
    message: str
    total_pages: int
    successful_pages: int
    total_rankings: int
    total_books: int
    successful_books: int
    execution_time: float = 0.0
    error: Optional[Exception] = None

    @classmethod
    def failed_res(cls, error: Exception, message: str = None) -> "CrawlTaskResult":
        """创建失败结果"""
        if not message:
            message = str(error)
        return cls(error=error,
                   message=message)

    @classmethod
    def build_result(cls, page_results: PagesResult, book_results: BooksResult, db_results: SaveResult,
                     execution_time: float) -> "CrawlTaskResult":
        """创建成功结果"""
        if db_results.exception:
            return cls.failed_res(db_results.exception, "数据库存储失败")
        return cls(
            success=True,
            message="爬取成功",
            total_pages=page_results.total_pages,
            successful_pages=page_results.successful_pages,
            total_rankings=page_results.successful_rankings,
            total_books=book_results.total_novels,
            successful_books=len(book_results.books),
            execution_time=execution_time
        )
