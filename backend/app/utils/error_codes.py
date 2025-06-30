"""
错误码定义

定义系统中所有的错误码，用于标准化错误处理
"""

class ErrorCodes:
    """错误码常量定义"""
    
    # 成功状态码
    SUCCESS = 200
    
    # 4xx 客户端错误
    BAD_REQUEST = 400          # 请求参数错误
    UNAUTHORIZED = 401         # 未认证
    FORBIDDEN = 403           # 无权限
    NOT_FOUND = 404           # 资源不存在
    METHOD_NOT_ALLOWED = 405  # 方法不允许
    VALIDATION_ERROR = 422    # 数据验证错误
    
    # 5xx 服务器错误
    INTERNAL_ERROR = 500      # 内部服务器错误
    SERVICE_UNAVAILABLE = 503 # 服务不可用
    
    # 1xxx 业务错误码 - 通用
    OPERATION_FAILED = 1001   # 操作失败
    PARAMETER_INVALID = 1002  # 参数无效
    DATA_NOT_FOUND = 1003     # 数据不存在
    DUPLICATE_DATA = 1004     # 数据重复
    
    # 2xxx 书籍相关错误
    BOOK_NOT_FOUND = 2001     # 书籍不存在
    BOOK_DATA_INVALID = 2002  # 书籍数据无效
    
    # 3xxx 榜单相关错误
    RANKING_NOT_FOUND = 3001  # 榜单不存在
    RANKING_DATA_INVALID = 3002  # 榜单数据无效
    
    # 4xxx 爬虫相关错误
    CRAWLER_FAILED = 4001     # 爬虫执行失败
    TASK_NOT_FOUND = 4002     # 任务不存在
    TASK_CREATE_FAILED = 4003 # 任务创建失败
    INVALID_CHANNEL = 4004    # 无效频道
    SCHEDULER_ERROR = 4005    # 调度器错误
    
    # 5xxx 用户相关错误
    USER_NOT_FOUND = 5001     # 用户不存在
    USER_DATA_INVALID = 5002  # 用户数据无效
    
    # 6xxx 系统相关错误
    CONFIG_ERROR = 6001       # 配置错误
    DATABASE_ERROR = 6002     # 数据库错误
    CACHE_ERROR = 6003        # 缓存错误


class ErrorMessages:
    """错误消息映射"""
    
    MESSAGES = {
        # 成功
        200: "操作成功",
        
        # 4xx 客户端错误
        400: "请求参数错误",
        401: "身份验证失败",
        403: "权限不足",
        404: "资源不存在",
        405: "请求方法不被允许",
        422: "数据验证失败",
        
        # 5xx 服务器错误
        500: "内部服务器错误",
        503: "服务暂时不可用",
        
        # 1xxx 通用业务错误
        1001: "操作失败",
        1002: "参数无效",
        1003: "数据不存在",
        1004: "数据重复",
        
        # 2xxx 书籍相关错误
        2001: "书籍不存在",
        2002: "书籍数据无效",
        
        # 3xxx 榜单相关错误
        3001: "榜单不存在",
        3002: "榜单数据无效",
        
        # 4xxx 爬虫相关错误
        4001: "爬虫执行失败",
        4002: "任务不存在",
        4003: "任务创建失败",
        4004: "无效的爬取频道",
        4005: "调度器错误",
        
        # 5xxx 用户相关错误
        5001: "用户不存在",
        5002: "用户数据无效",
        
        # 6xxx 系统相关错误
        6001: "配置错误",
        6002: "数据库错误",
        6003: "缓存错误",
    }
    
    @classmethod
    def get_message(cls, code: int) -> str:
        """根据错误码获取错误消息"""
        return cls.MESSAGES.get(code, "未知错误")


# 便捷的错误响应构建函数
def get_error_response(code: int, custom_message: str = None):
    """根据错误码构建错误响应"""
    from .response_utils import error_response
    
    message = custom_message or ErrorMessages.get_message(code)
    return error_response(code=code, message=message)