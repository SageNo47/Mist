# coding=utf-8
# 2025.9.18
"""
基础模型类

提供所有数据模型的基础结构和通用字段
"""
"""
基础模型类

提供所有数据模型的基础结构和通用字段
"""

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import as_declarative
from sqlalchemy.orm import Mapped, mapped_column


@as_declarative()
class Base:
    """所有数据模型的基类"""
    
    id: Any
    __name__: str
    
    # 生成表名：类名转为小写+s（如User -> users）
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"
    
    # 通用时间戳字段
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="creation time"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="update time"
    )
    
    def __repr__(self) -> str:
        """字符串表示"""
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"