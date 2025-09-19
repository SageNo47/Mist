# coding=utf-8
# 2025.9.19

"""
用户业务逻辑模块

处理用户相关的所有业务逻辑，包括注册、登录、更新等
"""

from typing import Optional, Union
from datetime import timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserResponse, LoginResponse, Token
from app.core.security import hash_password, verify_password, create_access_token
from app.config import get_settings

JWT_ACCESS_TOKEN_EXPIRE_MIN = get_settings().jwt_access_token_expire_min

class UserService:
    """用户服务类，包含所有用户相关的业务逻辑"""
    
    @staticmethod
    def create_user(db: Session, user_data: UserCreate) -> User:
        """
        创建新用户（用户注册）
        
        Args:
            db: 数据库会话
            user_data: 用户注册数据
            
        Returns:
            创建的用户实例
            
        Raises:
            HTTPException: 当用户名已存在时
        """
        # 检查用户名是否已存在
        if UserService.get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户名已存在",
                headers={"error_code": "USERNAME_ALREADY_EXISTS"}
            )
        
        # 创建用户实例
        db_user = User(
            username=user_data.username,
            password_hash=hash_password(user_data.password),
            timezone=user_data.timezone,
            is_active=True
        )
        
        try:
            # 保存到数据库
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户创建失败，用户名可能已存在"
            )
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
        """
        用户认证（登录验证）
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            认证成功返回用户实例，失败返回None
        """
        # 获取用户
        user = UserService.get_user_by_username(db, username)
        if not user:
            return None
        
        # 验证密码
        if not verify_password(password, user.password_hash):
            return None
        
        return user
    
    @staticmethod
    def login_user(db: Session, username: str, password: str) -> LoginResponse:
        """
        用户登录（包含认证和token生成）
        
        Args:
            db: 数据库会话
            username: 用户名
            password: 密码
            
        Returns:
            登录响应，包含用户信息和访问令牌
            
        Raises:
            HTTPException: 当认证失败时
        """
        # 认证用户
        user = UserService.authenticate_user(db, username, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # 检查用户是否被禁用
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="用户账户已被禁用"
            )
        
        # 生成访问令牌
        access_token = create_access_token(
            user_id=user.user_id,
            expires_delta=timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MIN)
        )
        
        # 构造响应
        user_response = UserResponse(
            user_id=user.user_id,
            username=user.username,
            timezone=user.timezone,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        token_response = Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=JWT_ACCESS_TOKEN_EXPIRE_MIN * 60  # 转换为秒
        )
        
        return LoginResponse(
            user=user_response,
            token=token_response
        )
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
        """
        根据用户ID获取用户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            用户实例或None
        """
        return db.query(User).filter(User.user_id == user_id).first()
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        根据用户名获取用户
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            用户实例或None
        """
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def update_user(db: Session, user_id: str, user_update: UserUpdate) -> User:
        """
        更新用户信息
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            user_update: 更新数据
            
        Returns:
            更新后的用户实例
            
        Raises:
            HTTPException: 当用户不存在时
        """
        # 获取用户
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 更新字段（只更新提供的字段）
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        
        try:
            db.commit()
            db.refresh(user)
            return user
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户信息更新失败"
            )
    
    @staticmethod
    def deactivate_user(db: Session, user_id: str) -> User:
        """
        禁用用户账户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            更新后的用户实例
            
        Raises:
            HTTPException: 当用户不存在时
        """
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user.is_active = False
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def activate_user(db: Session, user_id: str) -> User:
        """
        激活用户账户
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            
        Returns:
            更新后的用户实例
            
        Raises:
            HTTPException: 当用户不存在时
        """
        user = UserService.get_user_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        user.is_active = True
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def check_username_exists(db: Session, username: str) -> bool:
        """
        检查用户名是否已存在
        
        Args:
            db: 数据库会话
            username: 用户名
            
        Returns:
            存在返回True，不存在返回False
        """
        user = UserService.get_user_by_username(db, username)
        return user is not None
    
    @staticmethod
    def get_user_response(user: User) -> UserResponse:
        """
        将User模型转换为UserResponse
        
        Args:
            user: 用户模型实例
            
        Returns:
            用户响应模型
        """
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            timezone=user.timezone,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )


# 便捷函数（为向后兼容和简化使用）
def create_user(db: Session, user_data: UserCreate) -> User:
    """创建用户的便捷函数"""
    return UserService.create_user(db, user_data)


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """用户认证的便捷函数"""
    return UserService.authenticate_user(db, username, password)


def login_user(db: Session, username: str, password: str) -> LoginResponse:
    """用户登录的便捷函数"""
    return UserService.login_user(db, username, password)


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """根据ID获取用户的便捷函数"""
    return UserService.get_user_by_id(db, user_id)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """根据用户名获取用户的便捷函数"""
    return UserService.get_user_by_username(db, username)


def update_user(db: Session, user_id: str, user_update: UserUpdate) -> User:
    """更新用户的便捷函数"""
    return UserService.update_user(db, user_id, user_update)


# 用户验证相关的业务逻辑
class UserValidation:
    """用户验证相关的业务逻辑"""
    
    @staticmethod
    def validate_user_creation(db: Session, user_data: UserCreate) -> dict:
        """
        验证用户创建数据的完整性
        
        Args:
            db: 数据库会话
            user_data: 用户创建数据
            
        Returns:
            验证结果字典
        """
        errors = []
        
        # 检查用户名是否已存在
        if UserService.check_username_exists(db, user_data.username):
            errors.append("用户名已存在")
        
        # 可以添加更多验证规则
        # 例如：密码强度检查、邮箱格式验证等
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    @staticmethod
    def validate_password_strength(password: str) -> dict:
        """
        验证密码强度
        
        Args:
            password: 密码
            
        Returns:
            验证结果
        """
        errors = []
        
        # 可以添加更多密码规则
        # if not any(c.isupper() for c in password):
        #     errors.append("密码必须包含大写字母")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": "weak" if errors else "strong"
        }