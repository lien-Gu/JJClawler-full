"""
日志工具

提供统一的日志配置、格式化和输出管理
"""

import logging
import logging.config
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    log_format: Optional[str] = None,
    date_format: Optional[str] = None,
) -> None:
    """
    设置日志配置

    Args:
        level: 日志级别
        log_file: 日志文件路径
        log_format: 日志格式
        date_format: 时间格式
    """
    # 默认日志格式
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 默认时间格式
    if date_format is None:
        date_format = "%Y-%m-%d %H:%M:%S"

    # 日志配置
    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": log_format,
                "datefmt": date_format,
            },
        },
        "handlers": {
            "console": {
                "level": level,
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
    }

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        config["handlers"]["file"] = {
            "level": level,
            "class": "logging.handlers.RotatingFileHandler",
            "filename": log_file,
            "maxBytes": 10 * 1024 * 1024,  # 10MB
            "backupCount": 5,
            "formatter": "default",
            "encoding": "utf-8",
        }
        config["root"]["handlers"].append("file")

    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    """
    获取指定名称的日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name)


def log_function_call(logger: logging.Logger, func_name: str, *args, **kwargs):
    """
    记录函数调用日志

    Args:
        logger: 日志记录器
        func_name: 函数名
        *args: 位置参数
        **kwargs: 关键字参数
    """
    args_str = ", ".join(str(arg) for arg in args)
    kwargs_str = ", ".join(f"{k}={v}" for k, v in kwargs.items())

    params = []
    if args_str:
        params.append(args_str)
    if kwargs_str:
        params.append(kwargs_str)

    params_str = ", ".join(params)
    logger.debug(f"调用函数: {func_name}({params_str})")


def log_execution_time(
    logger: logging.Logger, func_name: str, start_time: datetime, end_time: datetime
):
    """
    记录函数执行时间

    Args:
        logger: 日志记录器
        func_name: 函数名
        start_time: 开始时间
        end_time: 结束时间
    """
    duration = (end_time - start_time).total_seconds()
    logger.info(f"函数 {func_name} 执行完成，耗时: {duration:.3f}秒")


def log_error_with_context(
    logger: logging.Logger, error: Exception, context: Optional[Dict[str, Any]] = None
):
    """
    记录带上下文的错误日志

    Args:
        logger: 日志记录器
        error: 异常对象
        context: 上下文信息
    """
    error_msg = f"错误: {type(error).__name__}: {str(error)}"

    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        error_msg += f" | 上下文: {context_str}"

    logger.error(error_msg, exc_info=True)


class LoggingMixin:
    """
    日志混入类

    为类提供便捷的日志功能
    """

    @property
    def logger(self) -> logging.Logger:
        """获取当前类的日志记录器"""
        return get_logger(self.__class__.__name__)

    def log_info(self, message: str, *args, **kwargs):
        """记录信息日志"""
        self.logger.info(message, *args, **kwargs)

    def log_debug(self, message: str, *args, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, *args, **kwargs)

    def log_warning(self, message: str, *args, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, *args, **kwargs)

    def log_error(self, message: str, *args, **kwargs):
        """记录错误日志"""
        self.logger.error(message, *args, **kwargs)

    def log_exception(self, message: str, *args, **kwargs):
        """记录异常日志"""
        self.logger.exception(message, *args, **kwargs)


def function_logger(func_name: Optional[str] = None):
    """
    函数日志装饰器

    Args:
        func_name: 自定义函数名，默认使用实际函数名
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            logger = get_logger(func.__module__)

            # 记录函数调用
            log_function_call(logger, name, *args, **kwargs)

            start_time = datetime.now()
            try:
                result = func(*args, **kwargs)
                end_time = datetime.now()

                # 记录执行时间
                log_execution_time(logger, name, start_time, end_time)

                return result

            except Exception as e:
                end_time = datetime.now()

                # 记录错误和执行时间
                log_error_with_context(
                    logger,
                    e,
                    {
                        "function": name,
                        "duration": f"{(end_time - start_time).total_seconds():.3f}s",
                    },
                )
                raise

        return wrapper

    return decorator


def async_function_logger(func_name: Optional[str] = None):
    """
    异步函数日志装饰器

    Args:
        func_name: 自定义函数名，默认使用实际函数名
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            logger = get_logger(func.__module__)

            # 记录函数调用
            log_function_call(logger, name, *args, **kwargs)

            start_time = datetime.now()
            try:
                result = await func(*args, **kwargs)
                end_time = datetime.now()

                # 记录执行时间
                log_execution_time(logger, name, start_time, end_time)

                return result

            except Exception as e:
                end_time = datetime.now()

                # 记录错误和执行时间
                log_error_with_context(
                    logger,
                    e,
                    {
                        "function": name,
                        "duration": f"{(end_time - start_time).total_seconds():.3f}s",
                    },
                )
                raise

        return wrapper

    return decorator
