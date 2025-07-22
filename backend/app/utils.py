import uuid
from datetime import datetime
from time import strftime


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