"""
CryptoGo - FastAPI 主应用
"""
import asyncio
import signal
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .utils.config import settings
from .utils.logging import setup_logging
from .utils.exceptions import (
    CryptoGoException,
    UnsupportedFeatureException, 
    DataFetchException,
    RateLimitException,
    ValidationException
)
from .api.v1.routes import api_v1_router

# 初始化 Loguru 日志系统
logger = setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    应用生命周期管理
    """
    # ============ 启动阶段 ============
    logger.info("=" * 80)
    logger.info(f"🚀 {settings.APP_NAME} v{settings.VERSION} 启动中...")
    logger.info(f"📊 交易所: {settings.EXCHANGE}")
    logger.info(f"📈 默认交易对: {settings.DEFAULT_SYMBOL}")
    logger.info(f"🌐 CORS 允许的源: {settings.CORS_ORIGINS}")
    logger.info("=" * 80)
    
    # 初始化数据库
    try:
        from .utils.database import init_db
        init_db()
        logger.info("✅ 数据库初始化成功")
    except Exception as e:
        logger.warning(f"⚠️ 数据库初始化失败: {str(e)}")
    
    # 测试交易所连接
    try:
        from .utils.data_collector import get_exchange
        _ = get_exchange()
        logger.info(f"✅ 交易所 {settings.EXCHANGE} 连接成功")
    except Exception as e:
        logger.error(f"❌ 交易所连接失败: {str(e)}")
    
    # 初始化后台 Agent 管理器
    from .services.trading_agent_service import get_background_agent_manager
    manager = get_background_agent_manager()
    logger.info("✅ 后台 Agent 管理器已初始化")
    logger.info("=" * 80)
    
    # yield 后的代码在关闭时执行
    yield
    
    # ============ 关闭阶段 ============
    logger.info("=" * 80)
    logger.info(f"👋 {settings.APP_NAME} 正在关闭...")
    logger.info("=" * 80)
    
    # 优雅关闭所有后台 Agent
    try:
        from .services.trading_session_service import TradingSessionService
        from .utils.database import get_db
        
        logger.info("🛑 开始停止所有后台 Agent...")
        running_agents = manager.list_agents()
        logger.info(f"📌 找到 {len(running_agents)} 个运行中的 Agent")
        
        # 设置关闭超时时间
        shutdown_timeout = 30  # 30秒超时
        
        for idx, agent_status in enumerate(running_agents, 1):
            if agent_status:
                session_id = agent_status['session_id']
                logger.info("-" * 60)
                logger.info(f"🔧 [{idx}/{len(running_agents)}] 停止 Session {session_id}")
                logger.info(f"   状态: {agent_status.get('status')}")
                logger.info(f"   运行次数: {agent_status.get('run_count')}")
                
                try:
                    # 异步停止 Agent（带超时）
                    await asyncio.wait_for(
                        manager.stop_background_agent(session_id),
                        timeout=shutdown_timeout
                    )
                    logger.info(f"✅ Agent 已停止 (Session {session_id})")
                    
                    # 更新会话状态
                    db = next(get_db())
                    try:
                        session_service = TradingSessionService(db)
                        session_service.end_session(
                            session_id=session_id,
                            status='stopped',
                            notes='应用关闭时自动结束'
                        )
                        logger.info(f"✅ 会话已关闭 (Session {session_id})")
                    except Exception as e:
                        logger.error(f"❌ 关闭会话失败 (Session {session_id}): {str(e)}")
                    finally:
                        db.close()
                        
                except asyncio.TimeoutError:
                    logger.error(f"⏱️ 停止 Agent 超时 (Session {session_id})，强制取消")
                except Exception as e:
                    logger.error(f"❌ 停止 Agent 失败 (Session {session_id}): {str(e)}")
                    logger.exception("详细错误:")
        
        logger.info("=" * 80)
        logger.info("✅ 所有后台 Agent 已停止")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ 关闭过程异常: {str(e)}")
        logger.exception("详细错误:")
    
    logger.info(f"👋 {settings.APP_NAME} 已关闭")


# 创建 FastAPI 应用（使用 lifespan）
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="自动合约交易",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan  # 使用新的 lifespan 管理器
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


# 注册集中式路由 - 所有 v1 API 路由
app.include_router(api_v1_router)


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


# ============================================
# 信号处理（优雅关闭）
# ============================================

def setup_signal_handlers():
    """设置信号处理器，确保优雅关闭"""
    def signal_handler(signum, frame):
        sig_name = signal.Signals(signum).name
        logger.info(f"📡 收到信号: {sig_name} ({signum})")
        logger.info("🛑 开始优雅关闭...")
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill
    logger.info("✅ 信号处理器已注册 (SIGINT, SIGTERM)")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9527,
        reload=settings.DEBUG
    )

