import uuid
from datetime import datetime
from time import strftime
from typing import Dict, List
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
    digits_str = ''.join(re.findall(r'\d', string))
    number = int(digits_str)
    return number


def filter_dict(raw_dict: dict, valid_field: set | list):
    """
    过滤字典
    :param raw_dict:
    :param valid_field:
    :return:
    """
    return {k: v for k, v in raw_dict.items() if k in valid_field}


def get_model_fields(model_class) -> set[str]:
    """
    获取 SQLAlchemy 模型的所有字段名
    
    :param model_class: SQLAlchemy 模型类
    :return: 字段名集合
    """
    mapper = inspect(model_class)
    return set(mapper.columns.keys())
