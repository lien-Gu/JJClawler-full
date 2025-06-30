"""
配置管理模块

使用pydantic-settings管理环境变量和应用配置
"""
import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 项目信息
    PROJECT_NAME: str = "JJCrawler"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # API配置
    API_V1_STR: str = "/api/v1"

    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/jjcrawler.db"
    
    # 爬虫配置
    CRAWL_DELAY: float = 1.0
    REQUEST_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 任务调度配置
    SCHEDULER_TIMEZONE: str = "Asia/Shanghai"
    JIAZI_SCHEDULE: str = "0 */1 * * *"  # 每小时执行
    RANKING_SCHEDULE: str = "0 0 * * *"  # 每天执行
    
    # 文件路径配置
    DATA_DIR: str = "./data"
    TASKS_FILE: str = "./data/tasks/tasks.json"
    URLS_CONFIG_FILE: str = "./data/urls.json"
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True
    }


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings


def ensure_directories():
    """确保必要的目录存在"""
    directories = [
        settings.DATA_DIR,
        os.path.dirname(settings.TASKS_FILE),
        f"{settings.DATA_DIR}/tasks/history",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)