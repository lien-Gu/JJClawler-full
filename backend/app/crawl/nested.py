"""
嵌套爬虫实现，支持多层次数据爬取
"""
import asyncio
import time
from typing import Dict, List, Optional, Any, Set
from .base import BaseCrawler, CrawlConfig, HttpClient
from .parser import UnifiedParser, ParsedItem, DataType


class NestedCrawler:
    """嵌套爬虫，支持从页面->榜单->书籍的层次爬取"""
    
    def __init__(self, request_delay: float = 1.0, max_depth: int = 3, max_book_details: int = 100):
        """
        初始化嵌套爬虫
        
        Args:
            request_delay: 请求间隔时间（秒）
            max_depth: 最大爬取深度
            max_book_details: 每次运行最大爬取的书籍详情数量
        """
        self.request_delay = request_delay
        self.max_depth = max_depth
        self.max_book_details = max_book_details
        
        # 初始化组件
        self.parser = UnifiedParser()
        self.config = CrawlConfig()
        self.client = HttpClient(request_delay=request_delay)
        
        # 状态管理
        self.crawled_urls = set()  # 避免重复爬取
        self.crawled_books = set()  # 已爬取的书籍ID
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'pages_crawled': 0,
            'rankings_crawled': 0,
            'books_crawled': 0,
            'nested_tasks_generated': 0,
            'nested_tasks_executed': 0,
        }
        
        # 任务队列
        self.pending_tasks = []
        self.completed_results = []
    
    async def crawl_with_nesting(self, task_id: str, enable_book_details: bool = True) -> Dict[str, Any]:
        """
        执行嵌套爬取（默认启用书籍详情爬取）
        
        Args:
            task_id: 初始任务ID
            enable_book_details: 是否启用书籍详情爬取（默认True）
            
        Returns:
            完整的爬取结果
        """
        try:
            start_time = time.time()
            
            # 第一层：爬取初始任务
            initial_result = await self._crawl_single_task(task_id, depth=1)
            if not initial_result or not initial_result.get('success'):
                return initial_result
            
            # 收集所有书籍ID用于嵌套爬取
            nested_tasks = self._extract_nested_tasks(initial_result.get('parsed_items', []))
            self.stats['nested_tasks_generated'] = len(nested_tasks)
            
            # 第二层：执行书籍详情爬取（默认启用）
            nested_results = []
            if nested_tasks:
                # 过滤书籍详情任务
                book_detail_tasks = [task for task in nested_tasks if task.get('type') == 'book_detail']
                
                # 如果启用书籍详情爬取，则爬取所有书籍（受max_book_details限制）
                if enable_book_details:
                    limited_tasks = book_detail_tasks[:self.max_book_details]
                    print(f"开始爬取 {len(limited_tasks)} 个书籍详情（总共 {len(book_detail_tasks)} 个）")
                    
                    # 批量执行书籍详情爬取
                    nested_results = await self._crawl_nested_tasks(limited_tasks)
                    self.stats['nested_tasks_executed'] = len(nested_results)
                else:
                    print(f"跳过书籍详情爬取，共 {len(book_detail_tasks)} 个书籍")
            
            # 整合结果
            result = {
                'task_id': task_id,
                'success': True,
                'initial_result': initial_result,
                'nested_results': nested_results,
                'total_nested_tasks': len(nested_tasks),
                'executed_nested_tasks': len(nested_results),
                'book_details_enabled': enable_book_details,
                'stats': self.get_stats(),
                'execution_time': time.time() - start_time,
                'timestamp': time.time()
            }
            
            self.completed_results.append(result)
            return result
            
        except Exception as e:
            return {
                'task_id': task_id,
                'success': False,
                'error': str(e),
                'stats': self.get_stats(),
                'timestamp': time.time()
            }
    
    async def crawl_multiple_with_nesting(self, task_ids: List[str], 
                                        enable_book_details: bool = True) -> List[Dict[str, Any]]:
        """
        并发执行多个嵌套爬取任务（默认启用书籍详情爬取）
        
        Args:
            task_ids: 任务ID列表
            enable_book_details: 是否启用书籍详情爬取（默认True）
            
        Returns:
            爬取结果列表
        """
        print(f"开始执行 {len(task_ids)} 个嵌套爬取任务，书籍详情爬取: {'启用' if enable_book_details else '禁用'}")
        
        tasks = [self.crawl_with_nesting(task_id, enable_book_details) for task_id in task_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'task_id': task_ids[i],
                    'success': False,
                    'error': str(result),
                    'timestamp': time.time()
                })
            else:
                processed_results.append(result)
        
        # 统计结果
        successful_tasks = sum(1 for r in processed_results if r.get('success'))
        total_books_crawled = sum(r.get('executed_nested_tasks', 0) for r in processed_results if r.get('success'))
        
        print(f"嵌套爬取完成: {successful_tasks}/{len(task_ids)} 任务成功，共爬取 {total_books_crawled} 个书籍详情")
        
        return processed_results
    
    async def _crawl_single_task(self, task_id: str, depth: int = 1) -> Dict[str, Any]:
        """
        爬取单个任务
        
        Args:
            task_id: 任务ID
            depth: 当前爬取深度
            
        Returns:
            爬取结果
        """
        if depth > self.max_depth:
            return {'success': False, 'error': f'超过最大爬取深度 {self.max_depth}'}
        
        # 获取任务配置
        task_config = self.config.get_task_config(task_id)
        if not task_config:
            return {'success': False, 'error': f'任务配置不存在: {task_id}'}
        
        # 构建URL
        url = self.config.build_url(task_config)
        
        # 避免重复爬取
        if url in self.crawled_urls:
            return {'success': False, 'error': f'URL已爬取: {url}'}
        
        try:
            # 发送请求
            self.stats['total_requests'] += 1
            raw_data = await self.client.get(url)
            self.stats['successful_requests'] += 1
            self.crawled_urls.add(url)
            
            # 解析数据
            parsed_items = self.parser.parse(raw_data)
            
            # 更新统计
            for item in parsed_items:
                if item.data_type == DataType.PAGE:
                    self.stats['pages_crawled'] += 1
                elif item.data_type == DataType.RANKING:
                    self.stats['rankings_crawled'] += 1
                elif item.data_type == DataType.BOOK:
                    self.stats['books_crawled'] += 1
            
            return {
                'task_id': task_id,
                'task_config': task_config,
                'url': url,
                'success': True,
                'depth': depth,
                'parsed_items': parsed_items,
                'total_items': len(parsed_items),
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            return {
                'task_id': task_id,
                'task_config': task_config,
                'url': url,
                'success': False,
                'error': str(e),
                'depth': depth,
                'timestamp': time.time()
            }
    
    async def _crawl_nested_tasks(self, tasks: List[Dict]) -> List[Dict[str, Any]]:
        """
        爬取嵌套任务列表
        
        Args:
            tasks: 嵌套任务列表
            
        Returns:
            嵌套任务爬取结果
        """
        # 创建临时任务配置
        temp_task_configs = {}
        for task in tasks:
            task_id = task['id']
            temp_task_configs[task_id] = task
        
        # 临时添加到配置中
        original_tasks = self.config._config.get('crawl_tasks', [])
        self.config._config['crawl_tasks'] = original_tasks + list(temp_task_configs.values())
        
        try:
            # 批量爬取（控制并发数）
            semaphore = asyncio.Semaphore(5)  # 最多5个并发
            
            async def crawl_with_semaphore(task):
                async with semaphore:
                    task_id = task['id']
                    book_id = task['params']['novel_id']
                    
                    # 避免重复爬取同一本书
                    if book_id in self.crawled_books:
                        return {'success': False, 'error': f'书籍已爬取: {book_id}'}
                    
                    result = await self._crawl_single_task(task_id, depth=2)
                    if result.get('success'):
                        self.crawled_books.add(book_id)
                    
                    return result
            
            # 执行并发爬取
            crawl_tasks = [crawl_with_semaphore(task) for task in tasks]
            results = await asyncio.gather(*crawl_tasks, return_exceptions=True)
            
            # 处理结果
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    processed_results.append({
                        'task_id': tasks[i]['id'],
                        'success': False,
                        'error': str(result),
                        'timestamp': time.time()
                    })
                else:
                    processed_results.append(result)
            
            return processed_results
            
        finally:
            # 恢复原始配置
            self.config._config['crawl_tasks'] = original_tasks
    
    def _extract_nested_tasks(self, parsed_items: List[ParsedItem]) -> List[Dict]:
        """
        从解析结果中提取嵌套任务
        
        Args:
            parsed_items: 解析后的数据项列表
            
        Returns:
            嵌套任务列表
        """
        nested_tasks = []
        
        for item in parsed_items:
            if item.nested_tasks:
                nested_tasks.extend(item.nested_tasks)
        
        # 去重（基于任务ID）
        unique_tasks = {}
        for task in nested_tasks:
            task_id = task['id']
            if task_id not in unique_tasks:
                unique_tasks[task_id] = task
        
        return list(unique_tasks.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """获取爬取统计信息"""
        total_items = (self.stats['pages_crawled'] + 
                      self.stats['rankings_crawled'] + 
                      self.stats['books_crawled'])
        
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = self.stats['successful_requests'] / self.stats['total_requests']
        
        return {
            **self.stats,
            'total_items': total_items,
            'success_rate': round(success_rate, 2),
            'crawled_urls_count': len(self.crawled_urls),
            'crawled_books_count': len(self.crawled_books)
        }
    
    def get_crawled_data(self) -> Dict[str, List]:
        """获取已爬取的数据"""
        pages = []
        rankings = []
        books = []
        
        for result in self.completed_results:
            if result.get('success'):
                # 处理初始结果
                initial_items = result.get('initial_result', {}).get('parsed_items', [])
                for item in initial_items:
                    if item.data_type == DataType.PAGE:
                        pages.append(item.data)
                    elif item.data_type == DataType.RANKING:
                        rankings.append(item.data)
                    elif item.data_type == DataType.BOOK:
                        books.append(item.data)
                
                # 处理嵌套结果
                nested_results = result.get('nested_results', [])
                for nested_result in nested_results:
                    if nested_result.get('success'):
                        nested_items = nested_result.get('parsed_items', [])
                        for item in nested_items:
                            if item.data_type == DataType.BOOK:
                                books.append(item.data)
        
        return {
            'pages': pages,
            'rankings': rankings,
            'books': books
        }
    
    async def close(self):
        """关闭爬虫连接"""
        await self.client.close()