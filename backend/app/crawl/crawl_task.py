"""
爬虫基础组件 - 简化版本
"""

import json
from pathlib import Path
from typing import List, Dict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PageTask:
    id: str
    name: str
    type: str
    url: str

    def __eq__(self, other):
        if not isinstance(other, PageTask):
            return NotImplemented
        return self.url == other.url

    def __hash__(self):
        return hash(self.url)


class CrawlTask:
    """爬取配置类"""

    def __init__(self):
        self.urls_file = Path(__file__).parent.parent.parent.joinpath("data/urls.json")
        self.params = None
        self.templates = None
        self.tasks: Dict[str, PageTask] = dict()
        self._load_config()

    def _load_config(self):
        """加载URL配置文件"""
        try:
            with open(self.urls_file, encoding="utf-8") as f:
                config = json.load(f)
            self.params = config.get("global", {}).get("base_params", {})
            self.templates = config.get("global", {}).get("templates", {})
            tasks_dict = config.get("crawl_tasks", [])
            self.tasks = self.build_tasks(tasks_dict)
        except Exception as e:
            raise Exception(f"配置文件加载失败: {e}")

    def build_tasks(self, tasks_dict) -> Dict[str, PageTask]:
        """
        构造爬虫任务信息
        :param tasks_dict:原始字典信息
        :return:
        """
        res_dict = {}
        for t in tasks_dict:
            task_id = t.get("id")
            url = self.build_page_url(t)
            task = PageTask(
                id=task_id,
                name=t.get("name"),
                type=t.get("type"),
                url=url)
            res_dict[task_id] = task
        return res_dict

    def get_task(self, task_id: str) -> PageTask:
        """获取特定任务的配置"""
        return self.tasks.get(task_id, None)

    def get_all_tasks(self) -> list[PageTask]:
        """获取所有任务配置"""
        return list(self.tasks.values())

    def get_page_tasks(self) -> list[PageTask]:
        """获取所有分类页面ID列表（排除夹子榜）"""
        return [t for t in self.tasks.values() if t.type == "page"]

    def get_tasks_by_words(self, page_ids: list[str]) -> list[PageTask]:
        """
        根据任务数据确定需要爬取的页面ID列表

        :param page_ids: 任务页面
        :return: 页面ID列表
        """
        # 兼容性处理：支持单页面字符串输入
        if isinstance(page_ids, str):
            page_ids = [page_ids]

        res = set()
        special_words = {"all": self.get_all_tasks, "page": self.get_page_tasks}  # 特殊字符任务类型
        for page_id in page_ids:
            if page_id in special_words:
                func = special_words.get(page_id, None)
                if not func:
                    raise ValueError(f"page id {page_id} does not exist")
                res.update(func())
            else:
                task = self.get_task(page_id)
                if task is None:
                    raise KeyError(f"page id {page_id} does not exist")
                res.add(task)
        return list(res)

    def build_page_url(self, task_config: dict) -> str:
        """
        根据任务信息和通用信息构建URL
        :param task_config:
        :return:
        """
        template_name = task_config["template"]
        template = self.templates.get(template_name)
        if not template:
            raise ValueError(f"模板不存在: {template_name}")
        # 合并参数
        params = {**self.params, **task_config.get("params", {})}

        # 格式化URL
        return template.format(**params)

    def build_novel_url(self, novel_id: str or int) -> str:
        """
        根据小说id构建url

        :param novel_id:
        :return:
        """
        if isinstance(novel_id, int):
            novel_id = str(novel_id)
        template = self.templates.get("novel_detail")
        return template.format(novel_id=novel_id)


_crawl_task: CrawlTask | None = None


def get_crawl_task() -> CrawlTask:
    """
    获取爬虫任务配置信息
    :return:
    """
    global _crawl_task
    if _crawl_task is None:
        _crawl_task = CrawlTask()
    return _crawl_task


if __name__ == '__main__':
    crawl_task = get_crawl_task()
    a = crawl_task.get_tasks_by_words(["index"])
    print(a)
