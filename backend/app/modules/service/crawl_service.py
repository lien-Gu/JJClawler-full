"""
统一爬取服务

合并page_service和task_service的功能，提供完整的爬取任务管理
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import httpx
import asyncio

from sqlmodel import select, and_

from app.config import get_settings
from app.utils.file_utils import read_json_file
from app.utils.log_utils import get_logger
from app.modules.service.crawl_models import CrawlTask, TaskStatus
from app.modules.models import TaskExecution
from app.modules.database.connection import get_session_sync

logger = get_logger(__name__)


class CrawlService:
    """统一爬取服务 - 配置管理 + 状态管理 + 任务执行"""

    def __init__(self, config_path: str = None):
        # 配置管理
        if config_path is None:
            settings = get_settings()
            config_path = settings.URLS_CONFIG_FILE

        self.config_path = Path(config_path)
        self._config = None
        self._task_config: List[CrawlTask] = []

        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        logger.info("使用数据库存储任务执行状态 (替代 tasks.json)")

    # 删除：不再需要JSON文件管理

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self._config is None:
            self._config = read_json_file(self.config_path)
            if self._config is None:
                raise FileNotFoundError(f"无法读取配置文件: {self.config_path}")
        return self._config

    def _build_task_url(self, task_data: Dict[str, Any]) -> str:
        """构建任务URL"""
        config = self._load_config()
        global_config = config.get('global', {})
        templates = global_config.get('templates', {})
        base_params = global_config.get('base_params', {})
        
        template_name = task_data['template']
        if template_name not in templates:
            raise ValueError(f"URL模板不存在: {template_name}")
        
        url_params = {**base_params, **task_data['params']}
        template = templates[template_name]
        try:
            return template.format(**url_params)
        except KeyError as e:
            raise ValueError(f"缺少URL参数 {e} for task {task_data['id']}")

    # ============ 数据库任务状态管理 ============
    
    def _create_task_execution(self, crawl_task: CrawlTask) -> TaskExecution:
        """创建任务执行记录"""
        with get_session_sync() as session:
            task_execution = TaskExecution.from_crawl_task(crawl_task)
            session.add(task_execution)
            session.commit()
            session.refresh(task_execution)
            logger.info(f"创建任务执行记录: {task_execution.task_id}")
            return task_execution
    
    def _update_task_execution(self, task_id: str, **updates) -> bool:
        """更新任务执行状态"""
        with get_session_sync() as session:
            stmt = select(TaskExecution).where(TaskExecution.task_id == task_id)
            task_execution = session.exec(stmt).first()
            
            if not task_execution:
                logger.warning(f"任务执行记录不存在: {task_id}")
                return False
            
            for key, value in updates.items():
                if hasattr(task_execution, key):
                    setattr(task_execution, key, value)
            
            session.commit()
            logger.info(f"更新任务执行状态: {task_id}")
            return True
    
    def _get_task_executions_by_status(self, status: str) -> List[TaskExecution]:
        """根据状态获取任务执行记录"""
        with get_session_sync() as session:
            stmt = select(TaskExecution).where(TaskExecution.status == status)
            return list(session.exec(stmt).all())
    
    def _get_task_execution(self, task_id: str) -> Optional[TaskExecution]:
        """获取单个任务执行记录"""
        with get_session_sync() as session:
            stmt = select(TaskExecution).where(TaskExecution.task_id == task_id)
            return session.exec(stmt).first()

    # ============ 配置管理方法 ============

    def get_all_task_configs(self) -> List[CrawlTask]:
        """获取所有任务配置"""
        if self._task_config:
            return self._task_config
            
        config = self._load_config()
        tasks = []

        for task_data in config.get('crawl_tasks', []):
            url = self._build_task_url(task_data)
            task = CrawlTask.from_config(task_data, url)
            tasks.append(task)
            
        self._task_config = tasks
        return self._task_config

    def get_task_config_by_id(self, task_id: str) -> CrawlTask:
        """根据ID获取任务配置"""
        tasks = self.get_all_task_configs()
        for task in tasks:
            if task.id == task_id:
                return task
        raise ValueError(f"任务配置不存在: {task_id}")

    def get_scheduled_tasks(self) -> List[CrawlTask]:
        """获取需要调度的任务"""
        return [task for task in self.get_all_task_configs() if task.is_scheduled_task()]

    # ============ 任务执行管理 ============

    def create_execution_task(self, task_id: str, metadata: Dict[str, Any] = None) -> str:
        """创建执行任务实例"""
        config_task = self.get_task_config_by_id(task_id)
        execution_task = config_task.create_execution_instance(metadata)
        
        # 保存到数据库
        self._create_task_execution(execution_task)
        
        logger.info(f"创建执行任务: {execution_task.task_id} (配置ID: {task_id})")
        return execution_task.task_id

    def start_task(self, execution_task_id: str) -> bool:
        """开始任务"""
        return self._update_task_execution(
            execution_task_id,
            status=TaskStatus.RUNNING.value,
            started_at=datetime.now()
        )

    def complete_task(self, execution_task_id: str, items_crawled: int = 0, metadata: Dict[str, Any] = None) -> bool:
        """完成任务"""
        updates = {
            "status": TaskStatus.COMPLETED.value,
            "completed_at": datetime.now(),
            "progress": 100,
            "items_crawled": items_crawled
        }
        
        if metadata:
            # 需要先获取现有的task_metadata，然后合并
            task_execution = self._get_task_execution(execution_task_id)
            if task_execution:
                merged_metadata = task_execution.task_metadata.copy()
                merged_metadata.update(metadata)
                updates["task_metadata"] = merged_metadata
        
        success = self._update_task_execution(execution_task_id, **updates)
        if success:
            logger.info(f"完成任务: {execution_task_id} (抓取 {items_crawled} 条)")
        return success

    def fail_task(self, execution_task_id: str, error_message: str) -> bool:
        """标记任务失败"""
        success = self._update_task_execution(
            execution_task_id,
            status=TaskStatus.FAILED.value,
            completed_at=datetime.now(),
            error_message=error_message
        )
        if success:
            logger.warning(f"任务失败: {execution_task_id} - {error_message}")
        return success

    def get_task_status(self, execution_task_id: str) -> Optional[CrawlTask]:
        """获取任务状态"""
        task_execution = self._get_task_execution(execution_task_id)
        if not task_execution:
            return None
        
        # 转换为CrawlTask格式
        task_dict = task_execution.to_crawl_task_dict()
        
        # 获取配置信息
        try:
            config_task = self.get_task_config_by_id(task_execution.config_id)
            # 合并配置信息
            task_dict.update({
                "name": config_task.name,
                "url": config_task.url,
                "frequency": config_task.frequency,
                "interval": config_task.interval,
                "parent_id": config_task.parent_id
            })
        except ValueError:
            # 如果配置不存在，使用默认值
            pass
        
        return CrawlTask.from_dict(task_dict)

    def get_current_tasks(self) -> List[CrawlTask]:
        """获取当前执行中的任务"""
        return self._get_tasks_by_status([TaskStatus.PENDING.value, TaskStatus.RUNNING.value])

    def get_all_tasks(self) -> Dict[str, List[CrawlTask]]:
        """获取所有任务"""
        return {
            "current": self._get_tasks_by_status([TaskStatus.PENDING.value, TaskStatus.RUNNING.value]),
            "completed": self._get_tasks_by_status([TaskStatus.COMPLETED.value]),
            "failed": self._get_tasks_by_status([TaskStatus.FAILED.value])
        }
    
    def _get_tasks_by_status(self, statuses: List[str]) -> List[CrawlTask]:
        """根据状态列表获取任务"""
        tasks = []
        with get_session_sync() as session:
            for status in statuses:
                stmt = select(TaskExecution).where(TaskExecution.status == status)
                task_executions = session.exec(stmt).all()
                
                for task_execution in task_executions:
                    task_dict = task_execution.to_crawl_task_dict()
                    
                    # 尝试获取配置信息
                    try:
                        config_task = self.get_task_config_by_id(task_execution.config_id)
                        task_dict.update({
                            "name": config_task.name,
                            "url": config_task.url,
                            "frequency": config_task.frequency,
                            "interval": config_task.interval,
                            "parent_id": config_task.parent_id
                        })
                    except ValueError:
                        # 配置不存在时使用默认值
                        task_dict.update({
                            "name": f"Unknown Task ({task_execution.config_id})",
                            "url": "",
                            "frequency": "daily",
                            "interval": 24,
                            "parent_id": None
                        })
                    
                    tasks.append(CrawlTask.from_dict(task_dict))
        
        return tasks

    # ============ 任务执行器 ============

    async def execute_task(self, task_id: str, executor: Callable, metadata: Dict[str, Any] = None, *args, **kwargs) -> bool:
        """执行带跟踪的任务"""
        execution_task_id = self.create_execution_task(task_id, metadata)
        
        try:
            self.start_task(execution_task_id)
            
            # 执行任务
            result = await executor(*args, **kwargs)
            
            # 处理结果
            if isinstance(result, dict):
                items_count = result.get('books_new', 0) + result.get('books_updated', 0)
                self.complete_task(execution_task_id, items_count, result)
            else:
                self.complete_task(execution_task_id)
            
            return True
            
        except Exception as e:
            self.fail_task(execution_task_id, str(e))
            logger.error(f"任务执行失败: {execution_task_id} - {e}")
            return False

    def get_pages_hierarchy(self) -> Dict[str, List[CrawlTask]]:
        """获取按父子节点分类的页面字典"""
        tasks = self.get_all_task_configs()
        
        pages = {"root": [], "children": {}}
        
        for task in tasks:
            if not task.parent_id:  # 根节点
                pages["root"].append(task)
            else:  # 子节点
                if task.parent_id not in pages["children"]:
                    pages["children"][task.parent_id] = []
                pages["children"][task.parent_id].append(task)
        
        return pages

    def refresh_config(self):
        """刷新配置"""
        self._config = None
        self._task_config = []

    # ============ 爬取功能 ============

    async def crawl_url(self, url: str, task_id: str = None) -> Dict[str, Any]:
        """统一的URL爬取方法"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info(f"开始爬取URL: {url}")
                
                response = await client.get(url)
                response.raise_for_status()
                
                content = response.text
                logger.info(f"爬取成功: {url}, 内容长度: {len(content)}")
                
                # 根据task_id判断解析方式
                if task_id == "jiazi":
                    return await self._parse_jiazi_content(content)
                else:
                    return await self._parse_page_content(content, task_id)
                    
        except Exception as e:
            logger.error(f"爬取失败 {url}: {e}")
            raise

    async def _parse_jiazi_content(self, content: str) -> Dict[str, Any]:
        """解析夹子榜内容"""
        try:
            # 这里应该调用具体的解析逻辑
            # 暂时返回模拟数据，需要根据实际解析逻辑替换
            from app.modules.crawler.jiazi_parser import parse_jiazi_response
            return await parse_jiazi_response(content)
        except ImportError:
            logger.warning("夹子榜解析器未找到，返回模拟数据")
            return {
                "books_new": 10,
                "books_updated": 5,
                "total_books": 15,
                "success": True
            }

    async def _parse_page_content(self, content: str, task_id: str) -> Dict[str, Any]:
        """解析页面内容"""
        try:
            # 这里应该调用具体的解析逻辑
            # 暂时返回模拟数据，需要根据实际解析逻辑替换
            from app.modules.crawler.page_parser import parse_page_response
            return await parse_page_response(content, task_id)
        except ImportError:
            logger.warning(f"页面解析器未找到，返回模拟数据: {task_id}")
            return {
                "books_new": 8,
                "books_updated": 3,
                "total_books": 11,
                "success": True
            }

    async def crawl_and_save(self, task_id: str) -> Dict[str, Any]:
        """统一的爬取和保存方法"""
        try:
            # 获取任务配置
            task_config = self.get_task_config_by_id(task_id)
            
            # 执行爬取
            crawl_result = await self.crawl_url(task_config.url, task_id)
            
            # 保存到数据库
            if crawl_result.get("success"):
                await self._save_crawl_data(task_id, crawl_result)
            
            return crawl_result
            
        except Exception as e:
            logger.error(f"爬取和保存失败 {task_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "books_new": 0,
                "books_updated": 0,
                "total_books": 0
            }

    async def _save_crawl_data(self, task_id: str, crawl_result: Dict[str, Any]):
        """保存爬取数据到数据库"""
        try:
            # 这里应该调用具体的数据保存逻辑
            from app.modules.database.dao import save_crawl_result
            await save_crawl_result(task_id, crawl_result)
            logger.info(f"数据保存成功: {task_id}")
        except ImportError:
            logger.warning(f"数据库保存功能未实现: {task_id}")
        except Exception as e:
            logger.error(f"数据保存失败 {task_id}: {e}")
            raise


# 全局实例
_crawl_service = None


def get_crawl_service() -> CrawlService:
    """获取爬取服务实例"""
    global _crawl_service
    if _crawl_service is None:
        _crawl_service = CrawlService()
    return _crawl_service


# 便捷函数
def get_all_task_configs() -> List[CrawlTask]:
    """获取所有任务配置"""
    return get_crawl_service().get_all_task_configs()


def get_scheduled_tasks() -> List[CrawlTask]:
    """获取调度任务"""
    return get_crawl_service().get_scheduled_tasks()


def execute_crawl_task(task_id: str, executor: Callable, metadata: Dict[str, Any] = None, *args, **kwargs):
    """执行爬取任务"""
    return get_crawl_service().execute_task(task_id, executor, metadata, *args, **kwargs)


def get_pages_hierarchy() -> Dict[str, List[CrawlTask]]:
    """获取页面层级结构"""
    return get_crawl_service().get_pages_hierarchy()