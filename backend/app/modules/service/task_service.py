"""
任务管理服务 - 简化版本

提供轻量级的任务管理功能：
- 任务状态管理（pending, running, completed, failed）
- 任务历史记录
- 进度跟踪
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from uuid import uuid4

from app.utils.file_utils import read_json_file, write_json_file
from app.utils.time_utils import to_iso_string
from app.utils.log_utils import get_logger
from app.config import get_settings

logger = get_logger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class TaskType(Enum):
    """任务类型枚举"""
    JIAZI = "jiazi"
    PAGE = "page"


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str
    task_type: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    progress: int = 0
    items_crawled: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TaskManager:
    """简化的任务管理器"""
    
    def __init__(self):
        settings = get_settings()
        self.tasks_file = f"{settings.DATA_DIR}/tasks/tasks.json"
        self._ensure_tasks_file()
    
    def _ensure_tasks_file(self):
        """确保任务文件存在"""
        default_data = {
            "current_tasks": [],
            "completed_tasks": [],
            "failed_tasks": [],
            "last_updated": to_iso_string(datetime.now())
        }
        
        try:
            read_json_file(self.tasks_file)
        except:
            write_json_file(self.tasks_file, default_data)
            logger.info("任务文件初始化完成")
    
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
    
    def create_task(self, task_type: TaskType, metadata: Dict[str, Any] = None) -> str:
        """创建新任务"""
        task_id = f"{task_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        
        task = TaskInfo(
            task_id=task_id,
            task_type=task_type.value,
            status=TaskStatus.PENDING.value,
            created_at=to_iso_string(datetime.now()),
            metadata=metadata or {}
        )
        
        data = self._read_tasks()
        data["current_tasks"].append(asdict(task))
        self._write_tasks(data)
        
        logger.info(f"创建任务: {task_id}")
        return task_id
    
    def start_task(self, task_id: str):
        """开始任务"""
        data = self._read_tasks()
        for task in data["current_tasks"]:
            if task["task_id"] == task_id:
                task["status"] = TaskStatus.RUNNING.value
                task["started_at"] = to_iso_string(datetime.now())
                self._write_tasks(data)
                logger.info(f"开始任务: {task_id}")
                return True
        return False
    
    def complete_task(self, task_id: str, items_crawled: int = 0, metadata: Dict[str, Any] = None):
        """完成任务"""
        data = self._read_tasks()
        
        for i, task in enumerate(data["current_tasks"]):
            if task["task_id"] == task_id:
                task["status"] = TaskStatus.COMPLETED.value
                task["completed_at"] = to_iso_string(datetime.now())
                task["progress"] = 100
                task["items_crawled"] = items_crawled
                
                if metadata:
                    task["metadata"].update(metadata)
                
                # 移动到完成列表
                data["completed_tasks"].append(task)
                data["current_tasks"].pop(i)
                self._write_tasks(data)
                
                logger.info(f"完成任务: {task_id} (抓取 {items_crawled} 条)")
                return True
        return False
    
    def fail_task(self, task_id: str, error_message: str):
        """标记任务失败"""
        data = self._read_tasks()
        
        for i, task in enumerate(data["current_tasks"]):
            if task["task_id"] == task_id:
                task["status"] = TaskStatus.FAILED.value
                task["completed_at"] = to_iso_string(datetime.now())
                task["error_message"] = error_message
                
                # 移动到失败列表
                data["failed_tasks"].append(task)
                data["current_tasks"].pop(i)
                self._write_tasks(data)
                
                logger.warning(f"任务失败: {task_id} - {error_message}")
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务信息"""
        data = self._read_tasks()
        all_tasks = data.get("current_tasks", []) + data.get("completed_tasks", []) + data.get("failed_tasks", [])
        
        for task_data in all_tasks:
            if task_data.get("task_id") == task_id:
                # 过滤掉不需要的字段
                filtered_data = {
                    "task_id": task_data.get("task_id", ""),
                    "task_type": task_data.get("task_type", ""),
                    "status": task_data.get("status", ""),
                    "created_at": task_data.get("created_at", ""),
                    "started_at": task_data.get("started_at"),
                    "completed_at": task_data.get("completed_at"),
                    "progress": task_data.get("progress", 0),
                    "items_crawled": task_data.get("items_crawled", 0),
                    "error_message": task_data.get("error_message"),
                    "metadata": task_data.get("metadata", {})
                }
                return TaskInfo(**filtered_data)
        return None
    
    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务状态（别名方法）"""
        return self.get_task(task_id)
    
    def get_current_tasks(self) -> List[TaskInfo]:
        """获取当前任务"""
        data = self._read_tasks()
        return [TaskInfo(**task) for task in data["current_tasks"]]
    
    def get_all_tasks(self) -> Dict[str, List[TaskInfo]]:
        """获取所有任务"""
        data = self._read_tasks()
        
        def create_task_info(task_data):
            # 过滤掉不需要的字段，只保留TaskInfo需要的字段
            filtered_data = {
                "task_id": task_data.get("task_id", ""),
                "task_type": task_data.get("task_type", ""),
                "status": task_data.get("status", ""),
                "created_at": task_data.get("created_at", ""),
                "started_at": task_data.get("started_at"),
                "completed_at": task_data.get("completed_at"),
                "progress": task_data.get("progress", 0),
                "items_crawled": task_data.get("items_crawled", 0),
                "error_message": task_data.get("error_message"),
                "metadata": task_data.get("metadata", {})
            }
            return TaskInfo(**filtered_data)
        
        return {
            "current": [create_task_info(task) for task in data.get("current_tasks", [])],
            "completed": [create_task_info(task) for task in data.get("completed_tasks", [])],
            "failed": [create_task_info(task) for task in data.get("failed_tasks", [])]
        }
    
    def get_task_summary(self) -> Dict[str, Any]:
        """获取任务摘要"""
        data = self._read_tasks()
        return {
            "current_count": len(data["current_tasks"]),
            "completed_count": len(data["completed_tasks"]),
            "failed_count": len(data["failed_tasks"]),
            "current_tasks": [
                {
                    "task_id": task["task_id"],
                    "task_type": task["task_type"],
                    "status": task["status"],
                    "progress": task["progress"],
                    "created_at": task["created_at"]
                }
                for task in data["current_tasks"]
            ]
        }


# 全局实例
_task_manager = None

def get_task_manager() -> TaskManager:
    """获取任务管理器实例"""
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


# 便捷函数
def create_jiazi_task() -> str:
    """创建夹子榜任务"""
    return get_task_manager().create_task(TaskType.JIAZI)


def create_page_task(channel: str) -> str:
    """创建页面爬取任务"""
    return get_task_manager().create_task(TaskType.PAGE, {"channel": channel})


async def execute_with_task(task_id: str, executor: Callable, *args, **kwargs) -> bool:
    """执行带任务跟踪的函数"""
    task_manager = get_task_manager()
    
    try:
        task_manager.start_task(task_id)
        
        # 执行任务
        result = await executor(*args, **kwargs)
        
        # 处理结果
        if isinstance(result, dict):
            items_count = result.get('books_new', 0) + result.get('books_updated', 0)
            task_manager.complete_task(task_id, items_count, result)
        else:
            task_manager.complete_task(task_id)
        
        return True
        
    except Exception as e:
        task_manager.fail_task(task_id, str(e))
        logger.error(f"任务执行失败: {task_id} - {e}")
        return False

