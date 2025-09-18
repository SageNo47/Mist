# coding=utf-8
# 2025.9.18

from datetime import datetime, timedelta, timezone
try:
    from datetime import UTC
    UTC_TZ = UTC
except ImportError:
    UTC_TZ = timezone.utc
from typing import Union, Any

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings
import logging


logger = logging.getLogger(__name__)


class PasswordManager:
    """密码管理工具类"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        对密码进行哈希加密
        
        Args:
            password: 明文密码
            
        Returns:
            加密后的密码哈希
        """
        # 生成盐并哈希密码
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        验证密码是否正确
        
        Args:
            plain_password: 明文密码
            hashed_password: 存储的密码哈希
            
        Returns:
            密码是否匹配
        """
        try:
            return bcrypt.checkpw(
                plain_password.encode('utf-8'),
                hashed_password.encode('utf-8')
            )
        except Exception:
            return False


class TokenManager:
    """JWT Token管理工具类"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
        """
        创建访问令牌
        
        Args:
            data: 要编码到token中的数据
            expires_delta: token有效期，默认使用配置的时间
            
        Returns:
            JWT访问令牌
        """
        to_encode = data.copy()
        
        # 设置过期时间
        if expires_delta:
            expire = datetime.now(UTC_TZ) + expires_delta
        else:
            expire = datetime.now(UTC_TZ) + timedelta(minutes=get_settings().jwt_access_token_expire_min)
        
        to_encode.update({"exp": expire})
        
        # 生成JWT token
        encoded_jwt = jwt.encode(to_encode, get_settings().jwt_secret_key, algorithm=get_settings().jwt_algorithm)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Union[dict, None]:
        """
        验证并解析JWT token
        
        Args:
            token: JWT令牌
            
        Returns:
            解析后的payload数据，验证失败返回None
        """
        try:
            payload = jwt.decode(token, get_settings().jwt_secret_key, algorithms=[get_settings().jwt_algorithm])
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Union[str, None]:
        """
        从token中提取用户ID
        
        Args:
            token: 从客户端接收的JWT令牌
            
        Returns:
            用户ID，验证失败返回None
        """
        payload = TokenManager.verify_token(token)
        if payload is None:
            return None
        return payload.get("sub")  # "sub" 是JWT标准中的用户标识字段


# 便捷函数
def hash_password(password: str) -> str:
    """哈希密码的便捷函数"""
    return PasswordManager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码的便捷函数"""
    return PasswordManager.verify_password(plain_password, hashed_password)


def create_access_token(user_id: str, expires_delta: Union[timedelta, None] = None) -> str:
    """
    为用户创建访问令牌的便捷函数
    
    Args:
        user_id: 用户ID
        expires_delta: token有效期
        
    Returns:
        JWT访问令牌
    """
    return TokenManager.create_access_token(
        data={"sub": user_id}, 
        expires_delta=expires_delta
    )


def verify_access_token(token: str) -> Union[str, None]:
    """
    验证访问令牌并返回用户ID的便捷函数
    
    Args:
        token: 从客户端接收的JWT令牌JWT令牌
        
    Returns:
        用户ID，验证失败返回None
    """
    return TokenManager.get_user_id_from_token(token)