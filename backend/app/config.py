"""
配置管理模块 - 使用Pydantic BaseSettings自动读取环境变量
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator, ValidationError
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """数据库配置"""

    # 数据库连接配置
    url: str = Field(default="sqlite:///./data/jjcrawler.db", description="数据库连接URL")
    echo: bool = Field(default=False, description="是否打印SQL语句")

    # 连接池配置
    pool_size: int = Field(default=5, ge=1, le=50, description="连接池大小")
    max_overflow: int = Field(default=10, ge=0, le=100, description="连接池最大溢出连接数")
    pool_timeout: int = Field(default=30, ge=1, le=300, description="连接池获取连接超时时间（秒）")
    pool_recycle: int = Field(default=3600, ge=300, le=86400, description="连接回收时间（秒）")

    class Config:
        env_prefix = "DATABASE_"
        env_file_encoding = "utf-8"


class APISettings(BaseSettings):
    """API服务配置"""

    # 基本配置
    title: str = Field(default="JJCrawler API", description="API标题")
    description: str = Field(default="晋江文学城爬虫API服务", description="API描述")
    version: str = Field(default="v1", description="API版本")

    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8000, ge=1, le=65535, description="服务器端口")
    debug: bool = Field(default=False, description="是否开启调试模式")

    # 跨域配置
    cors_enabled: bool = Field(default=True, description="是否启用CORS")
    cors_origins: List[str] = Field(default=["*"], description="允许的跨域源")
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"], description="允许的HTTP方法")
    cors_headers: List[str] = Field(default=["*"], description="允许的请求头")

    # 分页配置
    default_page_size: int = Field(default=20, ge=1, le=100, description="默认分页大小")
    max_page_size: int = Field(default=100, ge=1, le=1000, description="最大分页大小")

    class Config:
        env_prefix = "API_"
        env_file_encoding = "utf-8"


class CrawlerSettings(BaseSettings):
    """爬虫配置"""

    # HTTP客户端配置
    user_agent: dict = Field(
        default={'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 jjwxc/4.9.0',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'},
        description="User-Agent字符串")
    timeout: int = Field(default=30, ge=5, le=300, description="请求超时时间（秒）")
    retry_times: int = Field(default=3, ge=1, le=10, description="重试次数")
    retry_delay: float = Field(default=1.0, ge=0.1, le=10.0, description="重试延迟时间（秒）")

    # 爬取频率控制
    request_delay: float = Field(default=1.0, ge=0.1, le=60.0, description="请求间隔延迟（秒）")
    concurrent_requests: int = Field(default=5, ge=1, le=10, description="并发请求数")

    class Config:
        env_prefix = "CRAWLER_"
        env_file_encoding = "utf-8"


class SchedulerSettings(BaseSettings):
    """任务调度器配置"""

    # 调度器基本配置
    timezone: str = Field(default="Asia/Shanghai", description="时区设置")
    max_workers: int = Field(default=5, ge=1, le=20, description="最大工作线程数")

    # 任务默认配置
    job_defaults: Dict[str, Any] = Field(default={"coalesce": False, "max_instances": 1, "misfire_grace_time": 60},
                                         description="任务默认配置")

    # 任务存储配置
    job_store_type: str = Field(default="SQLAlchemyJobStore", description="任务存储类型")
    job_store_url: Optional[str] = Field(default="sqlite:///./data/jjcrawler.db", description="任务存储连接URL")

    class Config:
        env_prefix = "SCHEDULER_"
        env_file_encoding = "utf-8"


class LoggingSettings(BaseSettings):
    """日志配置"""

    level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="%(asctime)s-%(name)s-%(levelname)s-%(message)s", description="日志格式")
    console_enabled: bool = Field(default=True, description="是否启用控制台输出")
    file_enabled: bool = Field(default=True, description="是否启用文件输出")

    # 日志文件配置
    file_path: str = Field(default="./logs/jjcrawler.log", description="日志文件路径")
    max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024 * 1024, le=100 * 1024 * 1024,
                           description="单个日志文件最大大小（字节）")
    backup_count: int = Field(default=5, ge=1, le=20, description="备份日志文件数量")

    # 错误日志配置
    error_file_enabled: bool = Field(default=True, description="是否启用错误日志文件")
    error_file_path: str = Field(default="./logs/jjcrawler_error.log", description="错误日志文件路径")

    class Config:
        env_prefix = "LOG_"
        env_file_encoding = "utf-8"

    @field_validator('level')
    @classmethod
    def validate_log_level(cls, v: str):
        """验证日志级别"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'日志级别必须是 {valid_levels} 中的一个')
        return v.upper()


class Settings(BaseSettings):
    """主配置类 - 整合所有配置"""

    # 环境配置
    env: str = Field(default="dev", description="运行环境")
    debug: bool = Field(default=False, description="调试模式")

    # 项目信息
    project_name: str = Field(default="JJCrawler", description="项目名称")
    project_version: str = Field(default="1.0.0", description="项目版本")

    # 数据目录配置
    data_dir: str = Field(default="./data", description="数据目录")
    logs_dir: str = Field(default="./logs", description="日志目录")

    # 子配置
    database: DatabaseSettings = Field(default_factory=DatabaseSettings, description="数据库配置")
    api: APISettings = Field(default_factory=APISettings, description="API配置")
    crawler: CrawlerSettings = Field(default_factory=CrawlerSettings, description="爬虫配置")
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings, description="调度器配置")
    logging: LoggingSettings = Field(default_factory=LoggingSettings, description="日志配置")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()

    def _ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.data_dir,
            self.logs_dir,
            Path(self.logging.file_path).parent
        ]

        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)

    @field_validator('env')
    def validate_environment(cls, v):
        """验证环境配置"""
        valid_environments = ['dev', 'test', 'prod']
        if v.lower() not in valid_environments:
            raise ValueError(f'环境必须是 {valid_environments} 中的一个')
        return v.lower()

    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.env == 'dev'

    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.env == 'test'

    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env == 'prod'

    def get_database_url(self) -> str:
        """获取数据库连接URL"""
        return self.database.url


# 全局设置实例
_settings = Settings()
settings = _settings


# 便捷访问函数
def get_settings() -> Settings:
    """获取设置实例"""
    return _settings


def get_database_url() -> str:
    """获取数据库连接URL"""
    return _settings.get_database_url()


def is_debug() -> bool:
    """是否为调试模式"""
    return _settings.debug or _settings.is_development()


def is_production() -> bool:
    """是否为生产环境"""
    return _settings.is_production()

if __name__ == '__main__':
    try:
        # Pydantic-settings 会自动从环境变量或 .env 文件加载
        # 这里我们直接传入数据进行测试
        config = get_settings().logging
        print("有效配置测试通过:")
        print(f"  log Level: {config.level}")  # 输出: WARNING
    except ValidationError as e:
        print("有效配置测试失败:", e)
