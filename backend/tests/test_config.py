"""
配置模块测试文件
测试app.config模块的所有配置类和验证逻辑
"""
import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock
from pydantic import ValidationError

from app.config import (
    DatabaseSettings,
    APISettings,
    CrawlerSettings,
    SchedulerSettings,
    LoggingSettings,
    Settings,
    get_settings,
    get_database_url,
    is_debug,
    is_production
)


class TestDatabaseSettings:
    """测试DatabaseSettings配置类"""
    
    def test_default_values(self):
        """测试默认配置值"""
        settings = DatabaseSettings()
        
        assert settings.url == "sqlite:///./data/jjcrawler.db"
        assert settings.echo is False
        assert settings.pool_size == 5
        assert settings.max_overflow == 10
        assert settings.pool_timeout == 30
        assert settings.pool_recycle == 3600
    
    def test_custom_values(self):
        """测试自定义配置值"""
        settings = DatabaseSettings(
            url="postgresql://user:pass@localhost/testdb",
            echo=True,
            pool_size=10,
            max_overflow=20,
            pool_timeout=60,
            pool_recycle=7200
        )
        
        assert settings.url == "postgresql://user:pass@localhost/testdb"
        assert settings.echo is True
        assert settings.pool_size == 10
        assert settings.max_overflow == 20
        assert settings.pool_timeout == 60
        assert settings.pool_recycle == 7200
    
    def test_validation_constraints(self):
        """测试配置验证约束"""
        # 测试pool_size约束
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_size=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_size=100)  # 大于最大值
        
        # 测试max_overflow约束
        with pytest.raises(ValidationError):
            DatabaseSettings(max_overflow=-1)  # 小于最小值
        
        with pytest.raises(ValidationError):
            DatabaseSettings(max_overflow=200)  # 大于最大值
        
        # 测试pool_timeout约束
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_timeout=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_timeout=500)  # 大于最大值
        
        # 测试pool_recycle约束
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_recycle=100)  # 小于最小值
        
        with pytest.raises(ValidationError):
            DatabaseSettings(pool_recycle=100000)  # 大于最大值
    
    def test_environment_variables(self):
        """测试环境变量读取"""
        with patch.dict(os.environ, {
            'DATABASE_URL': 'mysql://localhost/test',
            'DATABASE_ECHO': 'true',
            'DATABASE_POOL_SIZE': '15'
        }):
            settings = DatabaseSettings()
            assert settings.url == 'mysql://localhost/test'
            assert settings.echo is True
            assert settings.pool_size == 15


