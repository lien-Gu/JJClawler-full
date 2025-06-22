"""
基础模型定义

包含枚举类型和共用的基础定义
"""
from enum import Enum


class UpdateFrequency(str, Enum):
    """更新频率枚举"""
    HOURLY = "hourly"
    DAILY = "daily"