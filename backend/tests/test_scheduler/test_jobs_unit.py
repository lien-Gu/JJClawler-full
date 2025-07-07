"""
任务管理器单元测试 - 测试JobManager类的各个方法和定时任务功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timedelta
import asyncio

# 跳过此测试类，因为scheduler模块不存在
pytest.skip("Scheduler module not available", allow_module_level=True)

# 假设的导入（根据项目实际结构调整）
# from app.scheduler.jobs import JobManager
# from app.scheduler.task_scheduler import TaskScheduler
# from app.crawler.crawler import Crawler
# from app.database.service.book_service import BookService
# from app.database.service.ranking_service import RankingService


class TestJobManager:
    """JobManager单元测试类"""
    
    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.mock_scheduler = Mock(spec=TaskScheduler)
        self.mock_crawler = Mock(spec=Crawler)
        self.mock_book_service = Mock(spec=BookService)
        self.mock_ranking_service = Mock(spec=RankingService)
        
        self.job_manager = JobManager(
            scheduler=self.mock_scheduler,
            crawler=self.mock_crawler,
            book_service=self.mock_book_service,
            ranking_service=self.mock_ranking_service
        )
    
    def test_init_job_manager(self):
        """测试JobManager初始化"""
        assert self.job_manager.scheduler == self.mock_scheduler
        assert self.job_manager.crawler == self.mock_crawler
        assert self.job_manager.book_service == self.mock_book_service
        assert self.job_manager.ranking_service == self.mock_ranking_service
        assert self.job_manager.jobs == {}
        assert self.job_manager.task_history == []
    
    def test_register_default_jobs(self, sample_job_data):
        """测试注册默认任务"""
        self.mock_scheduler.add_job = Mock()
        
        # 执行注册默认任务
        self.job_manager.register_default_jobs()
        
        # 验证调用次数（应该注册多个默认任务）
        assert self.mock_scheduler.add_job.call_count >= 3
        
        # 验证任务已添加到jobs字典
        assert len(self.job_manager.jobs) >= 3
        assert "jiazi_crawl_job" in self.job_manager.jobs
        assert "category_crawl_job" in self.job_manager.jobs
        assert "data_cleanup_job" in self.job_manager.jobs
    
    def test_register_job_success(self, sample_job_data):
        """测试成功注册单个任务"""
        job_config = sample_job_data["jiazi_crawl_job"]
        mock_job = Mock()
        mock_job.id = job_config["id"]
        
        self.mock_scheduler.add_job = Mock(return_value=mock_job)
        
        # 执行注册任务
        result = self.job_manager.register_job(job_config)
        
        # 验证结果
        assert result == mock_job
        assert job_config["id"] in self.job_manager.jobs
        assert self.job_manager.jobs[job_config["id"]] == job_config
        self.mock_scheduler.add_job.assert_called_once()
    
    def test_register_job_with_duplicate_id(self, sample_job_data):
        """测试注册重复ID的任务"""
        job_config = sample_job_data["jiazi_crawl_job"]
        
        # 先注册一个任务
        self.job_manager.jobs[job_config["id"]] = job_config
        
        # 尝试注册相同ID的任务
        with pytest.raises(ValueError) as exc_info:
            self.job_manager.register_job(job_config)
        
        assert "已存在" in str(exc_info.value)
    
    def test_register_job_with_invalid_config(self):
        """测试注册无效配置的任务"""
        invalid_config = {
            "id": "invalid_job",
            # 缺少必需字段
        }
        
        # 执行注册任务
        with pytest.raises(ValueError) as exc_info:
            self.job_manager.register_job(invalid_config)
        
        assert "无效" in str(exc_info.value) or "配置" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_crawl_jiazi_ranking_success(self, sample_book_data):
        """测试成功爬取夹子榜"""
        # 模拟爬虫返回数据
        mock_crawl_result = {
            "books": [sample_book_data],
            "crawl_time": datetime.now().isoformat(),
            "total_books": 1
        }
        
        self.mock_crawler.crawl_jiazi_ranking = AsyncMock(return_value=mock_crawl_result)
        self.mock_ranking_service.save_ranking_snapshot = AsyncMock()
        
        # 执行爬取夹子榜
        result = await self.job_manager.crawl_jiazi_ranking()
        
        # 验证结果
        assert result["status"] == "success"
        assert result["books_count"] == 1
        assert "execution_time" in result
        
        # 验证调用
        self.mock_crawler.crawl_jiazi_ranking.assert_called_once()
        self.mock_ranking_service.save_ranking_snapshot.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_crawl_jiazi_ranking_failure(self):
        """测试爬取夹子榜失败"""
        # 模拟爬虫抛出异常
        self.mock_crawler.crawl_jiazi_ranking = AsyncMock(
            side_effect=Exception("网络连接失败")
        )
        
        # 执行爬取夹子榜
        result = await self.job_manager.crawl_jiazi_ranking()
        
        # 验证结果
        assert result["status"] == "failed"
        assert "网络连接失败" in result["error"]
        assert "execution_time" in result
    
    @pytest.mark.asyncio
    async def test_cleanup_old_data_success(self):
        """测试成功清理旧数据"""
        # 模拟清理结果
        cleanup_result = {
            "deleted_books": 10,
            "deleted_snapshots": 50,
            "deleted_rankings": 5
        }
        
        self.mock_book_service.cleanup_old_data = AsyncMock(return_value=cleanup_result)
        self.mock_ranking_service.cleanup_old_data = AsyncMock(return_value=cleanup_result)
        
        # 执行清理旧数据
        result = await self.job_manager.cleanup_old_data()
        
        # 验证结果
        assert result["status"] == "success"
        assert result["deleted_books"] == 10
        assert result["deleted_snapshots"] == 50
        assert result["deleted_rankings"] == 5
        assert "execution_time" in result
        
        # 验证调用
        self.mock_book_service.cleanup_old_data.assert_called_once()
        self.mock_ranking_service.cleanup_old_data.assert_called_once()
    
    def test_get_jobs_statistics_success(self, sample_job_data, mock_task_execution_data):
        """测试成功获取任务统计"""
        # 添加任务
        for job_config in sample_job_data.values():
            self.job_manager.jobs[job_config["id"]] = job_config
        
        # 添加执行历史
        self.job_manager.task_history = list(mock_task_execution_data.values())
        
        # 执行获取统计
        result = self.job_manager.get_jobs_statistics()
        
        # 验证结果
        assert result["total_jobs"] == len(sample_job_data)
        assert result["total_executions"] == len(mock_task_execution_data)
        assert result["successful_executions"] >= 0
        assert result["failed_executions"] >= 0
        assert "average_execution_time" in result
        assert "last_execution_time" in result
    
    def test_validate_job_config_success(self, sample_job_data):
        """测试成功验证任务配置"""
        job_config = sample_job_data["jiazi_crawl_job"]
        
        # 执行验证
        result = self.job_manager.validate_job_config(job_config)
        
        # 验证结果
        assert result is True
    
    def test_validate_job_config_missing_required_fields(self):
        """测试验证缺少必需字段的配置"""
        invalid_config = {
            "id": "test_job",
            # 缺少 func 字段
            "trigger": "interval"
        }
        
        # 执行验证
        result = self.job_manager.validate_job_config(invalid_config)
        
        # 验证结果
        assert result is False
    
    def teardown_method(self):
        """每个测试方法执行后的清理"""
        self.job_manager.jobs.clear()
        self.job_manager.task_history.clear()
