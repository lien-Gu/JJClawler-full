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
    interval: int   # 小时间隔
    parent_id: Optional[str] = None
    
    @classmethod
    def from_config_data(cls, data: Dict[str, Any], url: str) -> 'TaskConfig':
        """从配置数据创建"""
        return cls(
            id=data['id'],
            name=data['name'],
            url=url,
            frequency=data['schedule']['frequency'],
            interval=data['schedule']['interval'],
            parent_id=data['category'].get('parent')
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
    
    def create_execution(self) -> 'TaskExecution':
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
    def create_from_config(cls, config: TaskConfig) -> 'TaskExecution':
        """从配置创建执行实例"""
        task_id = f"{config.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        return cls(
            task_id=task_id,
            config_id=config.id,
            created_at=datetime.now()
        )
    
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
        data['status'] = self.status.value
        
        # 转换时间
        for field in ['created_at', 'started_at', 'completed_at']:
            if data.get(field):
                data[field] = data[field].strftime(settings.DATETIME_FORMAT)
                
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskExecution':
        """从字典创建实例"""
        settings = get_settings()
        
        # 处理枚举字段
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])

        # 处理时间字段
        def parse_datetime(time_str: Optional[str]) -> Optional[datetime]:
            if not time_str:
                return None
            if isinstance(time_str, datetime):
                return time_str
            try:
                return datetime.strptime(time_str, settings.DATETIME_FORMAT)
            except ValueError:
                # 尝试ISO格式作为备选
                return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

        # 为缺失的必需字段提供默认值
        defaults = {
            'task_id': data.get('task_id', ''),
            'config_id': data.get('config_id', ''),
            'status': data.get('status', TaskStatus.PENDING),
            'created_at': parse_datetime(data.get('created_at')),
            'started_at': parse_datetime(data.get('started_at')),
            'completed_at': parse_datetime(data.get('completed_at')),
            'progress': data.get('progress', 0),
            'items_crawled': data.get('items_crawled', 0),
            'error_message': data.get('error_message')
        }

        return cls(**defaults)


@dataclass
class CrawlTask:
    """统一的爬取任务模型 - 兼容层，整合配置和执行状态"""
    
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
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: int = 0
    items_crawled: int = 0
    error_message: Optional[str] = None

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

    @classmethod
    def from_config_and_execution(cls, config: TaskConfig, execution: TaskExecution) -> 'CrawlTask':
        """从配置和执行状态创建统一任务"""
        return cls(
            id=config.id,
            name=config.name,
            url=config.url,
            frequency=config.frequency,
            interval=config.interval,
            parent_id=config.parent_id,
            
            status=execution.status,
            task_id=execution.task_id,
            created_at=execution.created_at,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            progress=execution.progress,
            items_crawled=execution.items_crawled,
            error_message=execution.error_message
        )

    def create_execution_instance(self) -> 'CrawlTask':
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
            created_at=datetime.now(),
        )
        return execution_task

    def start(self):
        """开始执行"""
        self.status = TaskStatus.RUNNING
        self.started_at = datetime.now()

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
        data = asdict(self)
        settings = get_settings()
        
        # 将枚举转换为字符串
        if isinstance(data['status'], TaskStatus):
            data['status'] = data['status'].value
            
        # 将datetime转换为字符串
        for field in ['created_at', 'started_at', 'completed_at']:
            if data.get(field) and isinstance(data[field], datetime):
                data[field] = data[field].strftime(settings.DATETIME_FORMAT)
                
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CrawlTask':
        """从字典创建实例"""
        settings = get_settings()
        
        # 处理枚举字段
        if isinstance(data.get('status'), str):
            data['status'] = TaskStatus(data['status'])

        # 处理时间字段
        def parse_datetime(time_str: Optional[str]) -> Optional[datetime]:
            if not time_str:
                return None
            if isinstance(time_str, datetime):
                return time_str
            try:
                return datetime.strptime(time_str, settings.DATETIME_FORMAT)
            except ValueError:
                # 尝试ISO格式作为备选
                return datetime.fromisoformat(time_str.replace('Z', '+00:00'))

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
            'created_at': parse_datetime(data.get('created_at')),
            'started_at': parse_datetime(data.get('started_at')),
            'completed_at': parse_datetime(data.get('completed_at')),
            'progress': data.get('progress', 0),
            'items_crawled': data.get('items_crawled', 0),
            'error_message': data.get('error_message')
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