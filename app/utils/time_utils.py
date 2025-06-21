"""
时间处理工具

提供时间格式化、时区转换、时间计算等时间相关的工具函数
"""
import pytz
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import logging

logger = logging.getLogger(__name__)

# 常用时区
UTC = pytz.UTC
CHINA_TZ = pytz.timezone('Asia/Shanghai')


def get_current_time(tz: Optional[pytz.BaseTzInfo] = None) -> datetime:
    """
    获取当前时间
    
    Args:
        tz: 时区，默认为UTC
        
    Returns:
        datetime: 当前时间
    """
    if tz is None:
        tz = UTC
    
    return datetime.now(tz)


def format_datetime(
    dt: datetime, 
    format_str: str = "%Y-%m-%d %H:%M:%S",
    tz: Optional[pytz.BaseTzInfo] = None
) -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        tz: 目标时区
        
    Returns:
        str: 格式化后的时间字符串
    """
    try:
        # 如果指定了时区，转换到目标时区
        if tz is not None:
            if dt.tzinfo is None:
                # 如果datetime没有时区信息，假设它是UTC时间
                dt = UTC.localize(dt)
            dt = dt.astimezone(tz)
        
        return dt.strftime(format_str)
        
    except Exception as e:
        logger.error(f"时间格式化失败: {dt} - {e}")
        return str(dt)


def parse_datetime(
    time_str: str, 
    format_str: str = "%Y-%m-%d %H:%M:%S",
    tz: Optional[pytz.BaseTzInfo] = None
) -> Optional[datetime]:
    """
    解析时间字符串
    
    Args:
        time_str: 时间字符串
        format_str: 格式字符串
        tz: 时区
        
    Returns:
        Optional[datetime]: 解析后的时间对象，失败时返回None
    """
    try:
        dt = datetime.strptime(time_str, format_str)
        
        # 如果指定了时区，添加时区信息
        if tz is not None:
            dt = tz.localize(dt)
        
        return dt
        
    except Exception as e:
        logger.error(f"时间解析失败: {time_str} - {e}")
        return None


def parse_iso_datetime(time_str: str) -> Optional[datetime]:
    """
    解析ISO 8601格式的时间字符串
    
    Args:
        time_str: ISO 8601格式的时间字符串
        
    Returns:
        Optional[datetime]: 解析后的时间对象
    """
    try:
        # 处理不同的ISO格式
        if time_str.endswith('Z'):
            # UTC时间
            dt = datetime.fromisoformat(time_str[:-1])
            return UTC.localize(dt)
        elif '+' in time_str or time_str.count('-') > 2:
            # 带时区信息的时间
            return datetime.fromisoformat(time_str)
        else:
            # 没有时区信息，假设为UTC
            dt = datetime.fromisoformat(time_str)
            return UTC.localize(dt)
            
    except Exception as e:
        logger.error(f"ISO时间解析失败: {time_str} - {e}")
        return None


def to_iso_string(dt: datetime) -> str:
    """
    将datetime转换为ISO 8601字符串
    
    Args:
        dt: 时间对象
        
    Returns:
        str: ISO 8601格式的时间字符串
    """
    try:
        if dt.tzinfo is None:
            # 没有时区信息，假设为UTC
            dt = UTC.localize(dt)
        
        return dt.isoformat()
        
    except Exception as e:
        logger.error(f"ISO时间转换失败: {dt} - {e}")
        return str(dt)


def convert_timezone(
    dt: datetime, 
    target_tz: pytz.BaseTzInfo,
    source_tz: Optional[pytz.BaseTzInfo] = None
) -> datetime:
    """
    时区转换
    
    Args:
        dt: 源时间对象
        target_tz: 目标时区
        source_tz: 源时区（如果dt没有时区信息）
        
    Returns:
        datetime: 转换后的时间对象
    """
    try:
        if dt.tzinfo is None:
            # 如果没有时区信息，使用指定的源时区或UTC
            if source_tz is None:
                source_tz = UTC
            dt = source_tz.localize(dt)
        
        return dt.astimezone(target_tz)
        
    except Exception as e:
        logger.error(f"时区转换失败: {dt} -> {target_tz} - {e}")
        return dt


def add_time(
    dt: datetime, 
    days: int = 0, 
    hours: int = 0, 
    minutes: int = 0, 
    seconds: int = 0
) -> datetime:
    """
    时间加法
    
    Args:
        dt: 基础时间
        days: 增加的天数
        hours: 增加的小时数
        minutes: 增加的分钟数
        seconds: 增加的秒数
        
    Returns:
        datetime: 计算后的时间
    """
    try:
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return dt + delta
        
    except Exception as e:
        logger.error(f"时间加法失败: {dt} + {days}d {hours}h {minutes}m {seconds}s - {e}")
        return dt


def time_diff(dt1: datetime, dt2: datetime) -> timedelta:
    """
    计算时间差
    
    Args:
        dt1: 时间1
        dt2: 时间2
        
    Returns:
        timedelta: 时间差 (dt1 - dt2)
    """
    try:
        return dt1 - dt2
        
    except Exception as e:
        logger.error(f"时间差计算失败: {dt1} - {dt2} - {e}")
        return timedelta(0)


def is_same_day(dt1: datetime, dt2: datetime, tz: Optional[pytz.BaseTzInfo] = None) -> bool:
    """
    判断两个时间是否为同一天
    
    Args:
        dt1: 时间1
        dt2: 时间2
        tz: 比较时使用的时区
        
    Returns:
        bool: 是否为同一天
    """
    try:
        if tz is not None:
            dt1 = convert_timezone(dt1, tz)
            dt2 = convert_timezone(dt2, tz)
        
        return dt1.date() == dt2.date()
        
    except Exception as e:
        logger.error(f"同一天判断失败: {dt1} vs {dt2} - {e}")
        return False


def get_day_start(dt: datetime, tz: Optional[pytz.BaseTzInfo] = None) -> datetime:
    """
    获取指定日期的开始时间（00:00:00）
    
    Args:
        dt: 日期时间
        tz: 时区
        
    Returns:
        datetime: 当天开始时间
    """
    try:
        if tz is not None:
            dt = convert_timezone(dt, tz)
        
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
        
    except Exception as e:
        logger.error(f"获取日期开始时间失败: {dt} - {e}")
        return dt


def get_day_end(dt: datetime, tz: Optional[pytz.BaseTzInfo] = None) -> datetime:
    """
    获取指定日期的结束时间（23:59:59）
    
    Args:
        dt: 日期时间
        tz: 时区
        
    Returns:
        datetime: 当天结束时间
    """
    try:
        if tz is not None:
            dt = convert_timezone(dt, tz)
        
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        
    except Exception as e:
        logger.error(f"获取日期结束时间失败: {dt} - {e}")
        return dt


def format_duration(seconds: Union[int, float]) -> str:
    """
    格式化持续时间
    
    Args:
        seconds: 秒数
        
    Returns:
        str: 格式化的持续时间字符串
    """
    try:
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
        else:
            days = seconds / 86400
            return f"{days:.1f}天"
            
    except Exception as e:
        logger.error(f"持续时间格式化失败: {seconds} - {e}")
        return f"{seconds}秒"


def get_cron_next_run(cron_expr: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
    """
    计算cron表达式的下次执行时间
    
    Args:
        cron_expr: cron表达式
        base_time: 基准时间，默认为当前时间
        
    Returns:
        Optional[datetime]: 下次执行时间
    """
    try:
        from apscheduler.triggers.cron import CronTrigger
        
        if base_time is None:
            base_time = get_current_time()
        
        trigger = CronTrigger.from_crontab(cron_expr, timezone=UTC)
        return trigger.get_next_fire_time(None, base_time)
        
    except Exception as e:
        logger.error(f"cron表达式计算失败: {cron_expr} - {e}")
        return None


# 便捷函数
def now_utc() -> datetime:
    """获取当前UTC时间"""
    return get_current_time(UTC)


def now_china() -> datetime:
    """获取当前中国时间"""
    return get_current_time(CHINA_TZ)


def today_start_utc() -> datetime:
    """获取今天的开始时间（UTC）"""
    return get_day_start(now_utc(), UTC)


def today_start_china() -> datetime:
    """获取今天的开始时间（中国时区）"""
    return get_day_start(now_china(), CHINA_TZ)