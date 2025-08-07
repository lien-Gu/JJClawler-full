"""
爬虫基础组件 - 简化版本
"""

import json
from pathlib import Path


class CrawlConfig:
    """爬取配置类"""

    def __init__(self):
        self.urls_file = Path(__file__).parent.parent.parent.joinpath("data/urls.json")
        self._config = None
        self.params = None
        self.templates = None
        self._load_config()

    def _load_config(self):
        """加载URL配置文件"""
        try:
            with open(self.urls_file, encoding="utf-8") as f:
                self._config = json.load(f)
            self.params = self._config.get("global", {}).get("base_params", {})
            self.templates = self._config.get("global", {}).get("templates", {})
        except Exception as e:
            raise Exception(f"配置文件加载失败: {e}")

    def get_task_config(self, task_id: str) -> dict | None:
        """获取特定任务的配置"""
        for task in self._config.get("crawl_tasks", []):
            if task["id"] == task_id:
                return task
        return None

    def get_all_tasks(self) -> list[dict]:
        """获取所有任务配置"""
        return self._config.get("crawl_tasks", [])

    def get_page_ids(self, page_ids: list[str]) -> list[str]:
        """
        根据任务数据确定需要爬取的页面ID列表

        :param page_ids: 任务页面
        :return: 页面ID列表
        """
        res = []
        special_words = {"all": self.get_all_page_ids(), "category": self.get_category_page_ids}  # 特殊字符任务类型
        for page_id in page_ids:
            if page_id in special_words:
                func = special_words.get(page_id, None)
                if not func:
                    raise ValueError(f"page id {page_id} does not exist")
                res.extend(func())
                continue
            if page_id in self.validate_page_id(page_id):
                res.append(page_id)
            else:
                raise ValueError(f"page id {page_id} does not exist")
        return res

    def get_category_page_ids(self) -> list[str]:
        """获取所有分类页面ID列表（排除夹子榜）"""
        all_tasks = self.get_all_tasks()
        category_ids = []

        for task in all_tasks:
            task_id = task.get("id", "")
            if not ("jiazi" in task_id.lower() or task.get("category") == "jiazi"):
                category_ids.append(task_id)

        return category_ids

    def get_all_page_ids(self) -> list[str]:
        """获取所有页面ID"""
        all_tasks = self.get_all_tasks()
        return [task.get("id") for task in all_tasks if task.get("id")]

    def validate_page_id(self, page_id: str) -> bool:
        """验证页面ID是否在配置中"""
        all_tasks = self.get_all_tasks()
        available_ids = {task.get("id", "") for task in all_tasks}
        return page_id in available_ids

    def build_url(self, task_id: str) -> str:
        """
        根据任务id构建URL
        :param task_id:
        :return:
        """
        task_config = self.get_task_config(task_id)
        template_name = task_config["template"]
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")

        # 合并参数
        params = {**self.params, **task_config.get("params", {})}

        # 格式化URL
        return template.format(**params)

    def build_novel_url(self, novel_id: str) -> str:
        """
        根据小说id构建url

        :param novel_id:
        :return:
        """
        template = self.templates.get("novel_detail")
        return template.format(novel_id=novel_id)
