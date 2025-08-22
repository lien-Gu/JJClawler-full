import uuid
import hashlib
from datetime import datetime, timedelta
from time import strftime
from typing import Dict, List, Any, Set, Type
import re
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect


def generate_batch_id() -> str:
    """
    生成新的批次ID
    使用时间和UUID4生成唯一的批次标识符
    Returns:
        str: 23位UUID字符串格式的批次ID
    """
    return "{}-{}".format(
        datetime.now().strftime("%Y%m%d%H%M%S"),
        str(uuid.uuid4().hex[:8])
    )


def update_dict(base_d: Dict, new_d: Dict, check_none: bool = True) -> Dict:
    """
    更新字典，使用新的字典来更新原来的字典
    :param base_d:
    :param new_d:
    :param check_none:
    :return:
    """
    if check_none:
        update_info = {key: value for key, value in new_d.items() if value not in [None, ""]}
    else:
        update_info = new_d.copy()
    result = base_d.copy()
    result.update(update_info)
    return result


def extract_number(string: str) -> int:
    """
    将数字从字符串中提取出来
    :param string:
    :return:
    """
    if not string:
        return 0
    digits_str = ''.join(re.findall(r'\d', string))
    number = int(digits_str)
    return number


def filter_dict(raw_dict: dict, valid_field: set | list | Any):
    """
    过滤字典
    :param raw_dict:
    :param valid_field:
    :return:
    """
    if isinstance(valid_field, set) or isinstance(valid_field, list):
        valid_field = set(valid_field)
    else:
        # 如果是SQLAlchemy模型类，获取字段集合
        valid_field = get_model_fields(valid_field)
    return {k: v for k, v in raw_dict.items() if k in valid_field}


def get_model_fields(model_class) -> set[str]:
    """
    获取 SQLAlchemy 模型的所有字段名
    
    :param model_class: SQLAlchemy 模型类
    :return: 字段名集合
    """
    mapper = inspect(model_class)
    return set(mapper.columns.keys())


def delta_to_str(delta: timedelta | int = None) -> str:
    """
    将时间间隔变为字符串
    :param delta:时间间隔、或者秒
    :return:时间字符串
    """
    str_format = "{days}天{hours}小时{minutes}分钟{seconds}秒"
    if not delta:
        return str_format.format(days=0, hours=0, minutes=0, seconds=0)
    if isinstance(delta, int):
        delta = timedelta(seconds=delta)

    days = delta.days
    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return str_format.format(days=days, hours=hours, minutes=minutes, seconds=seconds)


def generate_job_id(job_type: str, run_time: datetime, page_id: str = None) -> str:
    """
    根据任务类型、运行时间和页面ID生成job_id
    :param job_type: 任务类型，可以是字符串或枚举
    :param run_time: 运行时间
    :param page_id: 页面ID (可选)
    :return: 生成的job_id
    """
    # 处理枚举类型，获取其值
    if hasattr(job_type, 'value'):
        job_type = job_type.value
    
    base_id = f"{job_type}_{run_time.strftime('%Y%m%d_%H%M%S')}"
    if page_id:
        return f"{base_id}_{page_id}"
    return base_id


def generate_ranking_hash_id(ranking_data: dict) -> str:
    """
    为榜单数据生成MD5哈希ID
    
    使用以下字段按顺序拼接：rank_id|channel_name|channel_id|page_id|sub_channel_id
    空值使用空字符串
    
    :param ranking_data: 榜单数据字典
    :return: 32位MD5哈希字符串
    """
    # 按指定顺序提取字段，空值使用空字符串
    fields = [
        ranking_data.get("rank_id", "") or "",
        ranking_data.get("channel_name", "") or "", 
        ranking_data.get("channel_id", "") or "",
        ranking_data.get("page_id", "") or "",
        ranking_data.get("sub_channel_id", "") or ""
    ]
    
    # 转换为字符串并拼接
    text_to_hash = "|".join(str(field) for field in fields)
    
    # 生成MD5哈希
    return hashlib.md5(text_to_hash.encode('utf-8')).hexdigest()