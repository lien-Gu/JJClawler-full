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
    
    def test_load_default_config(self, expected_defaults):
        """测试加载默认配置"""
        from app.config import get_settings
        
        settings = get_settings()
        # 使用conftest中的期望值进行验证
        assert settings.env == expected_defaults["env"]
        assert settings.project_name == expected_defaults["project_name"]
        assert settings.project_version == expected_defaults["project_version"]
        assert settings.debug == expected_defaults["debug"]
        assert Path(settings.data_dir).exists()
        assert Path(settings.logs_dir).exists()
    
    def test_database_config(self, database_constraints, constraint_validator):
        """测试数据库配置"""
        from app.config import get_settings
        
        settings = get_settings().database
        
        # 使用conftest中的约束验证器
        assert settings.url.startswith("sqlite:///")
        assert settings.echo == False
        assert constraint_validator(settings.pool_size, database_constraints["pool_size"])
        assert constraint_validator(settings.max_overflow, database_constraints["max_overflow"])
        assert constraint_validator(settings.pool_timeout, database_constraints["pool_timeout"])
        assert constraint_validator(settings.pool_recycle, database_constraints["pool_recycle"])
    
    def test_scheduler_config(self, expected_defaults):
        """测试调度器配置"""
        from app.config import get_settings
        
        scheduler_settings = get_settings().scheduler
        
        # 使用conftest中的期望值
        assert scheduler_settings.timezone == expected_defaults["scheduler_timezone"]
        assert scheduler_settings.max_workers >= 1
        assert scheduler_settings.job_store_type == expected_defaults["scheduler_job_store_type"]
        assert scheduler_settings.job_store_url is not None
        assert isinstance(scheduler_settings.job_defaults, dict)
    
    def test_crawler_config(self, crawler_constraints, constraint_validator):
        """测试爬虫配置"""
        from app.config import get_settings
        
        crawler_settings = get_settings().crawler
        
        # 使用conftest中的约束验证器
        assert crawler_settings.user_agent is not None
        assert constraint_validator(crawler_settings.timeout, crawler_constraints["timeout"])
        assert constraint_validator(crawler_settings.retry_times, crawler_constraints["retry_times"])
        assert constraint_validator(crawler_settings.retry_delay, crawler_constraints["retry_delay"])
        assert constraint_validator(crawler_settings.request_delay, crawler_constraints["request_delay"])
        assert constraint_validator(crawler_settings.concurrent_requests, crawler_constraints["concurrent_requests"])
    
    def test_logging_config(self, logging_constraints, constraint_validator):
        """测试日志配置"""
        from app.config import get_settings
        
        log_settings = get_settings().logging
        
        # 检查日志配置
        assert log_settings.level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        assert log_settings.log_format is not None
        assert log_settings.console_enabled == True
        assert log_settings.file_enabled == True
        assert log_settings.file_path is not None
        assert constraint_validator(log_settings.max_bytes, logging_constraints["max_bytes"])
        assert constraint_validator(log_settings.backup_count, logging_constraints["backup_count"])
        assert log_settings.error_file_enabled == True
        assert log_settings.error_file_path is not None
    
    def test_api_config(self, expected_defaults, api_constraints, constraint_validator, expected_collections, collection_validator):
        """测试API配置"""
        from app.config import get_settings
        
        api_settings = get_settings().api
        
        # 使用conftest中的验证器和期望值
        assert api_settings.title is not None
        assert api_settings.description is not None
        assert api_settings.version == expected_defaults["api_version"]
        assert api_settings.host == expected_defaults["api_host"]
        assert constraint_validator(api_settings.port, api_constraints["port"])
        assert api_settings.debug == False
        assert api_settings.cors_enabled == True
        assert isinstance(api_settings.cors_origins, list)
        assert isinstance(api_settings.cors_methods, list)
        assert isinstance(api_settings.cors_headers, list)
        assert constraint_validator(api_settings.default_page_size, api_constraints["default_page_size"])
        assert constraint_validator(api_settings.max_page_size, api_constraints["max_page_size"])
        assert collection_validator(api_settings.cors_methods, expected_collections["cors_methods"])
    
    def test_environment_override(self, sample_env_vars, mock_env_override):
        """测试环境变量覆盖配置"""
        # 使用conftest中的mock数据和工具函数
        mock_env_override(sample_env_vars)
        
        from app.config import Settings
        test_settings = Settings()
        
        assert test_settings.env == "test"
        assert test_settings.debug == True
        assert test_settings.api.port == 9000
        assert test_settings.database.url == "sqlite:///test.db"
    
    def test_config_validation(self, valid_config_params, config_factory):
        """测试配置验证"""
        # 使用conftest中的配置工厂和有效参数
        settings = config_factory(**valid_config_params)
        
        assert settings.env == valid_config_params["env"]
        assert settings.debug == valid_config_params["debug"]
        assert settings.project_name == valid_config_params["project_name"]

    def test_invalid_config_validation(self, invalid_env_values, config_factory):
        """测试无效配置验证"""
        # 使用conftest中的无效值列表
        for invalid_env in invalid_env_values:
            with pytest.raises(ValueError):
                config_factory(env=invalid_env)
    
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
    
    def test_log_level_validation(self, valid_log_levels, invalid_log_levels):
        """测试日志级别验证"""
        from app.config import LoggingSettings
        
        # 使用conftest中的有效级别列表
        for level in valid_log_levels:
            log_settings = LoggingSettings(level=level)
            assert log_settings.level == level
        
        # 使用conftest中的无效级别列表
        for invalid_level in invalid_log_levels:
            with pytest.raises(ValueError):
                LoggingSettings(level=invalid_level)
    
    def test_field_constraints(self, database_constraints, api_constraints, crawler_constraints, 
                             scheduler_constraints, logging_constraints, constraint_validator):
        """测试字段约束"""
        from app.config import Settings
        
        settings = Settings()
        
        # 使用conftest中的约束验证器进行所有约束验证
        # 数据库配置约束
        assert constraint_validator(settings.database.pool_size, database_constraints["pool_size"])
        assert constraint_validator(settings.database.max_overflow, database_constraints["max_overflow"])
        assert constraint_validator(settings.database.pool_timeout, database_constraints["pool_timeout"])
        assert constraint_validator(settings.database.pool_recycle, database_constraints["pool_recycle"])
        
        # API配置约束
        assert constraint_validator(settings.api.port, api_constraints["port"])
        assert constraint_validator(settings.api.default_page_size, api_constraints["default_page_size"])
        assert constraint_validator(settings.api.max_page_size, api_constraints["max_page_size"])
        
        # 爬虫配置约束
        assert constraint_validator(settings.crawler.timeout, crawler_constraints["timeout"])
        assert constraint_validator(settings.crawler.retry_times, crawler_constraints["retry_times"])
        assert constraint_validator(settings.crawler.retry_delay, crawler_constraints["retry_delay"])
        assert constraint_validator(settings.crawler.request_delay, crawler_constraints["request_delay"])
        assert constraint_validator(settings.crawler.concurrent_requests, crawler_constraints["concurrent_requests"])
        
        # 调度器配置约束
        assert constraint_validator(settings.scheduler.max_workers, scheduler_constraints["max_workers"])
        
        # 日志配置约束
        assert constraint_validator(settings.logging.max_bytes, logging_constraints["max_bytes"])
        assert constraint_validator(settings.logging.backup_count, logging_constraints["backup_count"])
    
    def test_config_dict_fields(self, expected_collections, collection_validator):
        """测试字典类型配置字段"""
        from app.config import get_settings
        
        settings = get_settings()
        
        # 使用conftest中的集合验证器
        job_defaults = settings.scheduler.job_defaults
        assert isinstance(job_defaults, dict)
        assert collection_validator(job_defaults.keys(), expected_collections["job_defaults_keys"])
    
    def test_config_list_fields(self, expected_collections, collection_validator):
        """测试列表类型配置字段"""
        from app.config import get_settings
        
        settings = get_settings()
        
        # 使用conftest中的集合验证器
        assert isinstance(settings.api.cors_origins, list)
        assert isinstance(settings.api.cors_methods, list)
        assert isinstance(settings.api.cors_headers, list)
        assert collection_validator(settings.api.cors_methods, expected_collections["cors_methods"])
    
    def test_config_case_insensitive(self, case_sensitive_env_vars, mock_env_override):
        """测试配置大小写不敏感"""
        from app.config import Settings
        
        # 使用conftest中的大小写测试数据
        mock_env_override(case_sensitive_env_vars)
        settings = Settings()
        assert settings.env == "test"  # 应该被转换为小写
    
    def test_config_file_paths(self, expected_file_extensions, file_extension_validator):
        """测试配置文件路径"""
        from app.config import get_settings
        
        settings = get_settings()
        
        # 使用conftest中的文件扩展名验证器
        assert file_extension_validator(settings.logging.file_path, expected_file_extensions["log_files"])
        assert file_extension_validator(settings.logging.error_file_path, expected_file_extensions["log_files"])
        assert file_extension_validator(settings.database.url, expected_file_extensions["database_files"])
        
        # 测试调度器存储路径
        if settings.scheduler.job_store_url:
            assert file_extension_validator(settings.scheduler.job_store_url, expected_file_extensions["database_files"])
    
    def test_settings_singleton(self):
        """测试设置单例"""
        from app.config import get_settings, _settings
        
        # 多次获取应该返回同一个实例
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
        assert settings1 is _settings
    
    # ==========================================
    # MVP环境测试 - 使用conftest中的组合fixtures
    # ==========================================
    
    def test_dev_environment_behavior(self, dev_environment_setup):
        """测试开发环境行为"""
        from app.config import Settings
        
        dev_environment_setup
        settings = Settings()
        
        assert settings.env == "dev"
        assert settings.debug == True
        assert settings.is_development() == True
    
    def test_test_environment_behavior(self, test_environment_setup):
        """测试测试环境行为"""
        from app.config import Settings
        
        test_environment_setup
        settings = Settings()
        
        assert settings.env == "test"
        assert settings.debug == False
        assert settings.is_testing() == True
        assert settings.database.url == "sqlite:///:memory:"
    
    def test_prod_environment_behavior(self, prod_environment_setup):
        """测试生产环境行为"""
        from app.config import Settings
        
        prod_environment_setup
        settings = Settings()
        
        assert settings.env == "prod"
        assert settings.debug == False
        assert settings.is_production() == True 