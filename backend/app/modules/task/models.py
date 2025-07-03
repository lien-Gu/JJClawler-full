"""
任务核心模型

整合了任务配置和执行状态管理，提供完整的任务生命周期支持
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from uuid import uuid4

from app.config import get_settings


class TaskStatus(Enum):
    """任务状态"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskConfig:
    """任务配置 - 来自urls.json的静态配置"""

    id: str
    name: str
    url: str
    frequency: str  # hourly, daily
    interval: int  # 小时间隔
    parent_id: Optional[str] = None

    @classmethod
    def from_config_data(cls, data: Dict[str, Any], url: str) -> "TaskConfig":
        """从配置数据创建"""
        return cls(
            id=data["id"],
            name=data["name"],
            url=url,
            frequency=data["schedule"]["frequency"],
            interval=data["schedule"]["interval"],
            parent_id=data["category"].get("parent"),
        )

    def is_scheduled(self) -> bool:
        """是否需要调度"""
        return self.interval > 0

    def get_cron_config(self) -> Dict[str, Any]:
        """获取cron调度配置"""
        if self.frequency == "hourly":
            return {"minute": 5}
        elif self.frequency == "daily":
            return {"hour": 0, "minute": 5}
        else:
            raise ValueError(f"不支持的频率: {self.frequency}")

    def create_execution(self) -> "TaskExecution":
        """创建执行实例"""
        return TaskExecution.create_from_config(self)


@dataclass
class TaskExecution:
    """任务执行实例 - 运行时状态"""

    task_id: str
    config_id: str
    status: TaskStatus = TaskStatus.PENDING
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    items_crawled: int = 0
    error_message: Optional[str] = None

    @classmethod
    def create_from_config(cls, config: TaskConfig) -> "TaskExecution":
        """从配置创建执行实例"""
        task_id = (
            f"{config.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        )
        return cls(task_id=task_id, config_id=config.id, created_at=datetime.now())

    def start(self):
        """开始执行"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

    def complete(self, items_count: int = 0):
        """完成执行"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100
        self.items_crawled = items_count

    def fail(self, error: str):
        """执行失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        settings = get_settings()

        # 转换枚举
        data["status"] = self.status.value

        # 转换时间
        for field in ["created_at", "started_at", "completed_at"]:
            if data.get(field):
                data[field] = data[field].strftime(settings.DATETIME_FORMAT)

        return data


@dataclass
class CrawlTask:
    """统一的爬取任务模型 - 兼容层，整合配置和执行状态"""

    # 配置属性（来自urls.json）
    config: TaskConfig = None

    # 运行时属性（执行状态）
    execution: TaskExecution = None

    @classmethod
    def from_config(cls, task_data: Dict[str, Any], url: str) -> "CrawlTask":
        """从配置数据创建任务实例"""
        config = TaskConfig.from_config_data(task_data, url)
        return cls(config=config, execution=TaskExecution.create_from_config(config))

    def start(self):
        """开始执行"""
        self.execution.status = TaskStatus.RUNNING
        self.execution.started_at = datetime.now()

    def complete(self, items_crawled: int = 0):
        """完成执行"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
        self.progress = 100
        self.items_crawled = items_crawled

    def fail(self, error_message: str):
        """标记失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.now()
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于JSON序列化）"""
        return asdict(self.config) | self.execution.to_dict()
