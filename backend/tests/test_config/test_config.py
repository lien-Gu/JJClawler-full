"""
配置模块测试
"""
import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict


class TestConfig:
    """配置模块测试类"""
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        from app.config import settings
        
        # 检查默认配置值
        assert settings.APP_NAME == "JJCrawler"
        assert settings.VERSION == "1.0.0"
        assert settings.DEBUG == False
        assert settings.API_V1_STR == "/api/v1"
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
    
    def test_database_config(self):
        """测试数据库配置"""
        from app.config import settings
        
        # 检查数据库配置
        assert settings.DATABASE_URL.startswith("sqlite:///")
        assert settings.DATABASE_POOL_SIZE >= 5
        assert settings.DATABASE_POOL_OVERFLOW >= 10
        assert settings.DATABASE_POOL_TIMEOUT >= 30
    
    def test_scheduler_config(self):
        """测试调度器配置"""
        from app.config import settings
        
        # 检查调度器配置
        assert settings.SCHEDULER_TIMEZONE == "Asia/Shanghai"
        assert settings.SCHEDULER_MAX_WORKERS >= 2
        assert settings.SCHEDULER_COALESCE == True
        assert settings.SCHEDULER_MISFIRE_GRACE_TIME >= 60
    
    def test_crawler_config(self):
        """测试爬虫配置"""
        from app.config import settings
        
        # 检查爬虫配置
        assert settings.CRAWLER_USER_AGENT is not None
        assert settings.CRAWLER_TIMEOUT >= 10
        assert settings.CRAWLER_RETRIES >= 3
        assert settings.CRAWLER_DELAY >= 1
        assert settings.CRAWLER_CONCURRENT_LIMIT >= 5
    
    def test_logging_config(self):
        """测试日志配置"""
        from app.config import settings
        
        # 检查日志配置
        assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert settings.LOG_FORMAT is not None
        assert settings.LOG_FILE_PATH is not None
        assert settings.LOG_MAX_SIZE >= 10
        assert settings.LOG_BACKUP_COUNT >= 5
    
    def test_api_config(self):
        """测试API配置"""
        from app.config import settings
        
        # 检查API配置
        assert settings.API_TITLE is not None
        assert settings.API_DESCRIPTION is not None
        assert settings.API_VERSION is not None
        assert settings.API_RATE_LIMIT >= 100
        assert settings.API_CORS_ORIGINS is not None
    
    @patch.dict(os.environ, {
        'APP_NAME': 'TestApp',
        'DEBUG': 'true',
        'PORT': '9000',
        'DATABASE_URL': 'sqlite:///test.db'
    })
    def test_environment_override(self):
        """测试环境变量覆盖配置"""
        # 重新加载配置以获取环境变量
        from app.config import Settings
        test_settings = Settings()
        
        assert test_settings.APP_NAME == "TestApp"
        assert test_settings.DEBUG == True
        assert test_settings.PORT == 9000
        assert test_settings.DATABASE_URL == "sqlite:///test.db"
    
    def test_config_validation(self):
        """测试配置验证"""
        from app.config import Settings
        
        # 测试有效配置
        valid_config = {
            'APP_NAME': 'TestApp',
            'PORT': 8080,
            'DEBUG': False,
            'DATABASE_URL': 'sqlite:///valid.db'
        }
        
        settings = Settings(**valid_config)
        assert settings.APP_NAME == "TestApp"
        assert settings.PORT == 8080
        assert settings.DEBUG == False
    
    def test_invalid_config_validation(self):
        """测试无效配置验证"""
        from app.config import Settings
        
        # 测试无效端口
        with pytest.raises(ValueError):
            Settings(PORT=-1)
        
        # 测试无效数据库URL
        with pytest.raises(ValueError):
            Settings(DATABASE_URL="invalid-url")
    
    def test_jiazi_config(self):
        """测试夹子榜配置"""
        from app.config import settings
        
        # 检查夹子榜配置
        assert settings.JIAZI_URL is not None
        assert settings.JIAZI_INTERVAL >= 3600  # 至少1小时
        assert settings.JIAZI_PARSER_TYPE == "html"
        assert settings.JIAZI_MAX_PAGES >= 1
    
    def test_category_config(self):
        """测试分类配置"""
        from app.config import settings
        
        # 检查分类配置
        assert settings.CATEGORY_CONFIGS is not None
        assert isinstance(settings.CATEGORY_CONFIGS, dict)
        assert len(settings.CATEGORY_CONFIGS) > 0
    
    def test_file_config(self):
        """测试文件配置"""
        from app.config import settings
        
        # 检查文件配置
        assert settings.DATA_DIR is not None
        assert settings.LOG_DIR is not None
        assert settings.TEMP_DIR is not None
        assert settings.BACKUP_DIR is not None
    
    def test_security_config(self):
        """测试安全配置"""
        from app.config import settings
        
        # 检查安全配置
        assert settings.SECRET_KEY is not None
        assert len(settings.SECRET_KEY) >= 32
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES >= 30
        assert settings.ALGORITHM == "HS256"
    
    def test_config_from_file(self):
        """测试从文件加载配置"""
        # 创建临时配置文件
        config_data = {
            "APP_NAME": "FileTestApp",
            "DEBUG": True,
            "PORT": 7000
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            import json
            json.dump(config_data, f)
            config_file = f.name
        
        try:
            # 测试从文件加载配置
            from app.config import load_config_from_file
            loaded_config = load_config_from_file(config_file)
            
            assert loaded_config["APP_NAME"] == "FileTestApp"
            assert loaded_config["DEBUG"] == True
            assert loaded_config["PORT"] == 7000
        finally:
            os.unlink(config_file)
    
    def test_config_merge(self):
        """测试配置合并"""
        from app.config import merge_configs
        
        base_config = {
            "APP_NAME": "BaseApp",
            "DEBUG": False,
            "PORT": 8000
        }
        
        override_config = {
            "APP_NAME": "OverrideApp",
            "DEBUG": True
        }
        
        merged = merge_configs(base_config, override_config)
        
        assert merged["APP_NAME"] == "OverrideApp"
        assert merged["DEBUG"] == True
        assert merged["PORT"] == 8000
    
    def test_config_export(self):
        """测试配置导出"""
        from app.config import settings
        
        # 导出配置
        exported = settings.dict()
        
        # 检查导出的配置
        assert isinstance(exported, dict)
        assert "APP_NAME" in exported
        assert "DATABASE_URL" in exported
        assert "SECRET_KEY" not in exported  # 敏感信息应被过滤
    
    def test_config_reload(self):
        """测试配置重载"""
        from app.config import reload_config
        
        # 保存原始配置
        original_app_name = os.environ.get('APP_NAME', 'JJCrawler')
        
        try:
            # 修改环境变量
            os.environ['APP_NAME'] = 'ReloadedApp'
            
            # 重载配置
            new_settings = reload_config()
            
            assert new_settings.APP_NAME == 'ReloadedApp'
        finally:
            # 恢复原始配置
            if original_app_name:
                os.environ['APP_NAME'] = original_app_name
            else:
                os.environ.pop('APP_NAME', None)
    
    def test_config_cache(self):
        """测试配置缓存"""
        from app.config import get_cached_config, clear_config_cache
        
        # 获取缓存配置
        config1 = get_cached_config()
        config2 = get_cached_config()
        
        # 应该是同一个实例
        assert config1 is config2
        
        # 清理缓存
        clear_config_cache()
        
        config3 = get_cached_config()
        
        # 应该是新的实例
        assert config1 is not config3
    
    def test_config_validation_errors(self):
        """测试配置验证错误"""
        from app.config import Settings, ValidationError
        
        # 测试各种无效配置
        invalid_configs = [
            {'PORT': 'invalid'},  # 非数字端口
            {'CRAWLER_TIMEOUT': -1},  # 负数超时
            {'LOG_LEVEL': 'INVALID'},  # 无效日志级别
            {'SCHEDULER_MAX_WORKERS': 0},  # 零工作线程
        ]
        
        for invalid_config in invalid_configs:
            with pytest.raises(ValidationError):
                Settings(**invalid_config)
    
    def test_config_type_conversion(self):
        """测试配置类型转换"""
        from app.config import Settings
        
        # 测试字符串到数字的转换
        settings = Settings(
            PORT="8080",
            CRAWLER_TIMEOUT="30",
            DEBUG="true"
        )
        
        assert settings.PORT == 8080
        assert settings.CRAWLER_TIMEOUT == 30
        assert settings.DEBUG == True 