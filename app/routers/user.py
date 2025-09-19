# coding=utf-8
# 2025.9.19

"""
用户API路由模块

提供用户相关的所有API端点
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, UserUpdate, UserResponse, 
    LoginResponse, ErrorResponse
)
from app.services.user import UserService


# 创建路由器
router = APIRouter(
    prefix="/api/users",
    tags=["用户管理"],
    responses={
        400: {"model": ErrorResponse, "description": "请求错误"},
        401: {"model": ErrorResponse, "description": "未授权"},
        403: {"model": ErrorResponse, "description": "权限不足"},
        404: {"model": ErrorResponse, "description": "资源不存在"},
        409: {"model": ErrorResponse, "description": "资源冲突"},
        500: {"model": ErrorResponse, "description": "服务器错误"},
    }
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="用户注册",
    description="创建新用户账户",
    responses={
        201: {"description": "用户创建成功"},
        409: {"description": "用户名已存在"},
    }
)
async def register_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    用户注册
    
    创建新的用户账户。用户名必须唯一，密码将被安全地哈希存储。
    
    - **username**: 用户名（用户名只能包含中英文、数字、下划线、空格，且不能以空格开头，长度1-20）
    - **password**: 密码（密码长度必须在 6~20 个字符之间，仅包含数字、大小写字母和英文标点符号）
    - **timezone**: 时区（可选，默认UTC）
    """
    user = UserService.create_user(db, user_data)
    
    return UserService.get_user_response(user)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="用户登录",
    description="用户认证并获取访问令牌",
    responses={
        200: {"description": "登录成功"},
        401: {"description": "用户名或密码错误"},
        403: {"description": "用户账户已被禁用"},
    }
)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
) -> LoginResponse:
    """
    用户登录
    
    验证用户凭据并返回访问令牌。成功登录后，客户端应该保存token用于后续API调用。
    
    - **username**: 用户名（区分大小写）
    - **password**: 密码
    
    返回用户信息和访问令牌，token有效期为7天。
    """
    return UserService.login_user(db, login_data.username, login_data.password)


@router.get(
    "/profile",
    response_model=UserResponse,
    summary="获取当前用户信息",
    description="获取当前认证用户的详细信息",
    responses={
        200: {"description": "获取成功"},
        401: {"description": "未授权，需要登录"},
    }
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    获取当前用户信息
    
    返回当前认证用户的详细信息。需要在Header中提供有效的Bearer token。
    
    **需要认证**: 
    """
    return UserService.get_user_response(current_user)


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="更新用户信息",
    description="更新当前用户的个人信息",
    responses={
        200: {"description": "更新成功"},
        401: {"description": "未授权，需要登录"},
        400: {"description": "请求数据无效"},
    }
)
async def update_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """
    更新用户信息
    
    更新当前用户的个人信息。只能更新显示名称和时区，不能更改用户名和密码。
    
    - **timezone**: 新的时区（可选）
    
    **需要认证**: 是
    
    **注意**: 
    - 只提供需要更新的字段
    - 用户名和密码不能通过此接口修改
    - 密码修改需要单独的安全接口
    """
    # 更新当前用户信息
    updated_user = UserService.update_user(db, current_user.user_id, user_update)
    return UserService.get_user_response(updated_user)