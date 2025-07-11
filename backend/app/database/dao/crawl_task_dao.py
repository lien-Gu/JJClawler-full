"""
爬虫任务数据访问对象
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, update, delete, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from .base_dao import BaseDAO
from ..db.crawl_task import CrawlTask
from ...models.crawl import TaskStatus


class CrawlTaskDAO(BaseDAO[CrawlTask]):
    """爬虫任务数据访问对象"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(CrawlTask, session)
    
    async def create_task(self, task_id: str, status: str, message: str, 
                         page_ids: Optional[List[str]] = None,
                         task_type: str = "unknown") -> CrawlTask:
        """创建爬虫任务"""
        task = CrawlTask(
            task_id=task_id,
            status=status,
            message=message,
            page_ids=page_ids,
            task_type=task_type,
            started_at=datetime.now()
        )
        await self.create(task)
        return task
    
    async def get_by_task_id(self, task_id: str) -> Optional[CrawlTask]:
        """根据任务ID获取任务"""
        stmt = select(CrawlTask).where(CrawlTask.task_id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_tasks_by_status(self, status: TaskStatus, 
                                 limit: int = 50, offset: int = 0) -> List[CrawlTask]:
        """根据状态获取任务列表"""
        stmt = (
            select(CrawlTask)
            .where(CrawlTask.status == status.value)
            .order_by(desc(CrawlTask.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_recent_tasks(self, limit: int = 50, offset: int = 0) -> List[CrawlTask]:
        """获取最近的任务列表"""
        stmt = (
            select(CrawlTask)
            .order_by(desc(CrawlTask.created_at))
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def update_task_status(self, task_id: str, status: str, 
                               message: str = "", completed_at: Optional[datetime] = None,
                               duration: Optional[float] = None,
                               progress: int = 0, completed_pages: int = 0,
                               result_data: Optional[dict] = None,
                               error_message: Optional[str] = None) -> bool:
        """更新任务状态"""
        update_data = {
            "status": status,
            "message": message,
            "progress": progress,
            "completed_pages": completed_pages,
            "updated_at": datetime.now()
        }
        
        if completed_at:
            update_data["completed_at"] = completed_at
        if duration is not None:
            update_data["duration"] = duration
        if result_data is not None:
            update_data["result_data"] = result_data
        if error_message is not None:
            update_data["error_message"] = error_message
        
        stmt = (
            update(CrawlTask)
            .where(CrawlTask.task_id == task_id)
            .values(**update_data)
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
    
    async def delete_old_tasks(self, days: int = 30) -> int:
        """删除指定天数之前的任务"""
        cutoff_date = datetime.now() - timedelta(days=days)
        stmt = delete(CrawlTask).where(CrawlTask.created_at < cutoff_date)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount
    
    async def get_task_statistics(self) -> dict:
        """获取任务统计信息"""
        # 获取各状态的任务数量
        from sqlalchemy import func
        
        stmt = (
            select(
                CrawlTask.status,
                func.count(CrawlTask.id).label('count')
            )
            .group_by(CrawlTask.status)
        )
        
        result = await self.session.execute(stmt)
        status_counts = {row.status: row.count for row in result}
        
        # 获取总任务数
        total_stmt = select(func.count(CrawlTask.id))
        total_result = await self.session.execute(total_stmt)
        total_count = total_result.scalar()
        
        return {
            "total_tasks": total_count,
            "status_distribution": status_counts,
            "pending_tasks": status_counts.get(TaskStatus.PENDING.value, 0),
            "running_tasks": status_counts.get(TaskStatus.RUNNING.value, 0),
            "completed_tasks": status_counts.get(TaskStatus.COMPLETED.value, 0),
            "failed_tasks": status_counts.get(TaskStatus.FAILED.value, 0)
        }