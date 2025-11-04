"""
核心配置模块
使用 Pydantic Settings 管理应用配置，支持环境变量和 .env 文件
创建时间: 2025-10-27
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "CryptoGo"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"  # 日志级别: DEBUG, INFO, WARNING, ERROR
    
    # 交易所配置
    EXCHANGE: str = "binance"
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = True  # 是否使用测试网（Demo Trading）
    
    # 代理配置
    HTTP_PROXY: Optional[str] = "http://127.0.0.1:7897"
    HTTPS_PROXY: Optional[str] = "http://127.0.0.1:7897"
    
    # 默认交易对（合约格式）
    DEFAULT_SYMBOL: str = "BTC/USDT:USDT"
    
    # AI 配置 - DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"
    
    # 数据库配置 - 使用 SQLite（本地文件数据库）
    DATABASE_URL: str = "sqlite:///./data/trading.db"
    
    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://10.193.0.117:3000",
        "http://10.193.0.117:3001",
    ]
    
    # Pydantic v2 配置
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


# 全局配置实例
settings = Settings()

