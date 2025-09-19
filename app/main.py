"""
Ta Mist - 日程助手应用主入口

FastAPI应用的主要配置和启动文件
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import init_database, get_db_info
from app.routers.user import router as user_router
from app.core.logging_config import setup_logging

setup_logging()

import logging
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Start Mist ...")
    
    try:
        logger.info("Initialize database...")
        init_database()
        
        db_info = get_db_info()
        logger.info(f"Database connected: {db_info['database_path']}")
        logger.info(f"Database size: {db_info['database_size']} bytes")
        
        logger.info("Mist gets ready!")
        logger.info("API: http://localhost:8000/docs")
        logger.info("ReDoc: http://localhost:8000/redoc")
        
    except Exception as e:
        logger.error(f"Failed to start: {e}")
        raise
    
    yield  # 应用运行期间
    
    logger.info("Turn off Mist...")


app = FastAPI(
    title="Mist",
    description="""
    Hi, I'm Mist. I'm here to help you not to miss your future.
    """,
    version="0.0.1",
    lifespan=lifespan
)


# install routers
app.include_router(user_router, tags=["用户管理"])


# root
@app.get("/", tags=["系统"])
async def root():
    """
    应用根端点
    
    返回应用的基本信息和状态
    """
    return {
        "message": "Hi, I'm Mist!",
        "version": "0.0.1",
        "status": "running",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "api_prefix": "/api"
    }


# 健康检查端点
@app.get("/health", tags=["系统"])
async def health_check():
    """
    系统健康检查
    
    检查应用和数据库的健康状态
    """
    try:
        # 获取数据库信息
        db_info = get_db_info()
        
        return {
            "status": "healthy",
            "timestamp": "2025-09-19T10:30:00Z",  # 实际项目中使用 datetime.utcnow()
            "version": "1.0.0",
            "database": {
                "status": "connected" if db_info["database_exists"] else "disconnected",
                "path": db_info["database_path"],
                "size": db_info["database_size"]
            },
            "services": {
                "user_management": "active",
                "authentication": "active"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"系统不健康: {str(e)}"
        )


# 全局异常处理器
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """处理404错误"""
    return JSONResponse(
        status_code=404,
        content={
            "detail": "请求的资源不存在",
            "path": str(request.url.path),
            "method": request.method
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """处理500错误"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": "服务器内部错误",
            "message": "请稍后重试或联系技术支持"
        }
    )