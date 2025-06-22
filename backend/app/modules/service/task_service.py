"""
任务管理模块 - JSON文件存储的任务状态管理

提供轻量级的任务管理功能，使用JSON文件存储：
- 任务状态管理（pending, running, completed, failed）
- 任务历史记录
- 进度跟踪
- 错误处理和重试机制

设计原则：
1. 简单性：使用JSON文件而非数据库，降低复杂度
2. 线程安全：文件操作加锁，支持并发
3. 持久化：任务状态持久保存，应用重启后可恢复
4. 可扩展：为未来集成APScheduler预留接口
"""

import asyncio
import os
import threading
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from uuid import uuid4

from app.utils.file_utils import read_json_file, write_json_file, ensure_directory
from app.utils.time_utils import to_iso_string, parse_iso_datetime
from app.utils.log_utils import get_logger
from app.config import get_settings

# 配置日志
logger = get_logger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"       # 执行失败


class TaskType(Enum):
    """任务类型枚举"""
    JIAZI = "jiazi"          # 夹子榜抓取
    PAGE = "page"            # 分类页面抓取
    BOOK_DETAIL = "book_detail"  # 书籍详情抓取


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
    total_items: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class TaskFileManager:
    """
    任务文件管理器
    
    负责任务数据的文件存储和读取：
    - JSON文件的安全读写
    - 文件锁机制
    - 数据备份和恢复
    - 历史记录归档
    """
    
    def __init__(self, base_dir: str = None):
        """
        初始化任务文件管理器
        
        Args:
            base_dir: 任务文件存储目录
        """
        # 如果没有指定路径，从settings读取
        if base_dir is None:
            settings = get_settings()
            base_dir = f"{settings.DATA_DIR}/tasks"
            
        self.base_dir = Path(base_dir)
        self.tasks_file = self.base_dir / "tasks.json"
        self.history_dir = self.base_dir / "history"
        self.lock = threading.RLock()  # 可重入锁
        
        # 确保目录存在
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化任务文件
        self._init_tasks_file()
    
    def _init_tasks_file(self):
        """初始化任务文件"""
        if not self.tasks_file.exists():
            initial_data = {
                "current_tasks": [],
                "completed_tasks": [],
                "failed_tasks": [],
                "last_updated": datetime.now().isoformat()
            }
            self._write_tasks_file(initial_data)
            logger.info("任务文件初始化完成")
    
    def _read_tasks_file(self) -> Dict[str, Any]:
        """安全读取任务文件"""
        with self.lock:
            default_data = {"current_tasks": [], "completed_tasks": [], "failed_tasks": []}
            data = read_json_file(self.tasks_file, default=default_data)
            
            # 确保所有必需的字段都存在
            if "failed_tasks" not in data:
                data["failed_tasks"] = []
            
            return data
    
    def _write_tasks_file(self, data: Dict[str, Any]):
        """安全写入任务文件"""
        with self.lock:
            # 添加时间戳
            data["last_updated"] = to_iso_string(datetime.now())
            
            # 使用utils中的写入函数，自动处理备份
            success = write_json_file(self.tasks_file, data, backup=True)
            if not success:
                raise IOError("任务文件写入失败")
    
    def add_task(self, task: TaskInfo) -> bool:
        """
        添加新任务
        
        Args:
            task: 任务信息
            
        Returns:
            添加是否成功
        """
        try:
            data = self._read_tasks_file()
            data["current_tasks"].append(asdict(task))
            self._write_tasks_file(data)
            logger.info(f"任务已添加: {task.task_id}")
            return True
        except Exception as e:
            logger.error(f"添加任务失败: {e}")
            return False
    
    def update_task(self, task_id: str, updates: Dict[str, Any]) -> bool:
        """
        更新任务状态
        
        Args:
            task_id: 任务ID
            updates: 更新的字段
            
        Returns:
            更新是否成功
        """
        try:
            data = self._read_tasks_file()
            
            # 在当前任务中查找
            for task in data["current_tasks"]:
                if task["task_id"] == task_id:
                    task.update(updates)
                    self._write_tasks_file(data)
                    logger.debug(f"任务已更新: {task_id}")
                    return True
            
            logger.warning(f"未找到任务: {task_id}")
            return False
            
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            return False
    
    def complete_task(self, task_id: str, items_crawled: int = 0, metadata: Dict[str, Any] = None) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            items_crawled: 抓取的条目数
            metadata: 额外的元数据
            
        Returns:
            操作是否成功
        """
        try:
            data = self._read_tasks_file()
            
            # 在当前任务中查找并移动到完成列表
            for i, task in enumerate(data["current_tasks"]):
                if task["task_id"] == task_id:
                    # 更新任务状态
                    task["status"] = TaskStatus.COMPLETED.value
                    task["completed_at"] = datetime.now().isoformat()
                    task["progress"] = 100
                    task["items_crawled"] = items_crawled
                    
                    if metadata:
                        task["metadata"].update(metadata)
                    
                    # 移动到完成列表
                    data["completed_tasks"].append(task)
                    data["current_tasks"].pop(i)
                    
                    self._write_tasks_file(data)
                    logger.info(f"任务已完成: {task_id} (抓取 {items_crawled} 条)")
                    return True
            
            logger.warning(f"未找到任务: {task_id}")
            return False
            
        except Exception as e:
            logger.error(f"完成任务失败: {e}")
            return False
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            
        Returns:
            操作是否成功
        """
        try:
            data = self._read_tasks_file()
            
            # 在当前任务中查找并移动到失败列表
            for i, task in enumerate(data["current_tasks"]):
                if task["task_id"] == task_id:
                    # 更新任务状态
                    task["status"] = TaskStatus.FAILED.value
                    task["completed_at"] = datetime.now().isoformat()
                    task["error_message"] = error_message
                    
                    # 移动到失败列表
                    data["failed_tasks"].append(task)
                    data["current_tasks"].pop(i)
                    
                    self._write_tasks_file(data)
                    logger.warning(f"任务已失败: {task_id} - {error_message}")
                    return True
            
            logger.warning(f"未找到任务: {task_id}")
            return False
            
        except Exception as e:
            logger.error(f"标记任务失败操作失败: {e}")
            return False
    
    def get_task(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取指定任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息或None
        """
        try:
            data = self._read_tasks_file()
            
            # 在所有任务列表中查找
            all_tasks = (data["current_tasks"] + 
                        data["completed_tasks"] + 
                        data["failed_tasks"])
            
            for task_data in all_tasks:
                if task_data["task_id"] == task_id:
                    return TaskInfo(**task_data)
            
            return None
            
        except Exception as e:
            logger.error(f"获取任务失败: {e}")
            return None
    
    def get_all_tasks(self) -> Dict[str, List[TaskInfo]]:
        """
        获取所有任务
        
        Returns:
            按状态分组的任务字典
        """
        try:
            data = self._read_tasks_file()
            
            return {
                "current": [TaskInfo(**task) for task in data["current_tasks"]],
                "completed": [TaskInfo(**task) for task in data["completed_tasks"]],
                "failed": [TaskInfo(**task) for task in data["failed_tasks"]]
            }
            
        except Exception as e:
            logger.error(f"获取所有任务失败: {e}")
            return {"current": [], "completed": [], "failed": []}
    
    def cleanup_old_tasks(self, days: int = 7):
        """
        清理旧任务记录
        
        Args:
            days: 保留天数
        """
        try:
            data = self._read_tasks_file()
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # 过滤旧的完成任务
            data["completed_tasks"] = [
                task for task in data["completed_tasks"]
                if datetime.fromisoformat(task.get("completed_at", "")) > cutoff_date
            ]
            
            # 过滤旧的失败任务
            data["failed_tasks"] = [
                task for task in data["failed_tasks"]
                if datetime.fromisoformat(task.get("completed_at", "")) > cutoff_date
            ]
            
            self._write_tasks_file(data)
            logger.info(f"清理了 {days} 天前的旧任务记录")
            
        except Exception as e:
            logger.error(f"清理旧任务失败: {e}")


class TaskManager:
    """
    任务管理器主类
    
    提供任务管理的高级接口：
    - 任务创建和执行
    - 进度跟踪
    - 错误处理
    - 统计信息
    """
    
    def __init__(self, base_dir: str = None):
        """
        初始化任务管理器
        
        Args:
            base_dir: 任务文件存储目录
        """
        self.file_manager = TaskFileManager(base_dir)
        self._running_tasks: Dict[str, asyncio.Task] = {}
    
    def create_task(self, 
                   task_type: TaskType, 
                   metadata: Dict[str, Any] = None) -> str:
        """
        创建新任务
        
        Args:
            task_type: 任务类型
            metadata: 任务元数据
            
        Returns:
            任务ID
        """
        task_id = f"{task_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        
        task = TaskInfo(
            task_id=task_id,
            task_type=task_type.value,
            status=TaskStatus.PENDING.value,
            created_at=datetime.now().isoformat(),
            metadata=metadata or {}
        )
        
        if self.file_manager.add_task(task):
            logger.info(f"创建任务成功: {task_id} ({task_type.value})")
            return task_id
        else:
            raise RuntimeError(f"创建任务失败: {task_type.value}")
    
    async def execute_task(self, 
                          task_id: str, 
                          executor: Callable, 
                          *args, **kwargs) -> bool:
        """
        执行任务
        
        Args:
            task_id: 任务ID
            executor: 执行函数
            *args, **kwargs: 执行函数的参数
            
        Returns:
            执行是否成功
        """
        try:
            # 更新任务状态为运行中
            self.file_manager.update_task(task_id, {
                "status": TaskStatus.RUNNING.value,
                "started_at": datetime.now().isoformat()
            })
            
            # 执行任务
            logger.info(f"开始执行任务: {task_id}")
            result = await executor(*args, **kwargs)
            
            # 处理执行结果
            if isinstance(result, tuple) and len(result) >= 2:
                # 假设返回 (books, snapshots)
                items_count = len(result[0]) if result[0] else 0
                self.file_manager.complete_task(task_id, items_count)
            else:
                self.file_manager.complete_task(task_id)
            
            logger.info(f"任务执行成功: {task_id}")
            return True
            
        except Exception as e:
            error_msg = str(e)
            self.file_manager.fail_task(task_id, error_msg)
            logger.error(f"任务执行失败: {task_id} - {error_msg}")
            return False
    
    def update_progress(self, task_id: str, progress: int, items_crawled: int = 0):
        """
        更新任务进度
        
        Args:
            task_id: 任务ID
            progress: 进度百分比 (0-100)
            items_crawled: 已抓取条目数
        """
        self.file_manager.update_task(task_id, {
            "progress": min(100, max(0, progress)),
            "items_crawled": items_crawled
        })
    
    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务信息
        """
        return self.file_manager.get_task(task_id)
    
    def get_task_summary(self) -> Dict[str, Any]:
        """
        获取任务摘要统计
        
        Returns:
            任务统计信息
        """
        all_tasks = self.file_manager.get_all_tasks()
        
        return {
            "current_count": len(all_tasks["current"]),
            "completed_count": len(all_tasks["completed"]),
            "failed_count": len(all_tasks["failed"]),
            "current_tasks": [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "status": task.status,
                    "progress": task.progress,
                    "created_at": task.created_at
                }
                for task in all_tasks["current"]
            ]
        }
    
    def get_recent_tasks(self, limit: int = 10) -> List[TaskInfo]:
        """
        获取最近的任务
        
        Args:
            limit: 返回数量限制
            
        Returns:
            最近任务列表
        """
        all_tasks = self.file_manager.get_all_tasks()
        
        # 合并所有任务并按创建时间排序
        all_tasks_list = (all_tasks["current"] + 
                         all_tasks["completed"] + 
                         all_tasks["failed"])
        
        # 按创建时间倒序排序
        all_tasks_list.sort(
            key=lambda x: x.created_at, 
            reverse=True
        )
        
        return all_tasks_list[:limit]
    
    def cleanup_old_tasks(self, days: int = 7):
        """
        清理旧任务
        
        Args:
            days: 保留天数
        """
        self.file_manager.cleanup_old_tasks(days)
    
    def complete_task(self, task_id: str, items_crawled: int = 0, metadata: Dict[str, Any] = None) -> bool:
        """
        完成任务
        
        Args:
            task_id: 任务ID
            items_crawled: 抓取的条目数
            metadata: 额外的元数据
            
        Returns:
            操作是否成功
        """
        return self.file_manager.complete_task(task_id, items_crawled, metadata)
    
    def fail_task(self, task_id: str, error_message: str) -> bool:
        """
        标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
            
        Returns:
            操作是否成功
        """
        return self.file_manager.fail_task(task_id, error_message)


