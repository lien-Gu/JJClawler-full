"""
基础类模块

提供通用的基础类来减少代码重复
"""
from typing import Optional, List, Any
from abc import ABC
from sqlmodel import Session

from app.modules.database import get_session_sync
from app.utils.log_utils import get_logger


class BaseDAO(ABC):
    """数据访问对象基类"""
    
    def __init__(self):
        self._session: Optional[Session] = None
        self.logger = get_logger(self.__class__.__name__)
    
    @property
    def session(self) -> Session:
        """获取数据库会话"""
        if self._session is None:
            self._session = get_session_sync()
        return self._session
    
    def close(self):
        """关闭数据库会话"""
        if self._session:
            self._session.close()
            self._session = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class BaseService(ABC):
    """业务服务基类"""
    
    def __init__(self):
        self._daos: List[BaseDAO] = []
        self.logger = get_logger(self.__class__.__name__)
    
    def add_dao(self, dao: BaseDAO):
        """添加DAO到管理列表"""
        self._daos.append(dao)
    
    def close(self):
        """关闭所有DAO"""
        for dao in self._daos:
            try:
                dao.close()
            except Exception as e:
                self.logger.warning(f"关闭DAO失败: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def handle_service_error(logger, operation: str, error: Exception, default_return: Any = None):
    """统一的服务错误处理"""
    logger.error(f"{operation}失败: {error}")
    return default_return