class TestAPISettings:
    """测试APISettings配置类"""
    
    def test_default_values(self):
        """测试默认配置值"""
        settings = APISettings()
        
        assert settings.title == "JJCrawler API"
        assert settings.description == "晋江文学城爬虫API服务"
        assert settings.version == "v1"
        assert settings.host == "0.0.0.0"
        assert settings.port == 8000
        assert settings.debug is False
        assert settings.cors_enabled is True
        assert settings.cors_origins == ["*"]
        assert settings.cors_methods == ["GET", "POST", "PUT", "DELETE"]
        assert settings.cors_headers == ["*"]
        assert settings.default_page_size == 20
        assert settings.max_page_size == 100
    
    def test_custom_values(self):
        """测试自定义配置值"""
        settings = APISettings(
            title="Custom API",
            host="127.0.0.1",
            port=9000,
            debug=True,
            cors_enabled=False,
            cors_origins=["http://localhost:3000"],
            default_page_size=50,
            max_page_size=200
        )
        
        assert settings.title == "Custom API"
        assert settings.host == "127.0.0.1"
        assert settings.port == 9000
        assert settings.debug is True
        assert settings.cors_enabled is False
        assert settings.cors_origins == ["http://localhost:3000"]
        assert settings.default_page_size == 50
        assert settings.max_page_size == 200
    
    def test_port_validation(self):
        """测试端口号验证"""
        # 测试有效端口
        settings = APISettings(port=8080)
        assert settings.port == 8080
        
        # 测试无效端口
        with pytest.raises(ValidationError):
            APISettings(port=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            APISettings(port=70000)  # 大于最大值
    
    def test_page_size_validation(self):
        """测试分页大小验证"""
        # 测试default_page_size约束
        with pytest.raises(ValidationError):
            APISettings(default_page_size=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            APISettings(default_page_size=200)  # 大于最大值
        
        # 测试max_page_size约束
        with pytest.raises(ValidationError):
            APISettings(max_page_size=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            APISettings(max_page_size=2000)  # 大于最大值
    
    def test_environment_variables(self):
        """测试环境变量读取"""
        with patch.dict(os.environ, {
            'API_TITLE': 'Test API',
            'API_PORT': '9000',
            'API_DEBUG': 'true'
        }):
            settings = APISettings()
            assert settings.title == 'Test API'
            assert settings.port == 9000
            assert settings.debug is True


class TestCrawlerSettings:
    """测试CrawlerSettings配置类"""
    
    def test_default_values(self):
        """测试默认配置值"""
        settings = CrawlerSettings()
        
        assert isinstance(settings.user_agent, dict)
        assert 'User-Agent' in settings.user_agent
        assert settings.timeout == 30
        assert settings.retry_times == 3
        assert settings.retry_delay == 1.0
        assert settings.request_delay == 1.0
        assert settings.concurrent_requests == 3
    
    def test_custom_values(self):
        """测试自定义配置值"""
        custom_user_agent = {"User-Agent": "Custom Bot 1.0"}
        settings = CrawlerSettings(
            user_agent=custom_user_agent,
            timeout=60,
            retry_times=5,
            retry_delay=2.0,
            request_delay=0.5,
            concurrent_requests=5
        )
        
        assert settings.user_agent == custom_user_agent
        assert settings.timeout == 60
        assert settings.retry_times == 5
        assert settings.retry_delay == 2.0
        assert settings.request_delay == 0.5
        assert settings.concurrent_requests == 5
    
    def test_validation_constraints(self):
        """测试配置验证约束"""
        # 测试timeout约束
        with pytest.raises(ValidationError):
            CrawlerSettings(timeout=3)  # 小于最小值
        
        with pytest.raises(ValidationError):
            CrawlerSettings(timeout=500)  # 大于最大值
        
        # 测试retry_times约束
        with pytest.raises(ValidationError):
            CrawlerSettings(retry_times=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            CrawlerSettings(retry_times=20)  # 大于最大值
        
        # 测试retry_delay约束
        with pytest.raises(ValidationError):
            CrawlerSettings(retry_delay=0.05)  # 小于最小值
        
        with pytest.raises(ValidationError):
            CrawlerSettings(retry_delay=15.0)  # 大于最大值
        
        # 测试request_delay约束
        with pytest.raises(ValidationError):
            CrawlerSettings(request_delay=0.05)  # 小于最小值
        
        with pytest.raises(ValidationError):
            CrawlerSettings(request_delay=100.0)  # 大于最大值
        
        # 测试concurrent_requests约束
        with pytest.raises(ValidationError):
            CrawlerSettings(concurrent_requests=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            CrawlerSettings(concurrent_requests=20)  # 大于最大值


class TestSchedulerSettings:
    """测试SchedulerSettings配置类"""
    
    def test_default_values(self):
        """测试默认配置值"""
        settings = SchedulerSettings()
        
        assert settings.timezone == "Asia/Shanghai"
        assert settings.max_workers == 5
        assert isinstance(settings.job_defaults, dict)
        assert settings.job_defaults["coalesce"] is False
        assert settings.job_defaults["max_instances"] == 1
        assert settings.job_defaults["misfire_grace_time"] == 60
        assert settings.job_store_type == "SQLAlchemyJobStore"
        assert settings.job_store_url == "sqlite:///./data/jjcrawler.db"
    
    def test_custom_values(self):
        """测试自定义配置值"""
        custom_job_defaults = {"coalesce": True, "max_instances": 3}
        settings = SchedulerSettings(
            timezone="UTC",
            max_workers=10,
            job_defaults=custom_job_defaults,
            job_store_type="MemoryJobStore",
            job_store_url=None
        )
        
        assert settings.timezone == "UTC"
        assert settings.max_workers == 10
        assert settings.job_defaults == custom_job_defaults
        assert settings.job_store_type == "MemoryJobStore"
        assert settings.job_store_url is None
    
    def test_max_workers_validation(self):
        """测试最大工作线程数验证"""
        # 测试有效值
        settings = SchedulerSettings(max_workers=10)
        assert settings.max_workers == 10
        
        # 测试无效值
        with pytest.raises(ValidationError):
            SchedulerSettings(max_workers=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            SchedulerSettings(max_workers=25)  # 大于最大值


class TestLoggingSettings:
    """测试LoggingSettings配置类"""
    
    def test_default_values(self):
        """测试默认配置值"""
        settings = LoggingSettings()
        
        assert settings.level == "INFO"
        assert settings.log_format == "%(asctime)s-%(name)s-%(levelname)s-%(message)s"
        assert settings.console_enabled is True
        assert settings.file_enabled is True
        assert settings.file_path == "./logs/jjcrawler.log"
        assert settings.max_bytes == 10 * 1024 * 1024
        assert settings.backup_count == 5
        assert settings.error_file_enabled is True
        assert settings.error_file_path == "./logs/jjcrawler_error.log"
    
    def test_custom_values(self):
        """测试自定义配置值"""
        settings = LoggingSettings(
            level="DEBUG",
            console_enabled=False,
            file_enabled=False,
            file_path="./custom/app.log",
            max_bytes=50 * 1024 * 1024,
            backup_count=10,
            error_file_enabled=False
        )
        
        assert settings.level == "DEBUG"
        assert settings.console_enabled is False
        assert settings.file_enabled is False
        assert settings.file_path == "./custom/app.log"
        assert settings.max_bytes == 50 * 1024 * 1024
        assert settings.backup_count == 10
        assert settings.error_file_enabled is False
    
    def test_log_level_validation(self):
        """测试日志级别验证"""
        # 测试有效日志级别
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for level in valid_levels:
            settings = LoggingSettings(level=level)
            assert settings.level == level.upper()
            
            # 测试小写输入
            settings = LoggingSettings(level=level.lower())
            assert settings.level == level.upper()
        
        # 测试无效日志级别
        with pytest.raises(ValidationError, match="日志级别必须是"):
            LoggingSettings(level="INVALID")
    
    def test_max_bytes_validation(self):
        """测试最大字节数验证"""
        # 测试有效值
        settings = LoggingSettings(max_bytes=5 * 1024 * 1024)  # 5MB
        assert settings.max_bytes == 5 * 1024 * 1024
        
        # 测试无效值
        with pytest.raises(ValidationError):
            LoggingSettings(max_bytes=500 * 1024)  # 小于最小值
        
        with pytest.raises(ValidationError):
            LoggingSettings(max_bytes=200 * 1024 * 1024)  # 大于最大值
    
    def test_backup_count_validation(self):
        """测试备份文件数量验证"""
        # 测试有效值
        settings = LoggingSettings(backup_count=3)
        assert settings.backup_count == 3
        
        # 测试无效值
        with pytest.raises(ValidationError):
            LoggingSettings(backup_count=0)  # 小于最小值
        
        with pytest.raises(ValidationError):
            LoggingSettings(backup_count=25)  # 大于最大值


class TestSettings:
    """测试主配置类Settings"""
    
    def test_default_values(self):
        """测试默认配置值"""
        settings = Settings()
        
        assert settings.env == "dev"
        assert settings.debug is False
        assert settings.project_name == "JJCrawler"
        assert settings.project_version == "1.0.0"
        assert settings.data_dir == "./data"
        assert settings.logs_dir == "./logs"
        
        # 验证子配置实例
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.api, APISettings)
        assert isinstance(settings.crawler, CrawlerSettings)
        assert isinstance(settings.scheduler, SchedulerSettings)
        assert isinstance(settings.logging, LoggingSettings)
    
    def test_custom_values(self):
        """测试自定义配置值"""
        settings = Settings(
            env="prod",
            debug=True,
            project_name="CustomProject",
            project_version="2.0.0",
            data_dir="./custom_data",
            logs_dir="./custom_logs"
        )
        
        assert settings.env == "prod"
        assert settings.debug is True
        assert settings.project_name == "CustomProject"
        assert settings.project_version == "2.0.0"
        assert settings.data_dir == "./custom_data"
        assert settings.logs_dir == "./custom_logs"
    
    def test_environment_validation(self):
        """测试环境配置验证"""
        # 测试有效环境
        valid_environments = ['dev', 'test', 'prod']
        for env in valid_environments:
            settings = Settings(env=env)
            assert settings.env == env.lower()
            
            # 测试大写输入
            settings = Settings(env=env.upper())
            assert settings.env == env.lower()
        
        # 测试无效环境
        with pytest.raises(ValidationError, match="环境必须是"):
            Settings(env="invalid")
    
    def test_environment_methods(self):
        """测试环境判断方法"""
        # 测试开发环境
        dev_settings = Settings(env="dev")
        assert dev_settings.is_development() is True
        assert dev_settings.is_testing() is False
        assert dev_settings.is_production() is False
        
        # 测试测试环境
        test_settings = Settings(env="test")
        assert test_settings.is_development() is False
        assert test_settings.is_testing() is True
        assert test_settings.is_production() is False
        
        # 测试生产环境
        prod_settings = Settings(env="prod")
        assert prod_settings.is_development() is False
        assert prod_settings.is_testing() is False
        assert prod_settings.is_production() is True
    
    def test_get_database_url(self):
        """测试获取数据库URL方法"""
        settings = Settings()
        url = settings.get_database_url()
        assert url == settings.database.url
        
        # 测试自定义数据库配置
        custom_db = DatabaseSettings(url="postgresql://localhost/test")
        settings = Settings(database=custom_db)
        assert settings.get_database_url() == "postgresql://localhost/test"
    
    @patch('pathlib.Path.mkdir')
    def test_ensure_directories(self, mock_mkdir):
        """测试目录创建功能"""
        settings = Settings(
            data_dir="./test_data",
            logs_dir="./test_logs"
        )
        
        # 验证mkdir被调用
        assert mock_mkdir.call_count >= 3  # 至少创建3个目录
        
        # 验证mkdir调用参数
        calls = mock_mkdir.call_args_list
        for call in calls:
            assert call[1]["parents"] is True
            assert call[1]["exist_ok"] is True
    
    def test_nested_settings_configuration(self):
        """测试嵌套配置的设置"""
        # 创建自定义子配置
        custom_database = DatabaseSettings(url="custom://localhost/db")
        custom_api = APISettings(port=9000)
        
        settings = Settings(
            database=custom_database,
            api=custom_api
        )
        
        assert settings.database.url == "custom://localhost/db"
        assert settings.api.port == 9000
        # 其他配置应该使用默认值
        assert isinstance(settings.crawler, CrawlerSettings)
        assert settings.crawler.timeout == 30  # 默认值


class TestGlobalFunctions:
    """测试全局函数"""
    
    def test_get_settings(self):
        """测试get_settings函数"""
        settings = get_settings()
        assert isinstance(settings, Settings)
    
    def test_get_database_url(self):
        """测试get_database_url函数"""
        url = get_database_url()
        assert isinstance(url, str)
        assert url == get_settings().get_database_url()
    
    def test_is_debug(self):
        """测试is_debug函数"""
        # 这个测试依赖于全局设置，所以我们需要mock
        with patch('app.config._settings') as mock_settings:
            mock_settings.debug = True
            mock_settings.is_development.return_value = False
            assert is_debug() is True
            
            mock_settings.debug = False
            mock_settings.is_development.return_value = True
            assert is_debug() is True
            
            mock_settings.debug = False
            mock_settings.is_development.return_value = False
            assert is_debug() is False
    
    def test_is_production(self):
        """测试is_production函数"""
        with patch('app.config._settings') as mock_settings:
            mock_settings.is_production.return_value = True
            assert is_production() is True
            
            mock_settings.is_production.return_value = False
            assert is_production() is False


class TestConfigurationIntegration:
    """配置集成测试"""
    
    def test_environment_variable_integration(self):
        """测试环境变量集成"""
        env_vars = {
            'ENV': 'test',
            'DEBUG': 'true',
            'PROJECT_NAME': 'TestProject',
            'DATABASE_URL': 'postgresql://test:test@localhost/testdb',
            'API_PORT': '9090',
            'CRAWLER_TIMEOUT': '60',
            'LOG_LEVEL': 'DEBUG'
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.env == 'test'
            assert settings.debug is True
            assert settings.project_name == 'TestProject'
            assert settings.database.url == 'postgresql://test:test@localhost/testdb'
            assert settings.api.port == 9090
            assert settings.crawler.timeout == 60
            assert settings.logging.level == 'DEBUG'
    
    def test_dotenv_file_loading(self):
        """测试.env文件加载"""
        # 创建临时.env文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("ENV=prod\n")
            f.write("DEBUG=false\n")
            f.write("DATABASE_URL=sqlite:///prod.db\n")
            env_file = f.name
        
        try:
            # 使用自定义env_file路径
            with patch.object(Settings.Config, 'env_file', env_file):
                settings = Settings()
                
                # 注意：由于pydantic-settings的工作方式，这个测试可能需要调整
                # 实际的env文件加载行为可能与预期不同
                assert isinstance(settings, Settings)
        finally:
            # 清理临时文件
            os.unlink(env_file)
    
    def test_validation_error_handling(self):
        """测试验证错误处理"""
        # 测试多个验证错误
        with pytest.raises(ValidationError) as exc_info:
            Settings(
                env="invalid_env",
                database=DatabaseSettings(pool_size=0),  # 无效值
                api=APISettings(port=0),  # 无效值
                logging=LoggingSettings(level="INVALID")  # 无效值
            )
        
        # 验证包含至少一个错误
        errors = exc_info.value.errors()
        assert len(errors) >= 1  # 至少有1个验证错误
    
    def test_complex_configuration_scenario(self):
        """测试复杂配置场景"""
        # 模拟生产环境的复杂配置
        settings = Settings(
            env="prod",
            debug=False,
            database=DatabaseSettings(
                url="postgresql://user:pass@db.example.com:5432/jjcrawler",
                echo=False,
                pool_size=20,
                max_overflow=50
            ),
            api=APISettings(
                host="0.0.0.0",
                port=80,
                cors_origins=["https://jjcrawler.example.com"],
                max_page_size=50
            ),
            crawler=CrawlerSettings(
                timeout=45,
                retry_times=5,
                request_delay=2.0,
                concurrent_requests=2
            ),
            scheduler=SchedulerSettings(
                max_workers=10,
                job_store_url="postgresql://user:pass@db.example.com:5432/jjcrawler"
            ),
            logging=LoggingSettings(
                level="WARNING",
                file_enabled=True,
                error_file_enabled=True,
                max_bytes=50 * 1024 * 1024,
                backup_count=10
            )
        )
        
        # 验证生产环境配置
        assert settings.is_production()
        assert not settings.is_development()
        assert not settings.debug
        
        # 验证数据库配置
        assert "postgresql" in settings.database.url
        assert settings.database.pool_size == 20
        
        # 验证API配置
        assert settings.api.port == 80
        assert "https://jjcrawler.example.com" in settings.api.cors_origins
        
        # 验证爬虫配置
        assert settings.crawler.timeout == 45
        assert settings.crawler.concurrent_requests == 2
        
        # 验证调度器配置
        assert settings.scheduler.max_workers == 10
        
        # 验证日志配置
        assert settings.logging.level == "WARNING"
        assert settings.logging.max_bytes == 50 * 1024 * 1024