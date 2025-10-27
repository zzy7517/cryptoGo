"""
CryptoGo - FastAPI 主应用
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

from app.core.config import settings
from app.core.logging import setup_logging, InterceptHandler
from app.core.exceptions import (
    CryptoGoException,
    UnsupportedFeatureException, 
    DataFetchException,
    RateLimitException,
    ValidationException
)
from app.api.v1 import market

# 初始化 Loguru 日志系统
logger = setup_logging()

# 拦截标准库 logging，转发到 Loguru
logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
logging.getLogger("uvicorn").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
logging.getLogger("fastapi").handlers = [InterceptHandler()]

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="基于大语言模型的智能加密货币交易系统",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# 异常处理器
# ============================================

@app.exception_handler(UnsupportedFeatureException)
async def unsupported_feature_handler(request: Request, exc: UnsupportedFeatureException):
    """
    不支持的功能异常处理
    
    返回 501 Not Implemented
    """
    logger.warning(
        "不支持的功能",
        error=exc.message,
        path=str(request.url),
        error_code=exc.error_code
    )
    return JSONResponse(
        status_code=501,
        content=exc.to_dict()
    )


@app.exception_handler(DataFetchException)
async def data_fetch_exception_handler(request: Request, exc: DataFetchException):
    """
    数据获取失败异常处理
    
    返回 503 Service Unavailable
    """
    logger.error(
        "数据获取失败",
        error=exc.message,
        path=str(request.url),
        error_code=exc.error_code,
        details=exc.details
    )
    return JSONResponse(
        status_code=503,
        content=exc.to_dict()
    )


@app.exception_handler(RateLimitException)
async def rate_limit_exception_handler(request: Request, exc: RateLimitException):
    """
    频率限制异常处理
    
    返回 429 Too Many Requests
    """
    logger.warning(
        "触发频率限制",
        error=exc.message,
        path=str(request.url),
        error_code=exc.error_code
    )
    return JSONResponse(
        status_code=429,
        content=exc.to_dict(),
        headers={"Retry-After": "60"}  # 建议 60 秒后重试
    )


@app.exception_handler(ValidationException)
async def validation_exception_handler(request: Request, exc: ValidationException):
    """
    验证异常处理
    
    返回 400 Bad Request
    """
    logger.warning(
        "参数验证失败",
        error=exc.message,
        path=str(request.url),
        details=exc.details
    )
    return JSONResponse(
        status_code=400,
        content=exc.to_dict()
    )


@app.exception_handler(CryptoGoException)
async def cryptogo_exception_handler(request: Request, exc: CryptoGoException):
    """
    应用自定义异常处理
    
    捕获所有继承自 CryptoGoException 的异常
    """
    logger.error(
        "应用异常",
        error=exc.message,
        path=str(request.url),
        error_code=exc.error_code,
        details=exc.details
    )
    return JSONResponse(
        status_code=500,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    全局异常处理器
    
    捕获所有未处理的异常
    """
    logger.exception(
        "未处理的异常",
        error=str(exc),
        path=str(request.url),
        exception_type=type(exc).__name__
    )
    return JSONResponse(
        status_code=500,
        content={
            "error_type": "internal_server_error",
            "message": "服务器内部错误",
            "details": {
                "exception": str(exc) if settings.DEBUG else "Internal Server Error"
            }
        }
    )


# 注册路由
app.include_router(market.router, prefix="/api/v1")


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs",
        "message": "欢迎使用 CryptoGo API"
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.VERSION
    }


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.VERSION} 启动中...")
    logger.info(f"📊 交易所: {settings.EXCHANGE}")
    logger.info(f"📈 默认交易对: {settings.DEFAULT_SYMBOL}")
    logger.info(f"🌐 CORS 允许的源: {settings.CORS_ORIGINS}")
    
    # 测试交易所连接
    try:
        from app.services.data_collector import get_exchange_connector
        connector = get_exchange_connector()
        logger.info(f"✅ 交易所 {connector.exchange_id} 连接成功")
    except Exception as e:
        logger.error(f"❌ 交易所连接失败: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"👋 {settings.APP_NAME} 正在关闭...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9527,
        reload=settings.DEBUG
    )

