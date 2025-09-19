# coding=utf-8
# 2025.9.19

"""
数据库依赖注入模块

提供数据库会话和相关操作的依赖注入函数
"""

from typing import Generator
from contextlib import contextmanager

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from app.core.database import get_db as _get_db, get_db_info


# 重新导出基础数据库会话依赖
def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话依赖
    
    这是核心数据库依赖，大部分API都会使用
    重新导出core.database.get_db，提供统一的导入路径
    """
    yield from _get_db()


def get_db_with_error_handling() -> Generator[Session, None, None]:
    """
    带错误处理的数据库会话依赖
    
    自动处理常见的数据库错误，转换为合适的HTTP响应
    适用于需要更好错误处理的API端点
    """
    db = next(_get_db())
    try:
        yield db
    except IntegrityError as e:
        db.rollback()
        # 处理数据完整性错误（如唯一约束违反）
        if "UNIQUE constraint failed" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="数据已存在，违反唯一性约束"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="数据完整性错误"
            )
    except SQLAlchemyError as e:
        db.rollback()
        # 处理其他数据库错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="数据库操作失败"
        )
    except Exception as e:
        db.rollback()
        # 处理未预期的错误
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服务器内部错误"
        )
    finally:
        db.close()


@contextmanager
def get_db_transaction():
    """
    事务管理上下文管理器
    
    提供自动事务管理，成功时提交，失败时回滚
    用于需要事务保证的复杂操作
    
    使用示例:
        with get_db_transaction() as db:
            # 数据库操作
            user = create_user(db, user_data)
            log_action(db, "user_created", user.id)
            # 自动提交事务
    """
    db = next(_get_db())
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_readonly_db() -> Generator[Session, None, None]:
    """
    只读数据库会话依赖
    
    用于只读操作，确保不会意外修改数据
    适用于查询、报表等只读API
    """
    db = next(_get_db())
    try:
        # 设置会话为只读模式（防止意外提交）
        db.autocommit = False
        db.autoflush = False
        yield db
        # 只读模式下不执行commit
    except Exception:
        # 即使出错也不需要rollback，因为没有修改操作
        pass
    finally:
        db.close()


class DatabaseHealthChecker:
    """数据库健康检查器"""
    
    def __init__(self):
        self.last_check_result = True
    
    def check_health(self) -> bool:
        """检查数据库健康状态"""
        try:
            db = next(_get_db())
            try:
                # 执行简单查询检查连接
                db.execute("SELECT 1")
                self.last_check_result = True
                return True
            finally:
                db.close()
        except Exception:
            self.last_check_result = False
            return False
    
    def get_health_status(self) -> dict:
        """获取详细的健康状态信息"""
        is_healthy = self.check_health()
        db_info = get_db_info()
        
        return {
            "database_healthy": is_healthy,
            "database_exists": db_info["database_exists"],
            "database_size": db_info["database_size"],
            "database_path": db_info["database_path"],
            "last_check_time": "now"  # 实际项目中可以记录具体时间
        }


# 全局健康检查器实例
health_checker = DatabaseHealthChecker()


def get_db_health_checker() -> DatabaseHealthChecker:
    """
    数据库健康检查依赖
    
    用于健康检查API或需要验证数据库状态的场景
    """
    return health_checker


def check_db_health() -> dict:
    """
    数据库健康检查依赖函数
    
    返回数据库健康状态，可用于健康检查API
    如果数据库不健康，抛出HTTP异常
    """
    health_status = health_checker.get_health_status()
    
    if not health_status["database_healthy"]:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="数据库服务不可用"
        )
    
    return health_status


# 数据库操作装饰器依赖
def with_db_error_handling(func):
    """
    数据库操作错误处理装饰器
    
    为数据库操作函数添加统一的错误处理
    可以用于service层的函数
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="数据已存在"
                )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="数据完整性错误"
            )
        except SQLAlchemyError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="数据库操作失败"
            )
    return wrapper


# 便捷的依赖注入别名
# 为不同场景提供语义化的别名

# 标准数据库会话（最常用）
DatabaseSession = Depends(get_db)

# 带错误处理的数据库会话（推荐用于写操作）
SafeDatabaseSession = Depends(get_db_with_error_handling)

# 只读数据库会话（推荐用于查询操作）
ReadOnlyDatabaseSession = Depends(get_readonly_db)

# 数据库健康检查
DatabaseHealthCheck = Depends(check_db_health)