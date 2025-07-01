"""
任务监控和纠错服务

负责监控爬取任务的执行情况，检测缺失数据并进行自动纠错：
- 检查预期任务是否按时执行
- 发现缺失数据时自动重试
- 最多3次重试，失败后记录警告
- 30分钟间隔检查机制
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

from app.modules.service.crawl_service import get_crawl_service
from app.modules.database.connection import get_session_sync
from app.modules.models import Ranking, BookSnapshot, RankingSnapshot

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    JIAZI = "jiazi"
    PAGE = "page"


@dataclass
class MissingTaskInfo:
    """缺失任务信息"""
    task_type: TaskType
    channel: str
    expected_time: datetime
    retry_count: int = 0
    max_retries: int = 3
    last_retry_time: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)


class TaskMonitorService:
    """
    任务监控服务
    
    功能：
    1. 定期检查预期任务是否执行
    2. 发现缺失数据时触发重试
    3. 记录重试历史和失败原因
    4. 生成警告日志
    """
    
    def __init__(self):
        self.monitor_interval = 30 * 60  # 30分钟检查间隔
        self.missing_tasks: Dict[str, MissingTaskInfo] = {}
        self.is_running = False
        self.monitor_task: Optional[asyncio.Task] = None
    
    async def start_monitoring(self):
        """启动任务监控"""
        if self.is_running:
            logger.warning("任务监控已在运行中")
            return
        
        self.is_running = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("任务监控服务已启动，检查间隔: 30分钟")
    
    async def stop_monitoring(self):
        """停止任务监控"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("任务监控服务已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        logger.info("开始执行任务监控循环")
        
        while self.is_running:
            try:
                await self._check_missing_tasks()
                await asyncio.sleep(self.monitor_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"任务监控循环出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
    
    async def _check_missing_tasks(self):
        """检查缺失的任务"""
        logger.info("开始检查缺失任务...")
        current_time = datetime.now()
        
        # 检查夹子榜任务（每小时）
        await self._check_jiazi_tasks(current_time)
        
        # 检查页面任务（根据配置的频率）
        await self._check_page_tasks(current_time)
        
        # 处理需要重试的任务
        await self._process_retry_tasks(current_time)
        
        logger.info(f"任务检查完成，发现 {len(self.missing_tasks)} 个缺失任务")
    
    async def _check_jiazi_tasks(self, current_time: datetime):
        """检查夹子榜任务"""
        # 夹子榜每小时执行一次，检查最近2小时是否有数据
        check_hours = [current_time.hour - 1, current_time.hour - 2]
        
        for hour in check_hours:
            if hour < 0:
                continue
            
            expected_time = current_time.replace(hour=hour, minute=0, second=0, microsecond=0)
            task_key = f"jiazi_{expected_time.strftime('%Y%m%d_%H')}"
            
            # 检查是否有该时间的数据
            has_data = await self._check_jiazi_data_exists(expected_time)
            
            if not has_data and task_key not in self.missing_tasks:
                logger.warning(f"发现缺失的夹子榜任务: {expected_time}")
                self.missing_tasks[task_key] = MissingTaskInfo(
                    task_type=TaskType.JIAZI,
                    channel="jiazi",
                    expected_time=expected_time
                )
    
    async def _check_page_tasks(self, current_time: datetime):
        """检查页面任务"""
        # 从数据库获取所有榜单配置
        rankings = await self._get_rankings()
        
        for ranking in rankings:
            if ranking.ranking_id == 'jiazi':  # 夹子榜单独处理
                continue
            
            # 根据更新间隔计算预期时间
            update_interval = ranking.update_interval
            expected_times = self._calculate_expected_times(current_time, update_interval)
            
            for expected_time in expected_times:
                task_key = f"page_{ranking.channel}_{expected_time.strftime('%Y%m%d_%H')}"
                
                # 检查是否有该时间的数据
                has_data = await self._check_page_data_exists(ranking.id, expected_time)
                
                if not has_data and task_key not in self.missing_tasks:
                    logger.warning(f"发现缺失的页面任务: {ranking.channel} at {expected_time}")
                    self.missing_tasks[task_key] = MissingTaskInfo(
                        task_type=TaskType.PAGE,
                        channel=ranking.channel,
                        expected_time=expected_time
                    )
    
    async def _process_retry_tasks(self, current_time: datetime):
        """处理需要重试的任务"""
        retry_tasks = []
        
        for task_key, task_info in self.missing_tasks.items():
            # 检查是否需要重试
            if task_info.retry_count >= task_info.max_retries:
                # 已达到最大重试次数，生成警告日志
                await self._log_final_failure(task_info)
                continue
            
            # 检查重试间隔（至少等待10分钟）
            if (task_info.last_retry_time and 
                current_time - task_info.last_retry_time < timedelta(minutes=10)):
                continue
            
            retry_tasks.append((task_key, task_info))
        
        # 执行重试任务
        for task_key, task_info in retry_tasks:
            await self._retry_task(task_key, task_info)
    
    async def _retry_task(self, task_key: str, task_info: MissingTaskInfo):
        """重试单个任务"""
        logger.info(f"开始重试任务: {task_key} (第 {task_info.retry_count + 1} 次)")
        
        try:
            if task_info.task_type == TaskType.JIAZI:
                success = await self._retry_jiazi_task()
            else:
                success = await self._retry_page_task(task_info.channel)
            
            if success:
                logger.info(f"任务重试成功: {task_key}")
                # 从缺失任务列表中移除
                del self.missing_tasks[task_key]
            else:
                # 重试失败，更新重试信息
                task_info.retry_count += 1
                task_info.last_retry_time = datetime.now()
                task_info.errors.append(f"重试 {task_info.retry_count} 失败")
                logger.warning(f"任务重试失败: {task_key}, 重试次数: {task_info.retry_count}")
                
        except Exception as e:
            task_info.retry_count += 1
            task_info.last_retry_time = datetime.now()
            task_info.errors.append(f"重试 {task_info.retry_count} 异常: {str(e)}")
            logger.error(f"任务重试异常: {task_key}, 错误: {e}")
    
    async def _retry_jiazi_task(self) -> bool:
        """重试夹子榜任务"""
        try:
            result = await get_crawl_service().crawl_and_save("jiazi")
            return result is not None and result.get('success', False)
            
        except Exception as e:
            logger.error(f"夹子榜重试失败: {e}")
            return False
    
    async def _retry_page_task(self, channel: str) -> bool:
        """重试页面任务"""
        try:
            result = await get_crawl_service().crawl_and_save(channel)
            return result is not None and result.get('success', False)
            
        except Exception as e:
            logger.error(f"页面任务重试失败 ({channel}): {e}")
            return False
    
    async def _check_jiazi_data_exists(self, expected_time: datetime) -> bool:
        """检查夹子榜数据是否存在"""
        try:
            with get_session_sync() as session:
                # 检查该时间点前后30分钟是否有数据
                time_window_start = expected_time - timedelta(minutes=30)
                time_window_end = expected_time + timedelta(minutes=30)
                
                # 查询排名快照数据
                from sqlmodel import select
                stmt = select(RankingSnapshot).where(
                    RankingSnapshot.ranking_id == 1,  # 夹子榜的数字ID
                    RankingSnapshot.snapshot_time >= time_window_start,
                    RankingSnapshot.snapshot_time <= time_window_end
                )
                result = session.exec(stmt)
                return result.first() is not None
                
        except Exception as e:
            logger.error(f"检查夹子榜数据失败: {e}")
            return True  # 出错时假设数据存在，避免误报
    
    async def _check_page_data_exists(self, ranking_id: int, expected_time: datetime) -> bool:
        """检查页面数据是否存在"""
        try:
            with get_session_sync() as session:
                # 检查该时间点前后30分钟是否有数据
                time_window_start = expected_time - timedelta(minutes=30)
                time_window_end = expected_time + timedelta(minutes=30)
                
                # 查询排名快照数据
                from sqlmodel import select
                stmt = select(RankingSnapshot).where(
                    RankingSnapshot.ranking_id == ranking_id,
                    RankingSnapshot.snapshot_time >= time_window_start,
                    RankingSnapshot.snapshot_time <= time_window_end
                )
                result = session.exec(stmt)
                return result.first() is not None
                
        except Exception as e:
            logger.error(f"检查页面数据失败 (ranking_id={ranking_id}): {e}")
            return True  # 出错时假设数据存在，避免误报
    
    async def _get_rankings(self) -> List[Ranking]:
        """获取所有榜单配置"""
        try:
            with get_session_sync() as session:
                from sqlmodel import select
                stmt = select(Ranking)
                result = session.exec(stmt)
                return result.all()
        except Exception as e:
            logger.error(f"获取榜单配置失败: {e}")
            return []
    
    def _calculate_expected_times(self, current_time: datetime, update_interval: int) -> List[datetime]:
        """根据更新间隔计算预期时间"""
        expected_times = []
        
        # 检查最近的几个时间点
        for i in range(1, 4):  # 检查最近3个间隔
            hours_ago = i * update_interval
            expected_time = current_time - timedelta(hours=hours_ago)
            # 对齐到整点
            expected_time = expected_time.replace(minute=0, second=0, microsecond=0)
            expected_times.append(expected_time)
        
        return expected_times
    
    async def _log_final_failure(self, task_info: MissingTaskInfo):
        """记录最终失败的警告日志"""
        error_summary = "; ".join(task_info.errors)
        warning_msg = (
            f"⚠️ 任务最终失败警告 ⚠️\n"
            f"任务类型: {task_info.task_type.value}\n"
            f"频道: {task_info.channel}\n"
            f"预期时间: {task_info.expected_time}\n"
            f"重试次数: {task_info.retry_count}/{task_info.max_retries}\n"
            f"错误历史: {error_summary}\n"
            f"请手动检查并处理此问题！"
        )
        
        logger.warning(warning_msg)
        
        # 也可以发送到外部监控系统（如邮件、钉钉等）
        # await self._send_alert(warning_msg)
    
    def get_monitoring_status(self) -> Dict:
        """获取监控状态"""
        return {
            "is_running": self.is_running,
            "monitor_interval": self.monitor_interval,
            "missing_tasks_count": len(self.missing_tasks),
            "missing_tasks": {
                key: {
                    "task_type": info.task_type.value,
                    "channel": info.channel,
                    "expected_time": info.expected_time.isoformat(),
                    "retry_count": info.retry_count,
                    "max_retries": info.max_retries,
                    "errors": info.errors
                }
                for key, info in self.missing_tasks.items()
            }
        }


# 全局实例
_task_monitor_service = None


def get_task_monitor_service() -> TaskMonitorService:
    """获取任务监控服务实例"""
    global _task_monitor_service
    if _task_monitor_service is None:
        _task_monitor_service = TaskMonitorService()
    return _task_monitor_service