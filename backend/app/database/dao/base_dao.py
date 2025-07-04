"""
基础DAO类
"""
from typing import TypeVar, Generic, Type, List, Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseDAO(Generic[ModelType]):
    """基础数据访问对象"""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    def create(self, db: Session, obj_in: Dict[str, Any]) -> ModelType:
        """创建对象"""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """根据ID获取对象"""
        return db.get(self.model, id)

    def get_multi(
            self,
            db: Session,
            *,
            skip: int = 0,
            limit: int = 100,
            filters: Optional[Dict[str, Any]] = None
    ) -> List[ModelType]:
        """获取多个对象"""
        query = select(self.model)

        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        query = query.offset(skip).limit(limit)
        result = db.execute(query)
        return list(result.scalars())

    def update(
            self,
            db: Session,
            *,
            db_obj: ModelType,
            obj_in: Dict[str, Any]
    ) -> ModelType:
        """更新对象"""
        for key, value in obj_in.items():
            if hasattr(db_obj, key):
                setattr(db_obj, key, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, *, id: Any) -> Optional[ModelType]:
        """删除对象"""
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

    def count(self, db: Session, filters: Optional[Dict[str, Any]] = None) -> int:
        """计算对象数量"""
        query = select(self.model)

        # 应用过滤条件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.where(getattr(self.model, key) == value)

        result = db.execute(query)
        return len(list(result.scalars()))

    def exists(self, db: Session, **kwargs) -> bool:
        """检查对象是否存在"""
        query = select(self.model)
        for key, value in kwargs.items():
            if hasattr(self.model, key):
                query = query.where(getattr(self.model, key) == value)

        return db.scalar(query.limit(1)) is not None
