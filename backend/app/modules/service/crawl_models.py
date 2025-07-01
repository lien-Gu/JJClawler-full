"""
统一爬取任务模型

合并配置信息和执行状态到单一模型中
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, Any
from uuid import uuid4

from app.utils.time_utils import to_iso_string


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class CrawlTask:
    """统一的爬取任务模型 - 包含配置和状态"""

    # 配置属性（来自urls.json）
    id: str
    name: str
    url: str
    frequency: str
    interval: int
    parent_id: Optional[str] = None

    # 运行时属性（执行状态）
    status: TaskStatus = TaskStatus.PENDING
    task_id: Optional[str] = None  # 运行时生成的唯一ID
    created_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0
    items_crawled: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    @classmethod
    def from_config(cls, task_data: Dict[str, Any], url: str) -> 'CrawlTask':
        """从配置数据创建任务实例"""
        return cls(
            id=task_data['id'],
            name=task_data['name'],
            url=url,
            frequency=task_data['schedule']['frequency'],
            interval=task_data['schedule']['interval'],
            parent_id=task_data['category'].get('parent', None)
        )

    def create_execution_instance(self, metadata: Dict[str, Any] = None) -> 'CrawlTask':
        """创建执行实例（生成运行时ID和状态）"""
        execution_task = CrawlTask(
            # 复制配置属性
            id=self.id,
            name=self.name,
            url=self.url,
            frequency=self.frequency,
            interval=self.interval,
            parent_id=self.parent_id,

            # 设置运行时属性
            task_id=f"{self.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}",
            status=TaskStatus.PENDING,
            created_at=to_iso_string(datetime.now()),
            metadata=metadata or {}
        )
        return execution_task

    def start(self):
        """开始执行"""
        self.status = TaskStatus.RUNNING
        self.started_at = to_iso_string(datetime.now())

    def complete(self, items_crawled: int = 0, metadata: Dict[str, Any] = None):
        """完成执行"""
        self.status = TaskStatus.COMPLETED
        self.completed_at = to_iso_string(datetime.now())
        self.progress = 100
        self.items_crawled = items_crawled
        if metadata:
            self.metadata.update(metadata)

    def fail(self, error_message: str):
        """标记失败"""
        self.status = TaskStatus.FAILED
        self.completed_at = to_iso_string(datetime.now())
        self.error_message = error_message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于JSON序列化）"""
        data = asdict(self)
        # 将枚举转换为字符串
        if isinstance(data['status'], TaskStatus):
            data['status'] = data['status'].value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrawlTask':
        """从字典创建实例"""
        # 处理枚举字段
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])

        # 为缺失的必需字段提供默认值
        defaults = {
            'id': data.get('id', ''),
            'name': data.get('name', ''),
            'url': data.get('url', ''),
            'frequency': data.get('frequency', 'daily'),
            'interval': data.get('interval', 24),
            'parent_id': data.get('parent_id'),
            'status': data.get('status', TaskStatus.PENDING),
            'task_id': data.get('task_id'),
            'created_at': data.get('created_at'),
            'started_at': data.get('started_at'),
            'completed_at': data.get('completed_at'),
            'progress': data.get('progress', 0),
            'items_crawled': data.get('items_crawled', 0),
            'error_message': data.get('error_message'),
            'metadata': data.get('metadata', {})
        }

        return cls(**defaults)

    def is_scheduled_task(self) -> bool:
        """是否为调度任务"""
        return self.interval > 0

    def get_trigger_config(self) -> Dict[str, Any]:
        """获取调度触发器配置 - 统一使用CronTrigger"""
        if self.frequency == "hourly":
            # hourly任务：每小时的5分执行（避免整点延迟）
            return {
                "minute": 5
            }

        elif self.frequency == "daily":
            # daily任务：每天0点5分执行（避免0点整延迟）
            return {
                "hour": 0,
                "minute": 5
            }
        else:
            raise ValueError(f"不支持的频率: {self.frequency}")
