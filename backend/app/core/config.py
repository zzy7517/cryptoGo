"""
核心配置模块
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    APP_NAME: str = "CryptoGo"
    VERSION: str = "0.1.0"
    DEBUG: bool = True
    
    # 交易所配置
    EXCHANGE: str = "binance"
    BINANCE_API_KEY: Optional[str] = None
    BINANCE_SECRET: Optional[str] = None
    BINANCE_TESTNET: bool = True
    
    # 默认交易对
    DEFAULT_SYMBOL: str = "BTC/USDT"
    
    # 数据库配置
    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    
    # AI 配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama2"
    
    # 交易参数
    MAX_POSITION_SIZE: float = 1000.0
    MAX_DAILY_TRADES: int = 10
    RISK_PER_TRADE: float = 0.02
    
    # CORS 配置
    CORS_ORIGINS: list = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()

