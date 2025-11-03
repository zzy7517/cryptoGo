"""
数据库连接管理
支持 SQLite（默认）和 PostgreSQL，提供 SQLAlchemy 引擎和会话管理
创建时间: 2025-10-27
更新时间: 2025-11-03 - 添加 SQLite 支持
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from .config import settings
from .logging import get_logger

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
        # 判断是否为 SQLite
        is_sqlite = settings.DATABASE_URL.startswith("sqlite")
        
        # SQLite：确保数据目录存在
        if is_sqlite:
            db_path = settings.DATABASE_URL.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)
            if db_dir:
                Path(db_dir).mkdir(parents=True, exist_ok=True)
                logger.info(f"数据目录已创建: {db_dir}")
        
        # 创建引擎（根据数据库类型使用不同配置）
        if is_sqlite:
            engine = create_engine(
                settings.DATABASE_URL,
                connect_args={"check_same_thread": False},  # SQLite 多线程支持
                echo=False
            )
            
            # 启用 SQLite 外键约束
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")  # 使用 WAL 模式提升性能
                cursor.close()
                
        else:
            # PostgreSQL 配置
            engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                echo=False
            )
        
        # 创建会话工厂
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        db_info = "SQLite (local file)" if is_sqlite else settings.DATABASE_URL.split('@')[-1]
        logger.info(f"数据库连接初始化成功: {db_info}")
        
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

