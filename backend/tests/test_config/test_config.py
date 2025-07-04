"""
配置模块测试
"""
import pytest
import os
import tempfile
from typing import Any, Dict
from pathlib import Path


class TestConfig:
    """配置模块测试类"""
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        from app.config import get_settings
        
        settings = get_settings()
        # 检查默认配置值
        assert settings.env == "dev"
        assert settings.project_name == "JJCrawler"
        assert settings.project_version == "1.0.0"
        assert settings.debug == False
        assert Path(settings.data_dir).exists()
        assert Path(settings.logs_dir).exists()
    
    def test_database_config(self):
        """测试数据库配置"""
        from app.config import get_settings
        
        settings = get_settings().database
        
        # 检查数据库配置
        assert settings.url.startswith("sqlite:///")
        assert settings.echo == False
        assert settings.pool_size >= 1
        assert 0 < settings.max_overflow < 100
        assert 0 < settings.pool_timeout < 300
        assert settings.pool_recycle >= 300
    
    def test_scheduler_config(self):
        """测试调度器配置"""
        from app.config import get_settings
        
        scheduler_settings = get_settings().scheduler
        
        # 检查调度器配置
        assert scheduler_settings.timezone == "Asia/Shanghai"
        assert scheduler_settings.max_workers >= 1
        assert scheduler_settings.job_store_type == "SQLAlchemyJobStore"
        assert scheduler_settings.job_store_url is not None
        assert isinstance(scheduler_settings.job_defaults, dict)
    
    def test_crawler_config(self):
        """测试爬虫配置"""
        from app.config import get_settings
        
        crawler_settings = get_settings().crawler
        
        # 检查爬虫配置
        assert crawler_settings.user_agent is not None
        assert crawler_settings.timeout >= 5
        assert crawler_settings.retry_times >= 1
        assert crawler_settings.retry_delay >= 0.1
        assert crawler_settings.request_delay >= 0.1
        assert crawler_settings.concurrent_requests >= 1
    
    def test_logging_config(self):
        """测试日志配置"""
        from app.config import get_settings
        
        log_settings = get_settings().logging
        
        # 检查日志配置
        assert log_settings.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert log_settings.log_format is not None
        assert log_settings.console_enabled == True
        assert log_settings.file_enabled == True
        assert log_settings.file_path is not None
        assert log_settings.max_bytes >= 1024 * 1024  # 至少1MB
        assert log_settings.backup_count >= 1
        assert log_settings.error_file_enabled == True
        assert log_settings.error_file_path is not None
    
    def test_api_config(self):
        """测试API配置"""
        from app.config import get_settings
        
        api_settings = get_settings().api
        
        # 检查API配置
        assert api_settings.title is not None
        assert api_settings.description is not None
        assert api_settings.version == "v1"  # 用户修改后的版本
        assert api_settings.host == "0.0.0.0"
        assert 1 <= api_settings.port <= 65535
        assert api_settings.debug == False
        assert api_settings.cors_enabled == True
        assert isinstance(api_settings.cors_origins, list)
        assert isinstance(api_settings.cors_methods, list)
        assert isinstance(api_settings.cors_headers, list)
        assert api_settings.default_page_size >= 1
        assert api_settings.max_page_size >= api_settings.default_page_size
    
    def test_environment_override(self, mocker):
        """测试环境变量覆盖配置"""
        # 使用pytest-mock模拟环境变量
        mocker.patch.dict(os.environ, {
            'ENV': 'test',
            'DEBUG': 'true',
            'API_PORT': '9000',
            'DATABASE_URL': 'sqlite:///test.db'
        })
        
        # 重新加载配置以获取环境变量
        from app.config import Settings
        test_settings = Settings()
        
        assert test_settings.env == "test"
        assert test_settings.debug == True
        assert test_settings.api.port == 9000
        assert test_settings.database.url == "sqlite:///test.db"
    
    def test_config_validation(self):
        """测试配置验证"""
        from app.config import Settings
        
        # 测试有效配置
        settings = Settings(
            env="dev",
            debug=False,
            project_name="TestApp"
        )
        
        assert settings.env == "dev"
        assert settings.debug == False
        assert settings.project_name == "TestApp"
    
    def test_invalid_config_validation(self):
        """测试无效配置验证"""
        from app.config import Settings
        
        # 测试无效环境
        with pytest.raises(ValueError):
            Settings(env="invalid")
    
    def test_environment_methods(self):
        """测试环境判断方法"""
        from app.config import get_settings
        
        settings = get_settings()
        
        # 根据默认环境dev进行测试
        assert settings.is_development() == True
        assert settings.is_testing() == False
        assert settings.is_production() == False
    
    def test_database_url_method(self):
        """测试数据库URL获取方法"""
        from app.config import get_settings, get_database_url
        
        settings = get_settings()
        
        # 测试方法
        assert settings.get_database_url() == settings.database.url
        assert get_database_url() == settings.database.url
        assert get_database_url().startswith("sqlite:///")
    
    def test_debug_methods(self):
        """测试调试模式判断方法"""
        from app.config import is_debug, is_production
        
        # 测试便捷方法
        assert isinstance(is_debug(), bool)
        assert isinstance(is_production(), bool)
    
    def test_directory_creation(self):
        """测试目录创建"""
        from app.config import get_settings
        
        settings = get_settings()
        
        # 验证目录是否存在
        assert Path(settings.data_dir).exists()
        assert Path(settings.logs_dir).exists()
        assert Path(settings.logging.file_path).parent.exists()
    
    def test_log_level_validation(self):
        """测试日志级别验证"""
        from app.config import LoggingSettings
        
        # 测试有效的日志级别
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for level in valid_levels:
            log_settings = LoggingSettings(level=level)
            assert log_settings.level == level
        
        # 测试无效的日志级别
        with pytest.raises(ValueError):
            LoggingSettings(level="INVALID")
    
    def test_field_constraints(self):
        """测试字段约束"""
        from app.config import Settings
        
        settings = Settings()
        
        # 测试数据库配置约束
        assert 1 <= settings.database.pool_size <= 50
        assert 0 <= settings.database.max_overflow <= 100
        assert 1 <= settings.database.pool_timeout <= 300
        assert 300 <= settings.database.pool_recycle <= 86400
        
        # 测试API配置约束
        assert 1 <= settings.api.port <= 65535
        assert 1 <= settings.api.default_page_size <= 100
        assert 1 <= settings.api.max_page_size <= 1000
        
        # 测试爬虫配置约束
        assert 5 <= settings.crawler.timeout <= 300
        assert 1 <= settings.crawler.retry_times <= 10
        assert 0.1 <= settings.crawler.retry_delay <= 10.0
        assert 0.1 <= settings.crawler.request_delay <= 60.0
        assert 1 <= settings.crawler.concurrent_requests <= 10
        
        # 测试调度器配置约束
        assert 1 <= settings.scheduler.max_workers <= 20
        
        # 测试日志配置约束
        assert 1024 * 1024 <= settings.logging.max_bytes <= 100 * 1024 * 1024
        assert 1 <= settings.logging.backup_count <= 20
    
    def test_config_dict_fields(self):
        """测试字典类型配置字段"""
        from app.config import get_settings
        
        settings = get_settings()
        
        # 测试调度器默认配置
        job_defaults = settings.scheduler.job_defaults
        assert isinstance(job_defaults, dict)
        assert "coalesce" in job_defaults
        assert "max_instances" in job_defaults
        assert "misfire_grace_time" in job_defaults
    
    def test_config_list_fields(self):
        """测试列表类型配置字段"""
        from app.config import get_settings
        
        settings = get_settings()
        
        # 测试CORS配置
        assert isinstance(settings.api.cors_origins, list)
        assert isinstance(settings.api.cors_methods, list)
        assert isinstance(settings.api.cors_headers, list)
        
        # 检查默认值
        assert "GET" in settings.api.cors_methods
        assert "POST" in settings.api.cors_methods
    
    def test_config_case_insensitive(self, mocker):
        """测试配置大小写不敏感"""
        from app.config import Settings
        
        # 测试环境变量大小写不敏感
        mocker.patch.dict(os.environ, {'env': 'TEST'})
        settings = Settings()
        assert settings.env == "test"  # 应该被转换为小写
    
    def test_config_file_paths(self):
        """测试配置文件路径"""
        from app.config import get_settings
        
        settings = get_settings()
        
        # 测试日志文件路径
        assert settings.logging.file_path.endswith('.log')
        assert settings.logging.error_file_path.endswith('.log')
        
        # 测试数据库文件路径
        assert settings.database.url.endswith('.db')
        
        # 测试调度器存储路径
        if settings.scheduler.job_store_url:
            assert settings.scheduler.job_store_url.endswith('.db')
    
    def test_settings_singleton(self):
        """测试设置单例"""
        from app.config import get_settings, _settings
        
        # 多次获取应该返回同一个实例
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
        assert settings1 is _settings 