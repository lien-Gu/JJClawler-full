"""
统一日志配置模块
基于config.py中的LoggingSettings配置，为整个项目提供标准化的日志功能
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional

from .config import get_settings


class LoggerSetup:
    """日志配置管理器"""
    
    _initialized = False
    _loggers = {}
    
    @classmethod
    def setup_logging(cls) -> None:
        """初始化项目的日志配置"""
        if cls._initialized:
            return
            
        settings = get_settings()
        log_config = settings.logging
        
        # 确保日志目录存在
        log_file_path = Path(log_config.file_path)
        error_file_path = Path(log_config.error_file_path)
        
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        error_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 设置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_config.level))
        
        # 清除已有的处理器
        root_logger.handlers.clear()
        
        # 禁用httpx的INFO级别日志，只保留WARNING及以上
        logging.getLogger("httpx").setLevel(logging.WARNING)
        
        # 创建格式化器
        formatter = logging.Formatter(
            fmt=log_config.log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        if log_config.console_enabled:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, log_config.level))
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 文件处理器（所有日志）
        if log_config.file_enabled:
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_config.file_path,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=log_config.backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, log_config.level))
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        # 错误日志文件处理器
        if log_config.error_file_enabled:
            error_handler = logging.handlers.RotatingFileHandler(
                filename=log_config.error_file_path,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=log_config.backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """获取指定名称的日志器"""
        if not cls._initialized:
            cls.setup_logging()
        
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称，通常使用 __name__
        
    Returns:
        配置好的日志器实例
        
    Example:
        >>> from app.logger import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("这是一条信息日志")
    """
    if name is None:
        name = 'jjcrawler'
    
    return LoggerSetup.get_logger(name)


def setup_logging():
    """初始化日志系统的便捷函数"""
    LoggerSetup.setup_logging()


# 自动初始化日志系统
setup_logging()