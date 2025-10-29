"""
基础 Repository
提供通用的数据访问层基类，包含 CRUD 等常用操作
创建时间: 2025-10-27
"""
from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """基础数据访问层"""
    
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db
    
    def create(self, **kwargs) -> ModelType:
        """
        创建记录
        
        Args:
            **kwargs: 模型字段
            
        Returns:
            创建的模型实例
        """
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def get_by_id(self, id: int) -> Optional[ModelType]:
        """
        根据 ID 获取记录
        
        Args:
            id: 记录 ID
            
        Returns:
            模型实例或 None
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self, limit: int = 100, offset: int = 0) -> List[ModelType]:
        """
        获取所有记录
        
        Args:
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            模型实例列表
        """
        return self.db.query(self.model).offset(offset).limit(limit).all()
    
    def get_recent(self, limit: int = 10) -> List[ModelType]:
        """
        获取最近的记录（按创建时间倒序）
        
        Args:
            limit: 返回数量
            
        Returns:
            模型实例列表
        """
        return self.db.query(self.model)\
            .order_by(desc(self.model.created_at))\
            .limit(limit)\
            .all()
    
    def update(self, id: int, **kwargs) -> Optional[ModelType]:
        """
        更新记录
        
        Args:
            id: 记录 ID
            **kwargs: 要更新的字段
            
        Returns:
            更新后的模型实例或 None
        """
        instance = self.get_by_id(id)
        if not instance:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        self.db.commit()
        self.db.refresh(instance)
        return instance
    
    def delete(self, id: int) -> bool:
        """
        删除记录
        
        Args:
            id: 记录 ID
            
        Returns:
            是否删除成功
        """
        instance = self.get_by_id(id)
        if not instance:
            return False
        
        self.db.delete(instance)
        self.db.commit()
        return True
    
    def count(self) -> int:
        """
        统计记录数
        
        Returns:
            记录总数
        """
        return self.db.query(self.model).count()

