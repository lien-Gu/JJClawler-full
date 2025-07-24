import uuid
from datetime import datetime
from time import strftime
from typing import Dict, List
import re


def generate_batch_id() -> str:
    """
    生成新的批次ID
    使用时间和UUID4生成唯一的批次标识符
    Returns:
        str: 23位UUID字符串格式的批次ID
    """
    return "{}-{}".format(
        strftime("%Y%m%d%H%M%S", datetime.now()),
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
