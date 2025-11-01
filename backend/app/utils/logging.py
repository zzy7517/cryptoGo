"""
日志配置模块 - 基于 Loguru
配置结构化日志系统，支持文件轮转、JSON 格式和多级别日志
创建时间: 2025-10-27
"""
import sys
from pathlib import Path
from loguru import logger

from .config import settings

def setup_logging():
    """
    配置应用日志系统
    
    使用 Loguru 提供：
    - 彩色控制台输出（开发环境）
    - JSON 格式日志文件（生产环境）
    - 自动日志轮转和压缩
    - 异步写入（enqueue=True）
    - 异常追踪
    """
    
    # 移除默认的 handler
    logger.remove()
    
    # 配置控制台输出
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    logger.add(
        sys.stderr,
        format=console_format,
        level=settings.LOG_LEVEL,  # 使用配置的日志级别
        colorize=True,
        backtrace=True,
        diagnose=True,
    )
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置普通日志文件（JSON 格式，便于后续分析）
    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # 每天午夜轮转
        retention="30 days",  # 保留 30 天
        compression="zip",  # 压缩旧日志
        enqueue=True,  # 异步写入
        backtrace=True,
        diagnose=True,
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    )
    
    # 配置错误日志文件（单独的错误日志）
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="90 days",  # 错误日志保留更长时间
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=True,
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
    )
    
    # 配置 JSON 格式日志（便于日志分析工具处理）
    logger.add(
        log_dir / "app_json_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="30 days",
        compression="zip",
        enqueue=True,
        level="INFO",
        serialize=True,  # JSON 格式
    )
    
    logger.info("日志系统初始化完成")
    logger.info(f"应用名称: {settings.APP_NAME}")
    logger.info(f"应用版本: {settings.VERSION}")
    logger.info(f"调试模式: {settings.DEBUG}")
    logger.info(f"日志级别: {settings.LOG_LEVEL}")
    
    return logger


def get_logger(name: str = None):
    """
    获取日志记录器
    
    Args:
        name: 模块名称，通常使用 __name__
        
    Returns:
        配置好的 logger 实例
        
    Example:
        from app.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Hello, world!")
    """
    if name:
        return logger.bind(module=name)
    return logger


# 注意：已移除 InterceptHandler
# 第三方库（如 SQLAlchemy、uvicorn、fastapi）将使用它们自己的日志格式
# 不再统一转发到 Loguru

