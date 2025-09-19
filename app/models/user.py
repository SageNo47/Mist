# coding=utf-8
# 2025.8.18
"""
用户数据模型

定义用户表的结构和字段
"""

# import ulid
from sqlalchemy import Boolean, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
from app.models.utils import generate_ulid


class User(Base):
    """用户模型"""
    
    __tablename__ = "users"
    
    # 主键：ULID
    user_id: Mapped[str] = mapped_column(
        String(26),  # ULID固定长度26字符
        primary_key=True,
        default=generate_ulid,
        comment="user id"
    )
    
    # 用户名：唯一，用于登录
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="user name for logging"
    )
    
    # 显示名称：用于界面展示
    # display_name: Mapped[str] = mapped_column(
    #     String(100),
    #     nullable=False,
    #     comment="user name for displaying"
    # )
    
    # 密码哈希：存储加密后的密码
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="password in hash format"
    )
    
    # 时区：用于日程时间计算
    timezone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UTC",
        comment="user's time zone"
    )
    
    # 激活状态：用户是否可用
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        comment="active status"
    )
    
    # 数据库索引
    __table_args__ = (
        Index('idx_username', 'username'),  # 用户名索引（提高查询性能）
        Index('idx_user_active', 'is_active'),  # 激活状态索引
    )
    
    def __repr__(self) -> str:
        return f"<User(user_id='{self.user_id}', username='{self.username}')>"
    
    @property
    def id(self) -> str:
        """兼容性属性，返回user_id"""
        return self.user_id