"""
配置模块测试的Conftest文件 - MVP实现
提供基础的fixture和mock数据
"""
import pytest
import os
from typing import Dict, Any, List
from pathlib import Path


# ==========================================
# 核心测试数据 - MVP基础数据
# ==========================================

@pytest.fixture
def sample_env_vars():
    """测试用环境变量数据"""
    return {
        'ENV': 'test',
        'DEBUG': 'true',
        'API_PORT': '9000',
        'DATABASE_URL': 'sqlite:///test.db'
    }


@pytest.fixture
def case_sensitive_env_vars():
    """大小写敏感测试环境变量"""
    return {'env': 'TEST'}


@pytest.fixture
def valid_config_params():
    """有效配置参数"""
    return {
        "env": "dev",
        "debug": False,
        "project_name": "TestApp"
    }


@pytest.fixture
def invalid_env_values():
    """无效环境值列表"""
    return ["invalid", "INVALID", "production", "development"]


@pytest.fixture
def valid_log_levels():
    """有效日志级别列表"""
    return ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


@pytest.fixture
def invalid_log_levels():
    """无效日志级别列表"""
    return ["INVALID", "TRACE", "VERBOSE", "NONE"]


# ==========================================
# 配置约束测试数据 - MVP验证数据
# ==========================================

@pytest.fixture
def database_constraints():
    """数据库配置约束边界值"""
    return {
        "pool_size": {"min": 1, "max": 50},
        "max_overflow": {"min": 0, "max": 100},
        "pool_timeout": {"min": 1, "max": 300},
        "pool_recycle": {"min": 300, "max": 86400}
    }


@pytest.fixture
def api_constraints():
    """API配置约束边界值"""
    return {
        "port": {"min": 1, "max": 65535},
        "default_page_size": {"min": 1, "max": 100},
        "max_page_size": {"min": 1, "max": 1000}
    }


@pytest.fixture
def crawler_constraints():
    """爬虫配置约束边界值"""
    return {
        "timeout": {"min": 5, "max": 300},
        "retry_times": {"min": 1, "max": 10},
        "retry_delay": {"min": 0.1, "max": 10.0},
        "request_delay": {"min": 0.1, "max": 60.0},
        "concurrent_requests": {"min": 1, "max": 10}
    }


@pytest.fixture
def scheduler_constraints():
    """调度器配置约束边界值"""
    return {
        "max_workers": {"min": 1, "max": 20}
    }


@pytest.fixture
def logging_constraints():
    """日志配置约束边界值"""
    return {
        "max_bytes": {"min": 1024 * 1024, "max": 100 * 1024 * 1024},
        "backup_count": {"min": 1, "max": 20}
    }


# ==========================================
# 默认配置期望值 - MVP验证基准
# ==========================================

@pytest.fixture
def expected_defaults():
    """期望的默认配置值"""
    return {
        "env": "dev",
        "project_name": "JJCrawler",
        "project_version": "1.0.0",
        "debug": False,
        "api_version": "v1",
        "api_host": "0.0.0.0",
        "scheduler_timezone": "Asia/Shanghai",
        "scheduler_job_store_type": "SQLAlchemyJobStore"
    }


@pytest.fixture
def expected_file_extensions():
    """期望的文件扩展名"""
    return {
        "log_files": ".log",
        "database_files": ".db"
    }


@pytest.fixture
def expected_collections():
    """期望的集合类型数据"""
    return {
        "cors_methods": ["GET", "POST"],
        "job_defaults_keys": ["coalesce", "max_instances", "misfire_grace_time"]
    }


# ==========================================
# Mock辅助Fixtures - MVP工具函数
# ==========================================

@pytest.fixture
def mock_env_override(mocker):
    """环境变量覆盖mock工厂函数"""
    def _mock_env(env_vars: Dict[str, str]):
        return mocker.patch.dict(os.environ, env_vars)
    return _mock_env


@pytest.fixture
def temp_directory():
    """临时目录fixture"""
    import tempfile
    import shutil
    
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    
    # 清理
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.fixture
def config_factory():
    """配置对象工厂函数"""
    def _create_config(**kwargs):
        from app.config import Settings
        return Settings(**kwargs)
    return _create_config


# ==========================================
# 专用组合Fixtures - MVP常用场景
# ==========================================

@pytest.fixture
def dev_environment_setup(mock_env_override):
    """开发环境设置"""
    return mock_env_override({
        'ENV': 'dev',
        'DEBUG': 'true'
    })


@pytest.fixture
def test_environment_setup(mock_env_override):
    """测试环境设置"""
    return mock_env_override({
        'ENV': 'test',
        'DEBUG': 'false',
        'DATABASE_URL': 'sqlite:///:memory:'
    })


@pytest.fixture
def prod_environment_setup(mock_env_override):
    """生产环境设置"""
    return mock_env_override({
        'ENV': 'prod',
        'DEBUG': 'false',
        'LOG_LEVEL': 'WARNING'
    })


# ==========================================
# 配置验证辅助函数 - MVP验证工具
# ==========================================

@pytest.fixture
def constraint_validator():
    """约束验证辅助函数"""
    def _validate_constraint(value, constraint_dict):
        """验证值是否在约束范围内"""
        return constraint_dict["min"] <= value <= constraint_dict["max"]
    return _validate_constraint


@pytest.fixture
def collection_validator():
    """集合类型验证辅助函数"""
    def _validate_collection(collection, expected_items):
        """验证集合是否包含期望的项目"""
        return all(item in collection for item in expected_items)
    return _validate_collection


@pytest.fixture
def file_extension_validator():
    """文件扩展名验证辅助函数"""
    def _validate_extension(file_path, expected_extension):
        """验证文件路径是否有期望的扩展名"""
        return str(file_path).endswith(expected_extension)
    return _validate_extension 