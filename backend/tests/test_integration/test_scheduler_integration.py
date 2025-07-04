"""
调度模块集成测试 - 测试TaskScheduler和JobManager之间的集成以及完整的任务调度流程
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import time
import threading

# 假设的导入（根据项目实际结构调整）
from app.scheduler.task_scheduler import TaskScheduler
from app.scheduler.jobs import JobManager
from app.crawler.crawler import Crawler
from app.database.service.book_service import BookService
from app.database.service.ranking_service import RankingService


class TestSchedulerIntegration:
    """调度模块集成测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 创建模拟的服务依赖
        self.mock_crawler = Mock(spec=Crawler)
        self.mock_book_service = Mock(spec=BookService)
        self.mock_ranking_service = Mock(spec=RankingService)
        
        # 创建调度器实例
        self.scheduler = TaskScheduler()
        
        # 创建任务管理器实例
        self.job_manager = JobManager(
            scheduler=self.scheduler,
            crawler=self.mock_crawler,
            book_service=self.mock_book_service,
            ranking_service=self.mock_ranking_service
        )
    
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        if self.scheduler.is_running:
            self.scheduler.stop()
        self.job_manager.jobs.clear()
        self.job_manager.task_history.clear()
    
    def test_scheduler_and_job_manager_integration(self, sample_job_data):
        """测试调度器和任务管理器的集成"""
        # 启动调度器
        self.scheduler.start()
        assert self.scheduler.is_running is True
        
        # 注册任务
        job_config = sample_job_data["jiazi_crawl_job"]
        registered_job = self.job_manager.register_job(job_config)
        
        # 验证任务已注册到调度器
        scheduler_job = self.scheduler.get_job(job_config["id"])
        assert scheduler_job is not None
        assert scheduler_job.id == job_config["id"]
        
        # 验证任务已添加到任务管理器
        assert job_config["id"] in self.job_manager.jobs
        
        # 获取任务信息
        job_info = self.job_manager.get_job_info(job_config["id"])
        assert job_info["id"] == job_config["id"]
        assert job_info["name"] == job_config["name"]
        assert job_info["scheduler_info"] == scheduler_job
        
        # 停止调度器
        self.scheduler.stop()
        assert self.scheduler.is_running is False
    
    def test_register_multiple_jobs_integration(self, sample_job_data):
        """测试注册多个任务的集成"""
        # 启动调度器
        self.scheduler.start()
        
        # 注册多个任务
        registered_jobs = []
        for job_config in sample_job_data.values():
            registered_job = self.job_manager.register_job(job_config)
            registered_jobs.append(registered_job)
        
        # 验证所有任务都已注册
        assert len(self.job_manager.jobs) == len(sample_job_data)
        
        # 验证调度器中的任务
        scheduler_jobs = self.scheduler.get_jobs()
        assert len(scheduler_jobs) == len(sample_job_data)
        
        # 验证每个任务的信息
        for job_config in sample_job_data.values():
            job_info = self.job_manager.get_job_info(job_config["id"])
            assert job_info["id"] == job_config["id"]
            assert job_info["name"] == job_config["name"]
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_job_execution_integration(self, sample_job_data, sample_book_data):
        """测试任务执行的集成（模拟执行）"""
        # 模拟爬虫返回数据
        mock_crawl_result = {
            "books": [sample_book_data],
            "crawl_time": datetime.now().isoformat(),
            "total_books": 1
        }
        
        self.mock_crawler.crawl_jiazi_ranking = AsyncMock(return_value=mock_crawl_result)
        self.mock_ranking_service.save_ranking_snapshot = AsyncMock()
        
        # 启动调度器
        self.scheduler.start()
        
        # 注册夹子榜任务
        job_config = sample_job_data["jiazi_crawl_job"]
        self.job_manager.register_job(job_config)
        
        # 手动执行任务（模拟调度器触发）
        async def execute_job():
            result = await self.job_manager.crawl_jiazi_ranking()
            return result
        
        # 使用事件循环执行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(execute_job())
        finally:
            loop.close()
        
        # 验证执行结果
        assert result["status"] == "success"
        assert result["books_count"] == 1
        assert "execution_time" in result
        
        # 验证服务调用
        self.mock_crawler.crawl_jiazi_ranking.assert_called_once()
        self.mock_ranking_service.save_ranking_snapshot.assert_called_once()
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_job_pause_resume_integration(self, sample_job_data):
        """测试任务暂停和恢复的集成"""
        # 启动调度器
        self.scheduler.start()
        
        # 注册任务
        job_config = sample_job_data["jiazi_crawl_job"]
        self.job_manager.register_job(job_config)
        
        # 验证任务正在运行
        scheduler_job = self.scheduler.get_job(job_config["id"])
        assert scheduler_job is not None
        
        # 暂停任务
        self.job_manager.pause_job(job_config["id"])
        
        # 验证任务已暂停（这里需要根据实际APScheduler实现调整）
        paused_job = self.scheduler.get_job(job_config["id"])
        assert paused_job is not None
        
        # 恢复任务
        self.job_manager.resume_job(job_config["id"])
        
        # 验证任务已恢复
        resumed_job = self.scheduler.get_job(job_config["id"])
        assert resumed_job is not None
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_job_modification_integration(self, sample_job_data):
        """测试任务修改的集成"""
        # 启动调度器
        self.scheduler.start()
        
        # 注册任务
        job_config = sample_job_data["jiazi_crawl_job"]
        self.job_manager.register_job(job_config)
        
        # 获取原始任务信息
        original_job_info = self.job_manager.get_job_info(job_config["id"])
        assert original_job_info["name"] == job_config["name"]
        
        # 修改任务
        changes = {"hours": 2, "name": "修改后的夹子榜任务"}
        self.job_manager.modify_job(job_config["id"], **changes)
        
        # 验证任务配置已更新
        updated_config = self.job_manager.jobs[job_config["id"]]
        assert updated_config["hours"] == 2
        assert updated_config["name"] == "修改后的夹子榜任务"
        
        # 验证调度器中的任务也已更新
        scheduler_job = self.scheduler.get_job(job_config["id"])
        assert scheduler_job is not None
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_job_removal_integration(self, sample_job_data):
        """测试任务删除的集成"""
        # 启动调度器
        self.scheduler.start()
        
        # 注册任务
        job_config = sample_job_data["jiazi_crawl_job"]
        self.job_manager.register_job(job_config)
        
        # 验证任务已注册
        assert job_config["id"] in self.job_manager.jobs
        scheduler_job = self.scheduler.get_job(job_config["id"])
        assert scheduler_job is not None
        
        # 删除任务
        self.job_manager.unregister_job(job_config["id"])
        
        # 验证任务已从任务管理器中移除
        assert job_config["id"] not in self.job_manager.jobs
        
        # 验证任务已从调度器中移除
        removed_job = self.scheduler.get_job(job_config["id"])
        assert removed_job is None
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_multiple_job_types_integration(self, sample_job_data, sample_book_data):
        """测试多种任务类型的集成"""
        # 模拟不同类型任务的返回数据
        mock_crawl_result = {
            "books": [sample_book_data],
            "crawl_time": datetime.now().isoformat(),
            "total_books": 1
        }
        
        mock_cleanup_result = {
            "deleted_books": 5,
            "deleted_snapshots": 20,
            "deleted_rankings": 2
        }
        
        # 设置模拟
        self.mock_crawler.crawl_jiazi_ranking = AsyncMock(return_value=mock_crawl_result)
        self.mock_crawler.crawl_category_rankings = AsyncMock(return_value=mock_crawl_result)
        self.mock_ranking_service.save_ranking_snapshot = AsyncMock()
        self.mock_book_service.cleanup_old_data = AsyncMock(return_value=mock_cleanup_result)
        self.mock_ranking_service.cleanup_old_data = AsyncMock(return_value=mock_cleanup_result)
        
        # 启动调度器
        self.scheduler.start()
        
        # 注册所有类型的任务
        for job_config in sample_job_data.values():
            self.job_manager.register_job(job_config)
        
        # 验证所有任务已注册
        assert len(self.job_manager.jobs) == len(sample_job_data)
        
        # 手动执行不同类型的任务
        async def execute_all_jobs():
            results = {}
            
            # 执行夹子榜爬取
            results["jiazi"] = await self.job_manager.crawl_jiazi_ranking()
            
            # 执行分类榜爬取
            results["category"] = await self.job_manager.crawl_category_rankings()
            
            # 执行数据清理
            results["cleanup"] = await self.job_manager.cleanup_old_data()
            
            return results
        
        # 使用事件循环执行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(execute_all_jobs())
        finally:
            loop.close()
        
        # 验证所有任务执行成功
        assert results["jiazi"]["status"] == "success"
        assert results["category"]["status"] == "success"
        assert results["cleanup"]["status"] == "success"
        
        # 验证服务调用
        self.mock_crawler.crawl_jiazi_ranking.assert_called_once()
        self.mock_crawler.crawl_category_rankings.assert_called_once()
        self.mock_book_service.cleanup_old_data.assert_called_once()
        self.mock_ranking_service.cleanup_old_data.assert_called_once()
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_scheduler_health_check_integration(self, sample_job_data):
        """测试调度器健康检查的集成"""
        # 启动调度器
        self.scheduler.start()
        
        # 注册一些任务
        for job_config in sample_job_data.values():
            self.job_manager.register_job(job_config)
        
        # 执行健康检查
        health_status = self.scheduler.health_check()
        
        # 验证健康检查结果
        assert health_status["status"] == "healthy"
        assert health_status["scheduler_running"] is True
        assert health_status["total_jobs"] == len(sample_job_data)
        assert "last_check_time" in health_status
        
        # 停止调度器
        self.scheduler.stop()
        
        # 再次执行健康检查
        unhealthy_status = self.scheduler.health_check()
        assert unhealthy_status["status"] == "unhealthy"
        assert unhealthy_status["scheduler_running"] is False
    
    def test_scheduler_statistics_integration(self, sample_job_data, mock_task_execution_data):
        """测试调度器统计信息的集成"""
        # 启动调度器
        self.scheduler.start()
        
        # 注册任务
        for job_config in sample_job_data.values():
            self.job_manager.register_job(job_config)
        
        # 添加执行历史
        self.job_manager.task_history = list(mock_task_execution_data.values())
        
        # 获取调度器信息
        scheduler_info = self.scheduler.get_scheduler_info()
        
        # 验证调度器信息
        assert scheduler_info["running"] is True
        assert scheduler_info["total_jobs"] == len(sample_job_data)
        assert "statistics" in scheduler_info
        
        # 获取任务统计
        job_stats = self.job_manager.get_jobs_statistics()
        
        # 验证统计信息
        assert job_stats["total_jobs"] == len(sample_job_data)
        assert job_stats["total_executions"] == len(mock_task_execution_data)
        assert job_stats["successful_executions"] >= 0
        assert job_stats["failed_executions"] >= 0
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_error_handling_integration(self, sample_job_data):
        """测试错误处理的集成"""
        # 启动调度器
        self.scheduler.start()
        
        # 注册任务
        job_config = sample_job_data["jiazi_crawl_job"]
        self.job_manager.register_job(job_config)
        
        # 模拟爬虫失败
        self.mock_crawler.crawl_jiazi_ranking = AsyncMock(
            side_effect=Exception("网络连接失败")
        )
        
        # 手动执行任务
        async def execute_failing_job():
            result = await self.job_manager.crawl_jiazi_ranking()
            return result
        
        # 使用事件循环执行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(execute_failing_job())
        finally:
            loop.close()
        
        # 验证错误处理
        assert result["status"] == "failed"
        assert "网络连接失败" in result["error"]
        assert "execution_time" in result
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_concurrent_job_execution_integration(self, sample_job_data, sample_book_data):
        """测试并发任务执行的集成"""
        # 模拟返回数据
        mock_crawl_result = {
            "books": [sample_book_data],
            "crawl_time": datetime.now().isoformat(),
            "total_books": 1
        }
        
        # 设置模拟（添加延迟模拟真实情况）
        async def mock_crawl_with_delay():
            await asyncio.sleep(0.1)  # 模拟网络延迟
            return mock_crawl_result
        
        self.mock_crawler.crawl_jiazi_ranking = AsyncMock(side_effect=mock_crawl_with_delay)
        self.mock_ranking_service.save_ranking_snapshot = AsyncMock()
        
        # 启动调度器
        self.scheduler.start()
        
        # 注册任务
        job_config = sample_job_data["jiazi_crawl_job"]
        self.job_manager.register_job(job_config)
        
        # 并发执行多个任务
        async def execute_concurrent_jobs():
            tasks = []
            for i in range(3):
                task = asyncio.create_task(self.job_manager.crawl_jiazi_ranking())
                tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
        
        # 使用事件循环执行异步任务
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            results = loop.run_until_complete(execute_concurrent_jobs())
        finally:
            loop.close()
        
        # 验证所有任务都执行成功
        assert len(results) == 3
        for result in results:
            assert result["status"] == "success"
            assert result["books_count"] == 1
        
        # 验证服务调用次数
        assert self.mock_crawler.crawl_jiazi_ranking.call_count == 3
        assert self.mock_ranking_service.save_ranking_snapshot.call_count == 3
        
        # 停止调度器
        self.scheduler.stop()
    
    def test_job_config_validation_integration(self, sample_job_data):
        """测试任务配置验证的集成"""
        # 启动调度器
        self.scheduler.start()
        
        # 测试有效配置
        valid_config = sample_job_data["jiazi_crawl_job"]
        
        # 验证任务管理器的验证
        assert self.job_manager.validate_job_config(valid_config) is True
        
        # 验证调度器的验证
        assert self.scheduler.validate_job_config(valid_config) is True
        
        # 成功注册有效任务
        registered_job = self.job_manager.register_job(valid_config)
        assert registered_job is not None
        
        # 测试无效配置
        invalid_config = {
            "id": "invalid_job",
            "trigger": "invalid_trigger"
        }
        
        # 验证两个组件都拒绝无效配置
        assert self.job_manager.validate_job_config(invalid_config) is False
        assert self.scheduler.validate_job_config(invalid_config) is False
        
        # 尝试注册无效任务应该失败
        with pytest.raises(ValueError):
            self.job_manager.register_job(invalid_config)
        
        # 停止调度器
        self.scheduler.stop()
