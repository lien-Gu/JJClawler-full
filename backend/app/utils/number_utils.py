"""
数字处理工具

统一的数字解析和处理功能
"""

import re
from typing import Any, Optional, Union


def parse_number(data: Any, default: Optional[int] = None) -> Optional[int]:
    """
    统一的数字解析函数

    支持的格式：
    - 纯数字：123, "456", 1.23
    - 带单位：1.2万, 3千, "5.6万"
    - 带逗号：1,234, "1,234,567"

    Args:
        data: 要解析的数据
        default: 默认值，None表示返回None

    Returns:
        Optional[int]: 解析后的数字，失败时返回default
    """
    if data is None:
        return default

    # 转换为字符串并清理
    text = str(data).strip()
    if not text:
        return default

    try:
        # 移除常见的无用字符
        text = text.replace(",", "").replace("，", "").replace(" ", "")

        # 尝试直接转换为数字
        if text.replace(".", "").isdigit():
            return int(float(text))

        # 处理带单位的数字
        if "万" in text:
            num_part = re.findall(r"[\d.]+", text.replace("万", ""))
            if num_part:
                return int(float(num_part[0]) * 10000)

        if "千" in text:
            num_part = re.findall(r"[\d.]+", text.replace("千", ""))
            if num_part:
                return int(float(num_part[0]) * 1000)

        # 使用正则表达式提取数字
        numbers = re.findall(r"\d+\.?\d*", text)
        if numbers:
            return int(float(numbers[0]))

        return default

    except (ValueError, TypeError, IndexError):
        return default


def format_number(num: Union[int, float, None], unit: str = "") -> str:
    """
    格式化数字显示

    Args:
        num: 要格式化的数字
        unit: 单位后缀

    Returns:
        str: 格式化后的字符串
    """
    if num is None:
        return "-"

    try:
        num = float(num)
        if num >= 10000:
            return f"{num/10000:.1f}万{unit}"
        elif num >= 1000:
            return f"{num/1000:.1f}千{unit}"
        else:
            return f"{int(num)}{unit}"
    except (ValueError, TypeError):
        return str(num) + unit


def is_valid_number(data: Any) -> bool:
    """
    检查数据是否为有效数字

    Args:
        data: 要检查的数据

    Returns:
        bool: 是否为有效数字
    """
    return parse_number(data) is not None
