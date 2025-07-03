"""
任务管理器

简化的任务管理，只在需要详细跟踪时才创建TaskExecution记录
"""

from typing import List, Dict, Any
from pathlib import Path

from app.config import get_settings
from app.utils.file_utils import read_json_file
from app.utils.log_utils import get_logger
from app.modules.task.models import TaskConfig

logger = get_logger(__name__)


class TaskManager:
    """任务管理器 - 配置管理 + 简化的执行跟踪"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            settings = get_settings()
            config_path = settings.URLS_CONFIG_FILE

        self.config_path = Path(config_path)
        self._config = None
        self._task_configs: List[TaskConfig] = []

        if not self.config_path.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")

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
        global_config = config.get("global", {})
        templates = global_config.get("templates", {})
        base_params = global_config.get("base_params", {})

        template_name = task_data["template"]
        if template_name not in templates:
            raise ValueError(f"URL模板不存在: {template_name}")

        url_params = {**base_params, **task_data["params"]}
        template = templates[template_name]
        try:
            return template.format(**url_params)
        except KeyError as e:
            raise ValueError(f"缺少URL参数 {e} for task {task_data['id']}")

    def get_all_task_configs(self) -> List[TaskConfig]:
        """获取所有任务配置"""
        if self._task_configs:
            return self._task_configs

        config = self._load_config()
        configs = []

        for task_data in config.get("crawl_tasks", []):
            url = self._build_task_url(task_data)
            task_config = TaskConfig.from_config_data(task_data, url)
            configs.append(task_config)

        self._task_configs = configs
        return self._task_configs

    def get_task_config(self, task_id: str) -> TaskConfig:
        """获取任务配置"""
        for config in self.get_all_task_configs():
            if config.id == task_id:
                return config
        raise ValueError(f"任务配置不存在: {task_id}")

    def get_scheduled_configs(self) -> List[TaskConfig]:
        """获取需要调度的任务配置"""
        return [
            config for config in self.get_all_task_configs() if config.is_scheduled()
        ]

    def get_pages_hierarchy(self) -> Dict[str, List[TaskConfig]]:
        """获取页面层级结构"""
        configs = self.get_all_task_configs()
        hierarchy = {"root": [], "children": {}}

        for config in configs:
            if not config.parent_id:
                hierarchy["root"].append(config)
            else:
                if config.parent_id not in hierarchy["children"]:
                    hierarchy["children"][config.parent_id] = []
                hierarchy["children"][config.parent_id].append(config)

        return hierarchy

    def refresh(self):
        """刷新配置"""
        self._config = None
        self._task_configs = []


# 全局实例
_task_manager = None


def get_task_manager() -> TaskManager:
    """获取任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager
