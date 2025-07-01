"""
统一爬取服务

合并page_service和task_service的功能，提供完整的爬取任务管理
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime

from app.config import get_settings
from app.utils.file_utils import read_json_file, write_json_file
from app.utils.log_utils import get_logger
from app.utils.time_utils import to_iso_string
from app.modules.service.crawl_models import CrawlTask, TaskStatus

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
        self._task_configs: List[CrawlTask] = []

        # 状态管理
        settings = get_settings()
        self.tasks_file = Path(f"{settings.DATA_DIR}/tasks/tasks.json")
        self._ensure_tasks_file()

        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

    def _ensure_tasks_file(self):
        """确保任务文件存在"""
        default_data = {
            "current_tasks": [],
            "completed_tasks": [],
            "failed_tasks": [],
            "last_updated": to_iso_string(datetime.now())
        }
        if not self.tasks_file.exists():
            self.tasks_file.parent.mkdir(parents=True, exist_ok=True)
            write_json_file(self.tasks_file, default_data)
            logger.info("任务文件初始化完成")

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

    def _read_tasks(self) -> Dict[str, Any]:
        """读取任务数据"""
        return read_json_file(self.tasks_file, default={
            "current_tasks": [],
            "completed_tasks": [],
            "failed_tasks": []
        })

    def _write_tasks(self, data: Dict[str, Any]):
        """写入任务数据"""
        data["last_updated"] = to_iso_string(datetime.now())
        write_json_file(self.tasks_file, data)

    # ============ 配置管理方法 ============

    def get_all_task_configs(self) -> List[CrawlTask]:
        """获取所有任务配置"""
        if self._task_configs:
            return self._task_configs
            
        config = self._load_config()
        tasks = []

        for task_data in config.get('crawl_tasks', []):
            url = self._build_task_url(task_data)
            task = CrawlTask.from_config(task_data, url)
            tasks.append(task)
            
        self._task_configs = tasks
        return self._task_configs

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
        
        data = self._read_tasks()
        data["current_tasks"].append(execution_task.to_dict())
        self._write_tasks(data)
        
        logger.info(f"创建执行任务: {execution_task.task_id} (配置ID: {task_id})")
        return execution_task.task_id

    def start_task(self, execution_task_id: str) -> bool:
        """开始任务"""
        data = self._read_tasks()
        for task_data in data["current_tasks"]:
            if task_data["task_id"] == execution_task_id:
                task = CrawlTask.from_dict(task_data)
                task.start()
                
                # 更新数据
                task_data.update(task.to_dict())
                self._write_tasks(data)
                
                logger.info(f"开始任务: {execution_task_id}")
                return True
        return False

    def complete_task(self, execution_task_id: str, items_crawled: int = 0, metadata: Dict[str, Any] = None) -> bool:
        """完成任务"""
        data = self._read_tasks()
        
        for i, task_data in enumerate(data["current_tasks"]):
            if task_data["task_id"] == execution_task_id:
                task = CrawlTask.from_dict(task_data)
                task.complete(items_crawled, metadata)
                
                # 移动到完成列表
                data["completed_tasks"].append(task.to_dict())
                data["current_tasks"].pop(i)
                self._write_tasks(data)
                
                logger.info(f"完成任务: {execution_task_id} (抓取 {items_crawled} 条)")
                return True
        return False

    def fail_task(self, execution_task_id: str, error_message: str) -> bool:
        """标记任务失败"""
        data = self._read_tasks()
        
        for i, task_data in enumerate(data["current_tasks"]):
            if task_data["task_id"] == execution_task_id:
                task = CrawlTask.from_dict(task_data)
                task.fail(error_message)
                
                # 移动到失败列表
                data["failed_tasks"].append(task.to_dict())
                data["current_tasks"].pop(i)
                self._write_tasks(data)
                
                logger.warning(f"任务失败: {execution_task_id} - {error_message}")
                return True
        return False

    def get_task_status(self, execution_task_id: str) -> Optional[CrawlTask]:
        """获取任务状态"""
        data = self._read_tasks()
        all_tasks = data.get("current_tasks", []) + data.get("completed_tasks", []) + data.get("failed_tasks", [])
        
        for task_data in all_tasks:
            if task_data.get("task_id") == execution_task_id:
                return CrawlTask.from_dict(task_data)
        return None

    def get_current_tasks(self) -> List[CrawlTask]:
        """获取当前执行中的任务"""
        data = self._read_tasks()
        return [CrawlTask.from_dict(task_data) for task_data in data["current_tasks"]]

    def get_all_tasks(self) -> Dict[str, List[CrawlTask]]:
        """获取所有任务"""
        data = self._read_tasks()
        
        return {
            "current": [CrawlTask.from_dict(task_data) for task_data in data.get("current_tasks", [])],
            "completed": [CrawlTask.from_dict(task_data) for task_data in data.get("completed_tasks", [])],
            "failed": [CrawlTask.from_dict(task_data) for task_data in data.get("failed_tasks", [])]
        }

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
        self._task_configs = []


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