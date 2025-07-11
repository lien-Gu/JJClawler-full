"""
爬虫任务服务类
"""
import asyncio
from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..dao.crawl_task_dao import CrawlTaskDAO
from ..db.crawl_task import CrawlTask
from ...models.crawl import TaskStatus, CrawlTaskResponse


class CrawlTaskService:
    """爬虫任务服务"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dao = CrawlTaskDAO(session)
    
    async def create_task(self, task_id: str, task_type: str, 
                         page_ids: Optional[List[str]] = None,
                         message: str = "") -> CrawlTaskResponse:
        """创建爬虫任务"""
        task = await self.dao.create_task(
            task_id=task_id,
            status=TaskStatus.PENDING.value,
            message=message,
            page_ids=page_ids,
            task_type=task_type
        )
        
        return self._task_to_response(task)
    
    async def get_task_by_id(self, task_id: str) -> Optional[CrawlTaskResponse]:
        """根据任务ID获取任务"""
        task = await self.dao.get_by_task_id(task_id)
        if task:
            return self._task_to_response(task)
        return None
    
    async def get_tasks(self, status: Optional[TaskStatus] = None, 
                       limit: int = 50, offset: int = 0) -> List[CrawlTaskResponse]:
        """获取任务列表"""
        if status:
            tasks = await self.dao.get_tasks_by_status(status, limit, offset)
        else:
            tasks = await self.dao.get_recent_tasks(limit, offset)
        
        return [self._task_to_response(task) for task in tasks]
    
    async def update_task_status(self, task_id: str, status: TaskStatus,
                               message: str = "", progress: int = 0,
                               completed_pages: int = 0,
                               result_data: Optional[dict] = None,
                               error_message: Optional[str] = None) -> bool:
        """更新任务状态"""
        completed_at = None
        duration = None
        
        if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            completed_at = datetime.now()
            # 计算执行时长
            task = await self.dao.get_by_task_id(task_id)
            if task and task.started_at:
                duration = (completed_at - task.started_at).total_seconds()
        
        return await self.dao.update_task_status(
            task_id=task_id,
            status=status.value,
            message=message,
            completed_at=completed_at,
            duration=duration,
            progress=progress,
            completed_pages=completed_pages,
            result_data=result_data,
            error_message=error_message
        )
    
    async def start_task_execution(self, task_id: str, 
                                  execution_func, *args, **kwargs):
        """启动异步任务执行"""
        # 更新任务状态为运行中
        await self.update_task_status(task_id, TaskStatus.RUNNING, "任务开始执行")
        
        # 创建异步任务
        asyncio.create_task(
            self._execute_task_with_error_handling(
                task_id, execution_func, *args, **kwargs
            )
        )
    
    async def _execute_task_with_error_handling(self, task_id: str,
                                              execution_func, *args, **kwargs):
        """带错误处理的任务执行"""
        try:
            # 执行任务
            result = await execution_func(*args, **kwargs)
            
            # 更新为成功状态
            await self.update_task_status(
                task_id, TaskStatus.COMPLETED,
                "任务执行成功", progress=100,
                result_data=result if isinstance(result, dict) else {"result": str(result)}
            )
            
        except Exception as e:
            # 更新为失败状态
            await self.update_task_status(
                task_id, TaskStatus.FAILED,
                f"任务执行失败: {str(e)}",
                error_message=str(e)
            )
    
    async def get_task_statistics(self) -> dict:
        """获取任务统计信息"""
        return await self.dao.get_task_statistics()
    
    async def cleanup_old_tasks(self, days: int = 30) -> int:
        """清理老旧任务"""
        return await self.dao.delete_old_tasks(days)
    
    def _task_to_response(self, task: CrawlTask) -> CrawlTaskResponse:
        """将数据库模型转换为响应模型"""
        return CrawlTaskResponse(
            task_id=task.task_id,
            status=TaskStatus(task.status),
            message=task.message,
            page_ids=task.page_ids,
            started_at=task.started_at,
            completed_at=task.completed_at,
            duration=task.duration
        )