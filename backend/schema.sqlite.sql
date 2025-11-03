-- CryptoGo 数据库表结构 - SQLite 版本
-- 自动迁移说明：使用 SQLAlchemy ORM 时，此文件仅作为参考
-- 实际表结构由 models/*.py 中的 ORM 模型定义
-- 创建时间: 2025-11-03

-- ============================================
-- 清理现有表（按依赖关系倒序删除）
-- ============================================

DROP TABLE IF EXISTS trades;
DROP TABLE IF EXISTS ai_decisions;
DROP TABLE IF EXISTS trading_sessions;


-- ============================================
-- 1. 交易会话表（核心表）
-- ============================================

CREATE TABLE trading_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    
    -- 基本信息
    session_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'stopped', 'crashed', 'completed')),
    
    -- 初始状态
    initial_capital DECIMAL(20, 4),
    current_capital DECIMAL(20, 4),
    
    -- 最终统计（会话结束时计算）
    final_capital DECIMAL(20, 4),
    total_pnl DECIMAL(20, 4),
    total_return_pct DECIMAL(10, 4),
    
    -- 交易统计
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    
    -- 后台交易运行状态
    background_status VARCHAR(20) DEFAULT 'idle' CHECK (background_status IN ('idle', 'starting', 'running', 'stopping', 'stopped', 'crashed')),
    background_started_at TIMESTAMP,
    background_stopped_at TIMESTAMP,
    last_decision_time TIMESTAMP,
    decision_count INTEGER DEFAULT 0,
    decision_interval INTEGER DEFAULT 180,
    trading_symbols TEXT,  -- SQLite 不支持数组，使用 JSON 文本存储
    last_error TEXT,
    trading_params TEXT,   -- JSON 格式的文本
    
    -- 配置信息
    config TEXT,           -- JSON 格式的文本
    
    -- 备注
    notes TEXT
);

-- 索引
CREATE INDEX idx_session_status ON trading_sessions(status);
CREATE INDEX idx_session_created ON trading_sessions(created_at DESC);


-- ============================================
-- 2. AI 决策记录表
-- ============================================

CREATE TABLE ai_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 关联会话
    session_id INTEGER REFERENCES trading_sessions(id) ON DELETE CASCADE,
    
    -- 决策信息
    symbols TEXT,          -- JSON 数组格式
    decision_type VARCHAR(20) CHECK (decision_type IN ('buy', 'sell', 'hold', 'rebalance', 'close')),
    confidence DECIMAL(5, 4),
    
    -- AI 输入/输出
    prompt_data TEXT,      -- JSON 格式
    ai_response TEXT,
    reasoning TEXT,
    
    -- 建议的交易参数
    suggested_actions TEXT, -- JSON 格式
    
    -- 执行情况
    executed BOOLEAN DEFAULT 0,
    execution_result TEXT,  -- JSON 格式
    
    -- 账户信息（用于资产变化追踪）
    account_balance DECIMAL(20, 4),
    unrealized_pnl DECIMAL(20, 4),
    total_asset DECIMAL(20, 4)
);

-- 索引
CREATE INDEX idx_decision_session ON ai_decisions(session_id);
CREATE INDEX idx_decision_created_at ON ai_decisions(created_at);
CREATE INDEX idx_decision_executed ON ai_decisions(executed);


-- ============================================
-- 3. 交易记录表
-- ============================================

CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- 关联会话
    session_id INTEGER REFERENCES trading_sessions(id) ON DELETE CASCADE,

    -- 交易信息
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    order_type VARCHAR(20) CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit')),

    -- 数量和价格
    quantity DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 4) NOT NULL,
    exit_price DECIMAL(20, 4),
    price DECIMAL(20, 4) NOT NULL,  -- 向后兼容字段（等同于 entry_price）
    total_value DECIMAL(20, 4) NOT NULL,
    leverage INTEGER DEFAULT 1,

    -- 名义价值（用于杠杆交易）
    notional_entry DECIMAL(20, 4),
    notional_exit DECIMAL(20, 4),

    -- 时间信息（用于计算持仓时长）
    entry_time TIMESTAMP,
    exit_time TIMESTAMP,
    holding_duration TEXT,  -- SQLite 使用文本存储时间间隔

    -- 费用
    entry_fee DECIMAL(20, 8),
    exit_fee DECIMAL(20, 8),
    total_fees DECIMAL(20, 8),
    fee DECIMAL(20, 8),  -- 向后兼容字段
    fee_currency VARCHAR(10),

    -- 盈亏（平仓时计算）
    pnl DECIMAL(20, 4) NOT NULL,
    pnl_pct DECIMAL(10, 4),

    -- 关联
    ai_decision_id INTEGER,
    entry_order_id VARCHAR(100),
    exit_order_id VARCHAR(100),
    exchange_order_id VARCHAR(100)  -- 向后兼容字段
);

-- 索引
CREATE INDEX idx_trade_session ON trades(session_id);
CREATE INDEX idx_trade_symbol_created ON trades(symbol, created_at);
CREATE INDEX idx_trade_created_at ON trades(created_at);
CREATE INDEX idx_trade_entry_time ON trades(entry_time);
CREATE INDEX idx_trade_exit_time ON trades(exit_time);


-- ============================================
-- SQLite 优化配置
-- ============================================

-- 启用外键约束（默认关闭）
PRAGMA foreign_keys = ON;

-- 使用 WAL 模式提升并发性能
PRAGMA journal_mode = WAL;

-- 优化缓存大小（10MB）
PRAGMA cache_size = -10000;

-- 同步模式（NORMAL 平衡性能和安全性）
PRAGMA synchronous = NORMAL;
