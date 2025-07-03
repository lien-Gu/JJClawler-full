"""
文件操作工具

提供JSON文件读写、目录操作、配置管理等文件相关的工具函数
"""

import json
import os
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    确保目录存在，如果不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path: 目录路径对象
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    logger.debug(f"目录已确保存在: {path_obj}")
    return path_obj


def read_json_file(file_path: Union[str, Path], default: Any = None) -> Any:
    """
    读取JSON文件

    Args:
        file_path: 文件路径
        default: 文件不存在或读取失败时的默认值
    Returns:
        Any: JSON数据
    """
    file_path = Path(file_path)

    try:
        if not file_path.exists():
            logger.warning(f"JSON文件不存在: {file_path}")
            return default

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            logger.debug(f"JSON文件读取成功: {file_path}")
            return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON文件格式错误: {file_path} - {e}")
        return default
    except Exception as e:
        logger.error(f"JSON文件读取失败: {file_path} - {e}")
        return default


def write_json_file(
    file_path: Union[str, Path],
    data: Any,
    ensure_dir: bool = True,
    indent: int = 2,
    backup: bool = False,
) -> bool:
    """
    写入JSON文件

    Args:
        file_path: 文件路径
        data: 要写入的数据
        ensure_dir: 是否确保目录存在
        indent: JSON缩进
        backup: 是否创建备份

    Returns:
        bool: 是否写入成功
    """
    file_path = Path(file_path)

    try:
        # 确保目录存在
        if ensure_dir:
            ensure_directory(file_path.parent)

        # 创建备份
        if backup and file_path.exists():
            backup_path = file_path.with_suffix(
                f'.{datetime.now().strftime("%Y%m%d_%H%M%S")}.bak'
            )
            file_path.replace(backup_path)
            logger.info(f"已创建备份: {backup_path}")

        # 写入JSON文件
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)

        logger.debug(f"JSON文件写入成功: {file_path}")
        return True

    except Exception as e:
        logger.error(f"JSON文件写入失败: {file_path} - {e}")
        return False


def read_text_file(
    file_path: Union[str, Path], encoding: str = "utf-8"
) -> Optional[str]:
    """
    读取文本文件

    Args:
        file_path: 文件路径
        encoding: 文件编码

    Returns:
        Optional[str]: 文件内容，失败时返回None
    """
    file_path = Path(file_path)

    try:
        if not file_path.exists():
            logger.warning(f"文本文件不存在: {file_path}")
            return None

        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()
            logger.debug(f"文本文件读取成功: {file_path}")
            return content

    except Exception as e:
        logger.error(f"文本文件读取失败: {file_path} - {e}")
        return None


def write_text_file(
    file_path: Union[str, Path],
    content: str,
    encoding: str = "utf-8",
    ensure_dir: bool = True,
) -> bool:
    """
    写入文本文件

    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        ensure_dir: 是否确保目录存在

    Returns:
        bool: 是否写入成功
    """
    file_path = Path(file_path)

    try:
        # 确保目录存在
        if ensure_dir:
            ensure_directory(file_path.parent)

        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)

        logger.debug(f"文本文件写入成功: {file_path}")
        return True

    except Exception as e:
        logger.error(f"文本文件写入失败: {file_path} - {e}")
        return False


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        int: 文件大小，文件不存在时返回0
    """
    file_path = Path(file_path)
    try:
        return file_path.stat().st_size if file_path.exists() else 0
    except Exception as e:
        logger.error(f"获取文件大小失败: {file_path} - {e}")
        return 0


def list_files(
    directory: Union[str, Path], pattern: str = "*", recursive: bool = False
) -> List[Path]:
    """
    列出目录中的文件

    Args:
        directory: 目录路径
        pattern: 文件模式（如 "*.json"）
        recursive: 是否递归搜索

    Returns:
        List[Path]: 文件路径列表
    """
    directory = Path(directory)

    try:
        if not directory.exists():
            logger.warning(f"目录不存在: {directory}")
            return []

        if recursive:
            files = list(directory.rglob(pattern))
        else:
            files = list(directory.glob(pattern))

        # 只返回文件，不包括目录
        files = [f for f in files if f.is_file()]

        logger.debug(f"找到 {len(files)} 个文件在 {directory}")
        return files

    except Exception as e:
        logger.error(f"列出文件失败: {directory} - {e}")
        return []


def clean_old_files(
    directory: Union[str, Path],
    max_age_days: int,
    pattern: str = "*",
    dry_run: bool = False,
) -> List[Path]:
    """
    清理指定天数前的旧文件

    Args:
        directory: 目录路径
        max_age_days: 最大保留天数
        pattern: 文件模式
        dry_run: 是否只模拟运行（不实际删除）

    Returns:
        List[Path]: 被删除（或将被删除）的文件列表
    """
    directory = Path(directory)
    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)

    deleted_files = []

    try:
        files = list_files(directory, pattern, recursive=True)

        for file_path in files:
            try:
                if file_path.stat().st_mtime < cutoff_time:
                    if not dry_run:
                        file_path.unlink()
                        logger.info(f"已删除旧文件: {file_path}")
                    else:
                        logger.info(f"将删除旧文件: {file_path}")

                    deleted_files.append(file_path)

            except Exception as e:
                logger.error(f"删除文件失败: {file_path} - {e}")

        logger.info(f"清理完成: {len(deleted_files)} 个文件")
        return deleted_files

    except Exception as e:
        logger.error(f"清理旧文件失败: {directory} - {e}")
        return []


def get_project_root() -> Path:
    """
    获取项目根目录

    Returns:
        Path: 项目根目录路径
    """
    # 从当前文件向上查找包含 pyproject.toml 的目录
    current = Path(__file__).parent

    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent

    # 如果没找到，返回当前文件的父目录的父目录
    return Path(__file__).parent.parent.parent


def get_data_dir() -> Path:
    """
    获取数据目录

    Returns:
        Path: 数据目录路径
    """
    return get_project_root() / "data"


def get_config_path(config_name: str) -> Path:
    """
    获取配置文件路径

    Args:
        config_name: 配置文件名

    Returns:
        Path: 配置文件路径
    """
    return get_data_dir() / config_name
