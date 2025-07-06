"""
统一爬虫管理器，整合夹子榜和页面爬虫功能
"""
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .base import BaseCrawler
from .jiazi_parser import JiaziParser
from .page_parser import PageParser


class CrawlerManager:
    """爬虫管理器，负责统一管理所有爬虫任务"""
    
    def __init__(self, rate_limit: float = 1.0):
        """
        初始化爬虫管理器
        
        Args:
            rate_limit: 请求间隔时间（秒）
        """
        self.rate_limit = rate_limit
        self.jiazi_crawler = BaseCrawler(JiaziParser(), rate_limit)
        self.page_crawler = BaseCrawler(PageParser(), rate_limit)
        
        # 任务统计
        self.total_stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'total_items': 0,
            'start_time': None,
            'end_time': None
        }
    
    async def crawl_by_type(self, task_type: str, task_ids: Union[str, List[str]]) -> List[Dict[str, Any]]:
        """
        根据任务类型进行爬取
        
        Args:
            task_type: 任务类型 ("jiazi" 或 "page")
            task_ids: 任务ID或任务ID列表
            
        Returns:
            爬取结果列表
        """
        if isinstance(task_ids, str):
            task_ids = [task_ids]
        
        self.total_stats['start_time'] = time.time()
        self.total_stats['total_tasks'] += len(task_ids)
        
        if task_type == "jiazi":
            results = await self.jiazi_crawler.crawl_multiple_tasks(task_ids)
        elif task_type == "page":
            results = await self.page_crawler.crawl_multiple_tasks(task_ids)
        else:
            raise ValueError(f"不支持的任务类型: {task_type}")
        
        # 更新统计信息
        for result in results:
            if result.get('success'):
                self.total_stats['successful_tasks'] += 1
                self.total_stats['total_items'] += result.get('valid_items', 0)
            else:
                self.total_stats['failed_tasks'] += 1
        
        self.total_stats['end_time'] = time.time()
        
        return results
    
    async def crawl_jiazi(self) -> Dict[str, Any]:
        """
        爬取夹子榜
        
        Returns:
            爬取结果
        """
        results = await self.crawl_by_type("jiazi", ["jiazi"])
        return results[0] if results else {"success": False, "error": "爬取失败"}
    
    async def crawl_page(self, page_id: str) -> Dict[str, Any]:
        """
        爬取指定页面
        
        Args:
            page_id: 页面ID
            
        Returns:
            爬取结果
        """
        results = await self.crawl_by_type("page", [page_id])
        return results[0] if results else {"success": False, "error": "爬取失败"}
    
    async def crawl_multiple_pages(self, page_ids: List[str]) -> List[Dict[str, Any]]:
        """
        爬取多个页面
        
        Args:
            page_ids: 页面ID列表
            
        Returns:
            爬取结果列表
        """
        return await self.crawl_by_type("page", page_ids)
    
    async def crawl_all_tasks(self) -> List[Dict[str, Any]]:
        """
        爬取所有配置的任务
        
        Returns:
            爬取结果列表
        """
        from .base import CrawlConfig
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        
        # 按类型分组任务
        jiazi_tasks = [task["id"] for task in all_tasks if task["type"] == "jiazi"]
        page_tasks = [task["id"] for task in all_tasks if task["type"] == "page"]
        
        all_results = []
        
        # 爬取夹子榜任务
        if jiazi_tasks:
            jiazi_results = await self.crawl_by_type("jiazi", jiazi_tasks)
            all_results.extend(jiazi_results)
        
        # 爬取页面任务
        if page_tasks:
            page_results = await self.crawl_by_type("page", page_tasks)
            all_results.extend(page_results)
        
        return all_results
    
    async def crawl_tasks_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        根据分类爬取任务
        
        Args:
            category: 任务分类（如 "yq", "ca", "ys"等）
            
        Returns:
            爬取结果列表
        """
        from .base import CrawlConfig
        config = CrawlConfig()
        all_tasks = config.get_all_tasks()
        
        # 筛选匹配的任务
        matching_tasks = []
        for task in all_tasks:
            task_id = task["id"]
            # 匹配主分类或子分类
            if task_id == category or task_id.startswith(f"{category}."):
                matching_tasks.append(task_id)
        
        if not matching_tasks:
            return []
        
        # 确定任务类型（假设同一分类的任务类型相同）
        first_task = next(task for task in all_tasks if task["id"] in matching_tasks)
        task_type = first_task["type"]
        
        return await self.crawl_by_type(task_type, matching_tasks)
    
    def get_crawler_stats(self) -> Dict[str, Any]:
        """获取爬虫统计信息"""
        jiazi_stats = self.jiazi_crawler.get_stats()
        page_stats = self.page_crawler.get_stats()
        
        return {
            'total_stats': self.total_stats,
            'jiazi_stats': jiazi_stats,
            'page_stats': page_stats,
            'combined_stats': {
                'total_requests': jiazi_stats['total_requests'] + page_stats['total_requests'],
                'successful_requests': jiazi_stats['successful_requests'] + page_stats['successful_requests'],
                'failed_requests': jiazi_stats['failed_requests'] + page_stats['failed_requests'],
                'total_items': jiazi_stats['total_items'] + page_stats['total_items'],
                'valid_items': jiazi_stats['valid_items'] + page_stats['valid_items'],
            }
        }
    
    def get_available_tasks(self) -> List[Dict[str, Any]]:
        """获取所有可用的任务配置"""
        from .base import CrawlConfig
        config = CrawlConfig()
        return config.get_all_tasks()
    
    def get_task_config(self, task_id: str) -> Optional[Dict]:
        """获取指定任务的配置"""
        from .base import CrawlConfig
        config = CrawlConfig()
        return config.get_task_config(task_id)
    
    async def close(self):
        """关闭所有爬虫连接"""
        await self.jiazi_crawler.close()
        await self.page_crawler.close()


class TaskRecorder:
    """任务记录器，用于记录爬取任务的执行情况"""
    
    def __init__(self):
        self.tasks_dir = Path(__file__).parent.parent.parent / "data" / "tasks"
        self.tasks_dir.mkdir(exist_ok=True)
        self.tasks_file = self.tasks_dir / "tasks.json"
    
    def save_task_result(self, task_result: Dict[str, Any]) -> None:
        """
        保存任务执行结果
        
        Args:
            task_result: 任务执行结果
        """
        try:
            # 读取现有任务记录
            existing_tasks = self._load_existing_tasks()
            
            # 生成任务记录
            task_record = {
                'task_id': task_result.get('task_id'),
                'task_type': task_result.get('task_config', {}).get('type'),
                'status': 'success' if task_result.get('success') else 'failed',
                'start_time': datetime.fromtimestamp(task_result.get('timestamp', time.time())).isoformat(),
                'end_time': datetime.now().isoformat(),
                'url': task_result.get('url'),
                'total_items': task_result.get('total_items', 0),
                'valid_items': task_result.get('valid_items', 0),
                'error': task_result.get('error'),
                'data_sample': task_result.get('data', [])[:3] if task_result.get('data') else None  # 保存前3条作为样本
            }
            
            # 添加到当前任务列表
            existing_tasks['current_tasks'].append(task_record)
            
            # 移动已完成的任务到历史记录
            self._archive_completed_tasks(existing_tasks)
            
            # 保存任务记录
            with open(self.tasks_file, 'w', encoding='utf-8') as f:
                json.dump(existing_tasks, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存任务记录失败: {e}")
    
    def _load_existing_tasks(self) -> Dict:
        """加载现有任务记录"""
        if not self.tasks_file.exists():
            return {
                'current_tasks': [],
                'completed_tasks': [],
                'failed_tasks': []
            }
        
        try:
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {
                'current_tasks': [],
                'completed_tasks': [],
                'failed_tasks': []
            }
    
    def _archive_completed_tasks(self, tasks_data: Dict) -> None:
        """将已完成的任务移动到历史记录"""
        current_tasks = tasks_data['current_tasks']
        completed_tasks = tasks_data['completed_tasks']
        failed_tasks = tasks_data['failed_tasks']
        
        # 保留最近10个任务在current_tasks中
        if len(current_tasks) > 10:
            for task in current_tasks[:-10]:
                if task['status'] == 'success':
                    completed_tasks.append(task)
                else:
                    failed_tasks.append(task)
            
            tasks_data['current_tasks'] = current_tasks[-10:]
        
        # 限制历史记录数量
        tasks_data['completed_tasks'] = completed_tasks[-100:]  # 保留最近100个成功任务
        tasks_data['failed_tasks'] = failed_tasks[-50:]        # 保留最近50个失败任务
    
    def get_task_status(self) -> Dict:
        """获取任务状态"""
        return self._load_existing_tasks()