# 全局任务管理器实例
_task_manager: Optional[TaskManager] = None


def get_task_manager() -> TaskManager:
    """
    获取全局任务管理器实例
    
    Returns:
        TaskManager: 任务管理器实例
    """
    global _task_manager
    if _task_manager is None:
        _task_manager = TaskManager()
    return _task_manager


# 便捷函数
def create_jiazi_task() -> str:
    """
    创建夹子榜抓取任务
    
    Returns:
        任务ID
    """
    return get_task_manager().create_task(TaskType.JIAZI)


def create_page_task(channel: str) -> str:
    """
    创建分类页面抓取任务
    
    Args:
        channel: 频道标识
        
    Returns:
        任务ID
    """
    return get_task_manager().create_task(
        TaskType.PAGE, 
        metadata={"channel": channel}
    )


async def execute_jiazi_task(task_id: str) -> bool:
    """
    执行夹子榜抓取任务
    
    Args:
        task_id: 任务ID
        
    Returns:
        执行是否成功
    """
    from app.modules.crawler_service import crawl_jiazi
    return await get_task_manager().execute_task(task_id, crawl_jiazi)


async def execute_page_task(task_id: str, channel: str) -> bool:
    """
    执行分类页面抓取任务
    
    Args:
        task_id: 任务ID
        channel: 频道标识
        
    Returns:
        执行是否成功
    """
    from app.modules.crawler_service import crawl_page
    return await get_task_manager().execute_task(task_id, crawl_page, channel)