"""
数据库连接管理
使用 SQLite 数据库，提供 SQLAlchemy 引擎和会话管理
创建时间: 2025-10-27
更新时间: 2025-11-03 - 添加 SQLite 支持
更新时间: 2025-11-04 - 移除 PostgreSQL 支持，仅保留 SQLite
"""
import os
from pathlib import Path
from sqlalchemy import create_engine, event, inspect
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
    """初始化 SQLite 数据库连接，并自动创建表（如果不存在）"""
    global engine, SessionLocal

    if not settings.DATABASE_URL:
        logger.warning("未配置 DATABASE_URL，数据库功能将不可用")
        return

    try:
        # 确保数据目录存在
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            Path(db_dir).mkdir(parents=True, exist_ok=True)
            logger.info(f"数据目录已创建: {db_dir}")

        # 创建 SQLite 引擎
        engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False},  # SQLite 多线程支持
            echo=False
        )

        # 启用 SQLite 外键约束和 WAL 模式
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA journal_mode=WAL")  # 使用 WAL 模式提升性能
            cursor.close()

        # 创建会话工厂
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

        logger.info(f"SQLite 数据库连接初始化成功: {db_path}")

        # 自动创建表（如果不存在）
        _create_tables_if_not_exists()

    except Exception as e:
        logger.error(f"数据库连接初始化失败: {str(e)}")
        raise


def _create_tables_if_not_exists():
    """检查表是否存在，如果不存在则创建"""
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    try:
        # 导入所有模型以注册到 Base.metadata
        from ..models.trading_session import TradingSession
        from ..models.ai_decision import AIDecision
        from ..models.trade import Trade

        # 使用 inspector 检查表是否存在
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()

        # 获取所有模型定义的表名
        expected_tables = Base.metadata.tables.keys()

        # 检查是否有缺失的表
        missing_tables = [table for table in expected_tables if table not in existing_tables]

        if missing_tables:
            logger.info(f"检测到缺失的表: {', '.join(missing_tables)}")
            logger.info("正在创建数据库表...")
            Base.metadata.create_all(bind=engine)
            logger.info("✅ 数据库表创建成功")
        else:
            logger.info(f"✅ 数据库表已存在 ({len(existing_tables)} 个表)")

    except Exception as e:
        logger.error(f"检查/创建数据库表失败: {str(e)}")
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
    创建所有表（开发环境用）
    """
    if engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    try:
        # 导入所有模型以注册到 Base.metadata
        from ..models.trading_session import TradingSession
        from ..models.ai_decision import AIDecision
        from ..models.trade import Trade

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

