"""
错误码定义

使用枚举类定义系统中所有的错误码，确保类型安全和标准化错误处理
"""

from enum import IntEnum


class StatusCode(IntEnum):
    """状态码枚举定义 - 确保只能使用预定义的状态码"""

    # 成功状态码
    SUCCESS = 200

    # 4xx 客户端错误
    BAD_REQUEST = 400  # 请求参数错误
    UNAUTHORIZED = 401  # 未认证
    FORBIDDEN = 403  # 无权限
    NOT_FOUND = 404  # 资源不存在
    METHOD_NOT_ALLOWED = 405  # 方法不允许
    VALIDATION_ERROR = 422  # 数据验证错误

    # 5xx 服务器错误
    INTERNAL_ERROR = 500  # 内部服务器错误
    SERVICE_UNAVAILABLE = 503  # 服务不可用

    # 1xxx 业务错误码 - 通用
    OPERATION_FAILED = 1001  # 操作失败
    PARAMETER_INVALID = 1002  # 参数无效
    DATA_NOT_FOUND = 1003  # 数据不存在
    DUPLICATE_DATA = 1004  # 数据重复

    # 2xxx 书籍相关错误
    BOOK_NOT_FOUND = 2001  # 书籍不存在
    BOOK_DATA_INVALID = 2002  # 书籍数据无效

    # 3xxx 榜单相关错误
    RANKING_NOT_FOUND = 3001  # 榜单不存在
    RANKING_DATA_INVALID = 3002  # 榜单数据无效

    # 4xxx 爬虫相关错误
    CRAWLER_FAILED = 4001  # 爬虫执行失败
    TASK_NOT_FOUND = 4002  # 任务不存在
    TASK_CREATE_FAILED = 4003  # 任务创建失败
    INVALID_CHANNEL = 4004  # 无效频道
    SCHEDULER_ERROR = 4005  # 调度器错误

    # 5xxx 用户相关错误
    USER_NOT_FOUND = 5001  # 用户不存在
    USER_DATA_INVALID = 5002  # 用户数据无效

    # 6xxx 系统相关错误
    CONFIG_ERROR = 6001  # 配置错误
    DATABASE_ERROR = 6002  # 数据库错误
    CACHE_ERROR = 6003  # 缓存错误


class ErrorMessages:
    """错误消息映射"""

    MESSAGES = {
        # 成功
        StatusCode.SUCCESS: "操作成功",
        # 4xx 客户端错误
        StatusCode.BAD_REQUEST: "请求参数错误",
        StatusCode.UNAUTHORIZED: "身份验证失败",
        StatusCode.FORBIDDEN: "权限不足",
        StatusCode.NOT_FOUND: "资源不存在",
        StatusCode.METHOD_NOT_ALLOWED: "请求方法不被允许",
        StatusCode.VALIDATION_ERROR: "数据验证失败",
        # 5xx 服务器错误
        StatusCode.INTERNAL_ERROR: "内部服务器错误",
        StatusCode.SERVICE_UNAVAILABLE: "服务暂时不可用",
        # 1xxx 通用业务错误
        StatusCode.OPERATION_FAILED: "操作失败",
        StatusCode.PARAMETER_INVALID: "参数无效",
        StatusCode.DATA_NOT_FOUND: "数据不存在",
        StatusCode.DUPLICATE_DATA: "数据重复",
        # 2xxx 书籍相关错误
        StatusCode.BOOK_NOT_FOUND: "书籍不存在",
        StatusCode.BOOK_DATA_INVALID: "书籍数据无效",
        # 3xxx 榜单相关错误
        StatusCode.RANKING_NOT_FOUND: "榜单不存在",
        StatusCode.RANKING_DATA_INVALID: "榜单数据无效",
        # 4xxx 爬虫相关错误
        StatusCode.CRAWLER_FAILED: "爬虫执行失败",
        StatusCode.TASK_NOT_FOUND: "任务不存在",
        StatusCode.TASK_CREATE_FAILED: "任务创建失败",
        StatusCode.INVALID_CHANNEL: "无效的爬取频道",
        StatusCode.SCHEDULER_ERROR: "调度器错误",
        # 5xxx 用户相关错误
        StatusCode.USER_NOT_FOUND: "用户不存在",
        StatusCode.USER_DATA_INVALID: "用户数据无效",
        # 6xxx 系统相关错误
        StatusCode.CONFIG_ERROR: "配置错误",
        StatusCode.DATABASE_ERROR: "数据库错误",
        StatusCode.CACHE_ERROR: "缓存错误",
    }

    @classmethod
    def get_message(cls, code: StatusCode) -> str:
        """根据错误码获取错误消息"""
        return cls.MESSAGES.get(code, "未知错误")


# 便捷的错误响应构建函数
def get_error_response(code: StatusCode, custom_message: str = None):
    """根据错误码构建错误响应"""
    from .response_utils import error_response

    message = custom_message or ErrorMessages.get_message(code)
    return error_response(code=code, message=message)
