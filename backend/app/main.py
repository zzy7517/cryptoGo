"""
CryptoGo - FastAPI 主应用
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys

from app.core.config import settings
from app.api.v1 import market

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

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


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"全局异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "path": str(request.url)
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

