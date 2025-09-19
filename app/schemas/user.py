# coding=utf-8
# 2025.9.19
"""
用户API数据模型

定义用户相关的请求和响应数据格式
使用Pydantic进行数据验证和序列化
"""

from datetime import datetime
import re
import string
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class UserBase(BaseModel):
    """用户基础信息（共用字段）"""

    username: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="用户名只能包含中英文、数字、下划线、空格，且不能以空格开头，长度1-20",
        examples=["张三", "john_doe", "Alice 001"]
    )

    timezone: str = Field(
        default="UTC",
        max_length=50,
        description="user's time zone",
        examples=["UTC", "Asia/Shanghai", "America/New_York"]
    )


class UserCreate(UserBase):
    """用户注册请求模型"""

    password: str = Field(
        ...,
        min_length=6,
        max_length=20,
        description="密码，长度为6-20，仅限数字、字母和英文标点符号",
        examples=["Abc123!@#"]
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """密码验证"""
        allowed_chars = string.ascii_letters + string.digits + string.punctuation
        if not (6 <= len(v) <= 20):
            raise ValueError("密码长度必须在 6~20 个字符之间")
        if any(ch not in allowed_chars for ch in v):
            raise ValueError("密码只能包含数字、大小写字母和英文标点符号")
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """用户名验证"""
        pattern = r'^(?!\s)[\u4e00-\u9fa5A-Za-z0-9_ ]{1,20}$'
        if not re.match(pattern, v):
            raise ValueError("用户名只能包含中英文、数字、下划线、空格，且不能以空格开头，长度1-20")
        return v
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "password": "secure_password123",
                "timezone": "Asia/Shanghai"
            }
        }
    )


class UserLogin(BaseModel):
    """用户登陆请求模型"""
    username: str = Field(
        ...,
        description="用户名",
        examples=["john_doe"]
    )
    
    password: str = Field(
        ...,
        description="密码",
        examples=["password123"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "john_doe",
                "password": "secure_password123"
            }
        }
    )


class UserUpdate(BaseModel):
    """用户信息更新请求模型"""
    
    timezone: Optional[str] = Field(
        None,
        max_length=50,
        description="时区",
        examples=["Europe/London"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "display_name": "John Smith",
                "timezone": "Europe/London"
            }
        }
    )


class UserResponse(UserBase):
    """用户信息响应模型"""
    
    user_id: str = Field(
        ...,
        description="用户ID (ULID)",
        examples=["01HWXYZ1234567890ABCDEF"]
    )
    
    is_active: bool = Field(
        ...,
        description="是否激活",
        examples=[True]
    )
    
    created_at: datetime = Field(
        ...,
        description="创建时间",
        examples=["2025-09-19T10:30:00Z"]
    )
    
    updated_at: datetime = Field(
        ...,
        description="更新时间", 
        examples=["2025-09-19T10:30:00Z"]
    )
    
    model_config = ConfigDict(
        from_attributes=True,  # 允许从ORM模型创建
        json_schema_extra={
            "example": {
                "user_id": "01HWXYZ1234567890ABCDEF",
                "username": "john_doe",
                "display_name": "John Doe",
                "timezone": "Asia/Shanghai",
                "is_active": True,
                "created_at": "2025-09-19T10:30:00Z",
                "updated_at": "2025-09-19T10:30:00Z"
            }
        }
    )


class Token(BaseModel):
    """JWT令牌响应模型"""
    
    access_token: str = Field(
        ...,
        description="访问令牌",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )
    
    token_type: str = Field(
        default="bearer",
        description="令牌类型",
        examples=["bearer"]
    )
    
    expires_in: int = Field(
        ...,
        description="令牌有效期（分）",
        examples=[10080]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 10080
            }
        }
    )


class LoginResponse(BaseModel):
    """登录成功响应模型"""
    
    user: UserResponse = Field(
        ...,
        description="用户信息"
    )
    
    token: Token = Field(
        ...,
        description="访问令牌信息"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user": {
                    "user_id": "01HWXYZ1234567890ABCDEF",
                    "username": "john_doe", 
                    "display_name": "John Doe",
                    "timezone": "Asia/Shanghai",
                    "is_active": True,
                    "created_at": "2025-09-19T10:30:00Z",
                    "updated_at": "2025-09-19T10:30:00Z"
                },
                "token": {
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                    "token_type": "bearer",
                    "expires_in": 604800
                }
            }
        }
    )


class ErrorResponse(BaseModel):
    """错误响应模型"""
    
    detail: str = Field(
        ...,
        description="错误详情",
        examples=["用户名已存在"]
    )
    
    error_code: Optional[str] = Field(
        None,
        description="错误代码",
        examples=["USERNAME_ALREADY_EXISTS"]
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "用户名已存在",
                "error_code": "USERNAME_ALREADY_EXISTS"
            }
        }
    )