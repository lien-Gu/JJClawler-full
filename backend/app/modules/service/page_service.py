"""
页面服务模块 - 重构版本

简化的页面配置管理，支持扁平化的任务导向配置格式。
设计原则：
1. 扁平化结构：避免深层嵌套，数据结构清晰
2. 任务导向：以爬取任务为中心的配置方式
3. 模板化URL：统一的URL模板和参数管理
4. 高效查询：支持快速的任务查找和层级构建
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass

from app.config import get_settings
from app.utils.file_utils import read_json_file
from app.utils.log_utils import get_logger

logger = get_logger(__name__)


@dataclass
class CrawlTask:
    """爬取任务数据类"""
    id: str
    name: str
    type: str
    template: str
    params: Dict[str, Any]
    frequency: str
    interval: int
    parent: Optional[str]
    level: int
    display_order: int
    
    def build_url(self, templates: Dict[str, str], global_params: Dict[str, Any]) -> str:
        """构建完整的爬取URL"""
        if self.template not in templates:
            raise ValueError(f"URL模板不存在: {self.template}")
        
        # 合并全局参数和任务参数
        url_params = {**global_params, **self.params}
        
        # 获取模板并格式化
        template = templates[self.template]
        try:
            return template.format(**url_params)
        except KeyError as e:
            raise ValueError(f"缺少URL参数 {e} for task {self.id}")


@dataclass
class Category:
    """分类数据类"""
    id: str
    name: str
    level: int
    parent: Optional[str]
    display_order: int


class PageService:
    """
    重构的页面服务类
    
    提供基于新配置格式的页面管理功能：
    - 扁平化的任务配置管理
    - 高效的URL构建
    - 简化的层级关系处理
    - 缓存优化
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化页面服务
        
        Args:
            config_path: 配置文件路径
        """
        if config_path is None:
            settings = get_settings()
            config_path = settings.URLS_CONFIG_FILE
            
        self.config_path = Path(config_path)
        self._config_cache = None
        self._cache_timestamp = None
        self._cache_ttl = timedelta(minutes=30)
        
        # 内部缓存
        self._tasks_cache: List[CrawlTask] = []
        self._categories_cache: List[Category] = []
        self._tasks_by_id: Dict[str, CrawlTask] = {}
        self._tasks_by_parent: Dict[str, List[CrawlTask]] = {}
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    def _load_config(self, force_refresh: bool = False) -> Dict[str, Any]:
        """加载并缓存配置文件"""
        current_time = datetime.now()
        
        # 检查缓存是否有效
        if (not force_refresh and 
            self._config_cache is not None and 
            self._cache_timestamp is not None and 
            current_time - self._cache_timestamp < self._cache_ttl):
            return self._config_cache
        
        # 读取配置文件
        config = read_json_file(self.config_path)
        if config is None:
            logger.error("页面配置加载失败")
            raise FileNotFoundError(f"无法读取配置文件: {self.config_path}")
        
        # 解析配置并构建缓存
        self._parse_config(config)
        
        # 更新缓存
        self._config_cache = config
        self._cache_timestamp = current_time
        
        logger.debug("页面配置加载成功")
        return config
    
    def _parse_config(self, config: Dict[str, Any]):
        """解析配置文件并构建内部缓存"""
        # 解析爬取任务
        self._tasks_cache = []
        self._tasks_by_id = {}
        self._tasks_by_parent = {}
        
        for task_data in config.get('crawl_tasks', []):
            task = CrawlTask(
                id=task_data['id'],
                name=task_data['name'],
                type=task_data['type'],
                template=task_data['template'],
                params=task_data['params'],
                frequency=task_data['schedule']['frequency'],
                interval=task_data['schedule']['interval'],
                parent=task_data['category']['parent'],
                level=task_data['category']['level'],
                display_order=task_data['category']['display_order']
            )
            
            self._tasks_cache.append(task)
            self._tasks_by_id[task.id] = task
            
            # 按父类分组
            if task.parent not in self._tasks_by_parent:
                self._tasks_by_parent[task.parent] = []
            self._tasks_by_parent[task.parent].append(task)
        
        # 从任务中提取分类信息（level=1的任务作为分类）
        self._categories_cache = []
        category_tasks = [task for task in self._tasks_cache if task.level == 1]
        for task in category_tasks:
            category = Category(
                id=task.id,
                name=task.name,
                level=task.level,
                parent=task.parent,
                display_order=task.display_order
            )
            self._categories_cache.append(category)
    
    def get_all_crawl_tasks(self) -> List[CrawlTask]:
        """获取所有爬取任务"""
        self._load_config()
        return self._tasks_cache.copy()
    
    def get_task_by_id(self, task_id: str) -> Optional[CrawlTask]:
        """根据ID获取任务"""
        self._load_config()
        return self._tasks_by_id.get(task_id)
    
    def get_tasks_by_parent(self, parent_id: Optional[str]) -> List[CrawlTask]:
        """获取指定父级的所有子任务"""
        self._load_config()
        tasks = self._tasks_by_parent.get(parent_id, [])
        return sorted(tasks, key=lambda t: t.display_order)
    
    def get_all_categories(self) -> List[Category]:
        """获取所有分类"""
        self._load_config()
        return sorted(self._categories_cache, key=lambda c: c.display_order)
    
    def build_task_url(self, task_id: str) -> str:
        """构建任务的爬取URL"""
        config = self._load_config()
        task = self.get_task_by_id(task_id)
        
        if not task:
            raise ValueError(f"任务不存在: {task_id}")
        
        global_config = config.get('global', {})
        templates = global_config.get('templates', {})
        base_params = global_config.get('base_params', {})
        
        return task.build_url(templates, base_params)
    
    def get_scheduled_tasks(self) -> List[CrawlTask]:
        """获取所有有调度配置的任务"""
        return [task for task in self.get_all_crawl_tasks() if task.interval > 0]
    
    def get_tasks_by_frequency(self, frequency: str) -> List[CrawlTask]:
        """根据频率获取任务"""
        return [task for task in self.get_all_crawl_tasks() if task.frequency == frequency]
    
    # ==================== 兼容旧API的方法 ====================
    
    def get_all_pages(self) -> List[Dict[str, Any]]:
        """
        兼容旧API：获取页面配置列表
        
        将新的任务结构转换为旧的页面格式
        """
        try:
            categories = self.get_all_categories()
            all_tasks = self.get_all_crawl_tasks()
            pages = []
            
            # 添加根级别的任务（如jiazi）
            root_tasks = self.get_tasks_by_parent(None)
            for task in root_tasks:
                pages.append({
                    'page_id': task.id,
                    'name': task.name,
                    'type': task.type,
                    'frequency': task.frequency,
                    'rankings': [{
                        'ranking_id': task.id,
                        'name': task.name,
                        'update_frequency': task.frequency
                    }],
                    'parent_id': None
                })
            
            # 添加分类页面
            for category in categories:
                child_tasks = self.get_tasks_by_parent(category.id)
                rankings = []
                
                for task in child_tasks:
                    rankings.append({
                        'ranking_id': task.id,
                        'name': task.name,
                        'update_frequency': task.frequency
                    })
                
                pages.append({
                    'page_id': category.id,
                    'name': category.name,
                    'type': 'category',
                    'frequency': 'daily',  # 分类页面默认频率
                    'rankings': rankings,
                    'parent_id': None
                })
            
            logger.info(f"页面配置获取成功: {len(pages)} 个页面")
            return pages
            
        except Exception as e:
            logger.error(f"获取页面配置失败: {e}")
            return []
    
    def get_ranking_channels(self) -> List[Dict[str, str]]:
        """
        兼容旧API：获取排行榜频道列表
        """
        try:
            tasks = self.get_all_crawl_tasks()
            channels = []
            
            for task in tasks:
                channels.append({
                    'channel': task.id,
                    'name': task.name,
                    'frequency': task.frequency,
                    'page_name': self._get_category_name(task.parent) if task.parent else '根页面'
                })
            
            logger.info(f"频道列表获取成功: {len(channels)} 个频道")
            return channels
            
        except Exception as e:
            logger.error(f"获取频道列表失败: {e}")
            return []
    
    def _get_category_name(self, category_id: str) -> str:
        """获取分类名称"""
        for category in self._categories_cache:
            if category.id == category_id:
                return category.name
        return category_id
    
    def get_page_statistics(self) -> Dict[str, Any]:
        """
        兼容旧API：获取页面统计信息
        """
        try:
            categories = self.get_all_categories()
            tasks = self.get_all_crawl_tasks()
            root_tasks = self.get_tasks_by_parent(None)
            
            return {
                'total_pages': len(categories) + len(root_tasks),
                'root_pages': len(categories) + len(root_tasks),
                'sub_pages': len(tasks) - len(root_tasks),
                'total_rankings': len(tasks),
                'config_path': str(self.config_path),
                'cache_valid': self._cache_timestamp is not None,
                'last_updated': self._cache_timestamp.isoformat() if self._cache_timestamp else None
            }
            
        except Exception as e:
            logger.error(f"获取页面统计失败: {e}")
            return {
                'total_pages': 0,
                'root_pages': 0,
                'sub_pages': 0,
                'total_rankings': 0,
                'error': str(e)
            }
    
    def refresh_config(self):
        """强制刷新配置缓存"""
        try:
            self._load_config(force_refresh=True)
            logger.info("页面配置缓存已刷新")
        except Exception as e:
            logger.error(f"刷新配置缓存失败: {e}")
            raise


# 全局页面服务实例
_page_service: Optional[PageService] = None


def get_page_service() -> PageService:
    """获取全局页面服务实例"""
    global _page_service
    if _page_service is None:
        _page_service = PageService()
    return _page_service


# 新的便捷函数
def get_all_crawl_tasks() -> List[CrawlTask]:
    """获取所有爬取任务"""
    return get_page_service().get_all_crawl_tasks()


def get_task_by_id(task_id: str) -> Optional[CrawlTask]:
    """根据ID获取任务"""
    return get_page_service().get_task_by_id(task_id)


def build_task_url(task_id: str) -> str:
    """构建任务URL"""
    return get_page_service().build_task_url(task_id)


def get_scheduled_tasks() -> List[CrawlTask]:
    """获取所有调度任务"""
    return get_page_service().get_scheduled_tasks()


# 兼容旧API的便捷函数
def get_all_pages() -> List[Dict[str, Any]]:
    """便捷函数：获取所有页面配置（兼容旧API）"""
    return get_page_service().get_all_pages()


def get_ranking_channels() -> List[Dict[str, str]]:
    """便捷函数：获取所有排行榜频道（兼容旧API）"""
    return get_page_service().get_ranking_channels()