"""
数据库连接管理
管理 PostgreSQL 数据库连接，提供 SQLAlchemy 引擎和会话管理
创建时间: 2025-10-27
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# SQLAlchemy Base
Base = declarative_base()

# 数据库引擎（延迟初始化）
engine = None
SessionLocal = None


def init_db():
    """初始化数据库连接"""
    global engine, SessionLocal
    
    if not settings.DATABASE_URL:
        logger.warning("未配置 DATABASE_URL，数据库功能将不可用")
        return
    
    try:
        # 创建引擎
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,  # 连接前检查
            pool_size=5,         # 连接池大小
            max_overflow=10,     # 最大溢出连接数
            echo=settings.DEBUG  # 是否打印 SQL（开发模式）
        )
        
        # 创建会话工厂
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        logger.info(
            "数据库连接初始化成功",
            database=settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else "hidden"
        )
        
    except Exception as e:
        logger.error(f"数据库连接初始化失败: {str(e)}")
        raise


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话（依赖注入用）
    
    用法：
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    创建所有表（开发环境用，生产环境使用 Alembic）
    """
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"创建数据库表失败: {str(e)}")
        raise


def drop_tables():
    """
    删除所有表（仅开发环境使用，危险操作！）
    """
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    
    if not settings.DEBUG:
        raise RuntimeError("生产环境禁止删除表！")
    
    try:
        Base.metadata.drop_all(bind=engine)
        logger.warning("数据库表已删除")
    except Exception as e:
        logger.error(f"删除数据库表失败: {str(e)}")
        raise

