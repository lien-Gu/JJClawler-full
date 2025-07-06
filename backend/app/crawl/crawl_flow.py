"""
爬取流程管理器 - 重新设计的爬取架构
"""
import asyncio
import time
from typing import Dict, List, Set, Optional, Any
from .base import CrawlConfig, HttpClient
from .parser import UnifiedParser, DataType, ParsedItem


class CrawlFlow:
    """
    爬取流程管理器
    
    流程设计：
    1. 生成页面地址
    2. 爬取页面内容
    3. 解析页面中的榜单
    4. 从榜单中提取书籍ID
    5. 去重后爬取书籍详情
    """
    
    def __init__(self, request_delay: float = 1.0):
        """
        初始化爬取流程管理器
        
        Args:
            request_delay: 请求间隔时间（秒）
        """
        self.request_delay = request_delay
        
        # 初始化组件
        self.config = CrawlConfig()
        self.client = HttpClient(request_delay=request_delay)
        self.parser = UnifiedParser()
        
        # 书籍去重集合
        self.crawled_book_ids: Set[str] = set()
        # 数据存储
        self.books_data: List[Dict] = []
        
        # 简化统计
        self.stats = {
            'books_crawled': 0,
            'total_requests': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def execute_crawl_task(self, task_id: str) -> Dict[str, Any]:
        """
        执行完整的爬取任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            爬取结果
        """
        self.stats['start_time'] = time.time()
        print(f"开始执行任务: {task_id}")
        
        try:
            # 第一步：生成页面地址
            page_url = self._generate_page_url(task_id)
            if not page_url:
                return self._create_error_result(task_id, "无法生成页面地址")
            
            # 第二步：爬取页面内容
            page_content = await self._crawl_page_content(page_url)
            if not page_content:
                return self._create_error_result(task_id, "页面内容爬取失败")
            
            # 第三步：解析页面中的榜单
            rankings = self._parse_rankings_from_page(page_content)
            print(f"发现 {len(rankings)} 个榜单")
            
            # 第四步：从榜单中提取书籍ID
            book_ids = self._extract_book_ids_from_rankings(rankings)
            print(f"发现 {len(book_ids)} 个书籍ID")
            
            # 第五步：去重后爬取书籍详情
            unique_book_ids = self._deduplicate_book_ids(book_ids)
            books = await self._crawl_books_details(unique_book_ids)
            
            print(f"爬取完成: {self.stats['books_crawled']} 个书籍详情")
            
            # 整合结果
            result = self._create_success_result(task_id, page_url, rankings, books)
            
            self.stats['end_time'] = time.time()
            
            return result
            
        except Exception as e:
            print(f"任务执行失败: {str(e)}")
            return self._create_error_result(task_id, str(e))
    
    async def execute_multiple_tasks(self, task_ids: List[str]) -> List[Dict[str, Any]]:
        """
        并发执行多个爬取任务
        
        Args:
            task_ids: 任务ID列表
            
        Returns:
            爬取结果列表
        """
        print(f"开始并发执行 {len(task_ids)} 个任务")
        
        # 为每个任务创建独立的流程实例（避免书籍去重冲突）
        tasks = []
        for task_id in task_ids:
            flow = CrawlFlow(self.request_delay)
            task = flow.execute_crawl_task(task_id)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(self._create_error_result(
                    task_ids[i], f"任务执行异常: {str(result)}"
                ))
            else:
                processed_results.append(result)
        
        # 汇总统计
        total_books = sum(r.get('books_crawled', 0) for r in processed_results if r.get('success'))
        successful_tasks = sum(1 for r in processed_results if r.get('success'))
        
        print(f"并发任务完成: {successful_tasks}/{len(task_ids)} 成功，共爬取 {total_books} 个书籍")
        
        return processed_results
    
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
        
        return book_ids
    
    def _deduplicate_book_ids(self, book_ids: List[str]) -> List[str]:
        """去重书籍ID"""
        unique_ids = []
        
        for book_id in book_ids:
            if book_id not in self.crawled_book_ids:
                unique_ids.append(book_id)
                self.crawled_book_ids.add(book_id)
            else:
                self.stats['duplicate_books_skipped'] += 1
        
        print(f"去重后书籍ID: {len(unique_ids)} 个")
        return unique_ids
    
    async def _crawl_books_details(self, book_ids: List[str]) -> List[Dict]:
        """批量爬取书籍详情"""
        if not book_ids:
            return []
        
        print(f"开始爬取 {len(book_ids)} 个书籍详情...")
        
        # 并发控制（最多5个并发）
        semaphore = asyncio.Semaphore(5)
        
        async def crawl_single_book(book_id: str) -> Optional[Dict]:
            async with semaphore:
                return await self._crawl_single_book_detail(book_id)
        
        # 并发爬取
        tasks = [crawl_single_book(book_id) for book_id in book_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        books = []
        for i, result in enumerate(results):
            if result and not isinstance(result, Exception):
                books.append(result)
                self.books_data.append(result)
                self.stats['books_crawled'] += 1
        
        return books
    
    async def _crawl_single_book_detail(self, book_id: str) -> Optional[Dict]:
        """爬取单个书籍详情"""
        try:
            # 构建书籍详情URL
            book_url = self.config.templates['novel_detail'].format(
                novel_id=book_id, 
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
            
        except Exception:
            return None
    
    def _create_success_result(self, task_id: str, url: str, rankings: List[Dict], books: List[Dict]) -> Dict[str, Any]:
        """创建成功结果"""
        return {
            'task_id': task_id,
            'success': True,
            'url': url,
            'rankings': rankings,
            'books': books,
            'pages_crawled': self.stats['pages_crawled'],
            'rankings_found': len(rankings),
            'books_found': self.stats['books_found'],
            'books_crawled': len(books),
            'duplicate_books_skipped': self.stats['duplicate_books_skipped'],
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
        """获取爬取的书籍数据"""
        return {'books': self.books_data}
    
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