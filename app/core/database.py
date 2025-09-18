# coding=utf-8
# 2025.9.18

"""
数据库连接配置

管理SQLite数据库的连接、会话和表创建
"""

import logging
import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.models.base import Base
from app.config import get_settings


logger = logging.getLogger(__name__)

app_settings = get_settings()

DATABASE_PATH = Path(app_settings.database_path)  # 数据库文件路径
DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"  # 数据库URL

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # 允许多线程访问
    # 开发环境下显示SQL语句（生产环境可关闭）
    echo=True if os.getenv("ENV") == "development" else False
)

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    这个函数会被FastAPI的依赖注入系统使用
    确保每个请求都有独立的数据库会话，并在完成后关闭
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_tables() -> None:
    """
    创建所有数据表
    
    在应用启动时调用，根据模型定义创建数据库表
    """
    logger.info(f"Creating database tables at: {DATABASE_PATH}")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully!")


def drop_tables() -> None:
    """
    删除所有数据表
    
    谨慎使用！仅在开发环境重置数据库时使用
    """
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("All tables dropped!")


def get_db_info() -> dict:
    """
    获取数据库信息
    
    返回数据库路径、表数量等信息，用于调试
    """
    return {
        "database_path": str(DATABASE_PATH),
        "database_url": DATABASE_URL,
        "database_exists": DATABASE_PATH.exists(),
        "database_size": DATABASE_PATH.stat().st_size if DATABASE_PATH.exists() else 0
    }


# 数据库初始化函数
def init_database() -> None:
    """
    初始化数据库
    
    创建表并执行必要的初始化操作
    """
    try:
        create_tables()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise