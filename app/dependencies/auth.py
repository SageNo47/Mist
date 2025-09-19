# coding=utf-8
# 2025.9.19

"""
认证依赖注入模块

提供用户认证、权限验证等依赖注入函数
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import verify_access_token
from app.dependencies.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse


# HTTP Bearer token提取器
security = HTTPBearer()


def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    从HTTP Authorization header中提取JWT token
    
    Args:
        credentials: FastAPI自动注入的认证凭据
        
    Returns:
        提取出的JWT token字符串
        
    Raises:
        HTTPException: 当token格式不正确时
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证方案必须是Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


def verify_token(token: str = Depends(get_token_from_header)) -> str:
    """
    验证JWT token并返回用户ID
    
    Args:
        token: JWT token字符串
        
    Returns:
        token中包含的用户ID
        
    Raises:
        HTTPException: 当token无效或过期时
    """
    user_id = verify_access_token(token)
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def get_current_user(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
) -> User:
    """
    获取当前认证用户（只验证用户存在，不检查激活状态）
    
    Args:
        user_id: 从token中验证出的用户ID
        db: 数据库会话
        
    Returns:
        当前用户的User模型实例
        
    Raises:
        HTTPException: 当用户不存在时
    """
    user = db.query(User).filter(User.user_id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    获取当前活跃用户（在get_current_user基础上检查激活状态）
    
    Args:
        current_user: 当前用户
        
    Returns:
        验证为活跃状态的用户
        
    Raises:
        HTTPException: 当用户已被禁用时
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账户已被禁用"
        )
    return current_user


def get_optional_current_user(
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[User]:
    """
    获取可选的当前用户（无token时不报错）
    
    适用于某些接口可以匿名访问，但登录后提供额外功能的场景
    
    Args:
        db: 数据库会话
        credentials: 可选的认证凭据
        
    Returns:
        用户实例（如果已认证）或None（如果未认证）
    """
    if not credentials:
        return None
    
    try:
        # 验证token
        user_id = verify_access_token(credentials.credentials)
        if not user_id:
            return None
        
        # 获取用户
        user = db.query(User).filter(
            User.user_id == user_id,
            User.is_active == True
        ).first()
        
        return user
    except Exception:
        # 任何认证错误都返回None，不抛出异常
        return None


def get_current_user_info(
    user: User = Depends(get_current_active_user)
) -> User:
    """
    获取当前用户信息的便捷包装
    
    Args:
        user: 当前用户
        
    Returns:
        CurrentUser实例，提供便捷的属性访问
    """
    return CurrentUser(user)


def require_user_access(
    target_user_id: str,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    要求用户只能访问自己的资源
    
    用于保护需要用户身份验证的资源（如个人资料、个人日程等）
    
    Args:
        target_user_id: 目标用户ID
        current_user: 当前认证用户
        
    Returns:
        当前用户（验证通过）
        
    Raises:
        HTTPException: 当用户试图访问其他用户的资源时
    """
    if current_user.user_id != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="您只能访问自己的资源"
        )
    return current_user


def create_user_access_checker(target_user_id: str):
    """
    创建用户访问检查器工厂函数
    
    用于动态创建特定用户的访问检查依赖
    
    Args:
        target_user_id: 目标用户ID
        
    Returns:
        检查函数，可用作FastAPI依赖
    """
    def check_access(current_user: User = Depends(get_current_active_user)) -> User:
        return require_user_access(target_user_id, current_user)
    
    return check_access


# 便捷的依赖注入别名
# 为不同认证需求提供语义化的别名

# 必须登录的用户
CurrentUser = Depends(get_current_active_user)

# 用户信息便捷访问
CurrentUserInfo = Depends(get_current_user_info)

# 可选登录的用户
OptionalCurrentUser = Depends(get_optional_current_user)

# 仅验证token有效性
ValidToken = Depends(verify_token)


# 认证装饰器（可选，用于service层）
def require_authentication(func):
    """
    认证装饰器，确保函数调用者已认证
    
    可用于service层函数的额外保护
    """
    def wrapper(*args, **kwargs):
        # 这里可以添加额外的认证逻辑
        # 实际项目中，主要在API层处理认证
        return func(*args, **kwargs)
    return wrapper


# 用户权限检查（为后续扩展预留）
class UserPermission:
    """用户权限检查类（预留扩展）"""
    
    @staticmethod
    def can_modify_schedule(user: User, schedule_user_id: str) -> bool:
        """检查用户是否可以修改指定日程"""
        # 目前简单实现：用户只能修改自己的日程
        return user.user_id == schedule_user_id
    
    @staticmethod
    def can_view_schedule(user: User, schedule_user_id: str) -> bool:
        """检查用户是否可以查看指定日程"""
        # 目前简单实现：用户只能查看自己的日程
        return user.user_id == schedule_user_id


def check_schedule_access(schedule_user_id: str):
    """
    检查日程访问权限的依赖工厂
    
    Args:
        schedule_user_id: 日程所属用户ID
        
    Returns:
        权限检查依赖函数
    """
    def check_permission(current_user: User = Depends(get_current_active_user)) -> User:
        if not UserPermission.can_view_schedule(current_user, schedule_user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="您没有权限访问此日程"
            )
        return current_user
    
    return Depends(check_permission)