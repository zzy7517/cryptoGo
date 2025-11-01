-- CryptoGo 数据库表结构 V3
-- 在 Supabase SQL Editor 中执行此脚本
-- 本脚本会删除现有表并重新创建
--
-- 更新日志 V3 (2025-11-01):
-- 1. 修改 trades 表，优化为完整交易周期记录（只在平仓时创建）
-- 2. 新增字段：entry_price, exit_price, entry_fee, exit_fee, total_fees
-- 3. 新增字段：entry_order_id, exit_order_id
-- 4. 修改 side 约束：只允许 'long' 和 'short'（移除 'buy' 和 'sell'）
-- 5. 修改 pnl 为 NOT NULL（已平仓的交易必须有盈亏）
-- 6. 新增索引：idx_trade_entry_time, idx_trade_exit_time

-- ============================================
-- 清理现有表（按依赖关系倒序删除）
-- ============================================

DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS ai_decisions CASCADE;
DROP TABLE IF EXISTS trading_sessions CASCADE;

-- 删除现有的触发器函数（如果存在）
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;


-- ============================================
-- 1. 交易会话表（核心表）
-- ============================================

CREATE TABLE trading_sessions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    
    -- 基本信息
    session_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'stopped', 'crashed', 'completed')),
    
    -- 初始状态
    initial_capital NUMERIC(20, 4),
    current_capital NUMERIC(20, 4),
    
    -- 最终统计（会话结束时计算）
    final_capital NUMERIC(20, 4),
    total_pnl NUMERIC(20, 4),
    total_return_pct NUMERIC(10, 4),
    
    -- 交易统计
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    
    -- 后台交易运行状态
    background_status VARCHAR(20) DEFAULT 'idle' CHECK (background_status IN ('idle', 'starting', 'running', 'stopping', 'stopped', 'crashed')),
    background_started_at TIMESTAMPTZ,
    background_stopped_at TIMESTAMPTZ,
    last_decision_time TIMESTAMPTZ,
    decision_count INTEGER DEFAULT 0,
    decision_interval INTEGER DEFAULT 180,
    trading_symbols TEXT[],
    last_error TEXT,
    trading_params JSONB,
    
    -- 配置信息
    config JSONB,
    
    -- 备注
    notes TEXT
);

-- 索引
CREATE INDEX idx_session_status ON trading_sessions(status);
CREATE INDEX idx_session_created ON trading_sessions(created_at DESC);

-- 注释
COMMENT ON TABLE trading_sessions IS '交易会话表 - 记录每次运行实例';
COMMENT ON COLUMN trading_sessions.session_name IS '会话名称（可选）';
COMMENT ON COLUMN trading_sessions.status IS '会话状态: running, stopped, crashed, completed';
COMMENT ON COLUMN trading_sessions.initial_capital IS '初始资金';
COMMENT ON COLUMN trading_sessions.current_capital IS '当前资金（实时更新）';
COMMENT ON COLUMN trading_sessions.final_capital IS '最终资金';
COMMENT ON COLUMN trading_sessions.total_pnl IS '总盈亏';
COMMENT ON COLUMN trading_sessions.total_return_pct IS '总收益率 (%)';
COMMENT ON COLUMN trading_sessions.background_status IS '后台运行状态: idle, starting, running, stopping, stopped, crashed';
COMMENT ON COLUMN trading_sessions.background_started_at IS '后台启动时间';
COMMENT ON COLUMN trading_sessions.background_stopped_at IS '后台停止时间';
COMMENT ON COLUMN trading_sessions.last_decision_time IS '最后决策时间';
COMMENT ON COLUMN trading_sessions.decision_count IS '决策执行次数';
COMMENT ON COLUMN trading_sessions.decision_interval IS '决策间隔（秒）';
COMMENT ON COLUMN trading_sessions.trading_symbols IS '交易对列表';
COMMENT ON COLUMN trading_sessions.last_error IS '最后的错误信息';
COMMENT ON COLUMN trading_sessions.trading_params IS '交易参数（JSON格式，包含 risk_params 等）';
COMMENT ON COLUMN trading_sessions.config IS '运行配置（JSON格式）';


-- ============================================
-- 2. AI 决策记录表
-- ============================================

CREATE TABLE ai_decisions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- 关联会话
    session_id BIGINT REFERENCES trading_sessions(id) ON DELETE CASCADE,
    
    -- 决策信息
    symbols TEXT[],
    decision_type VARCHAR(20) CHECK (decision_type IN ('buy', 'sell', 'hold', 'rebalance', 'close')),
    confidence NUMERIC(5, 4),
    
    -- AI 输入/输出（TEXT类型无长度限制，可存储完整内容）
    prompt_data JSONB,
    ai_response TEXT,
    reasoning TEXT,
    
    -- 建议的交易参数
    suggested_actions JSONB,
    
    -- 执行情况
    executed BOOLEAN DEFAULT FALSE,
    execution_result JSONB
);

-- 索引
CREATE INDEX idx_decision_session ON ai_decisions(session_id);
CREATE INDEX idx_decision_created_at ON ai_decisions(created_at);
CREATE INDEX idx_decision_executed ON ai_decisions(executed);

-- 注释
COMMENT ON TABLE ai_decisions IS 'AI 决策记录表';
COMMENT ON COLUMN ai_decisions.session_id IS '所属交易会话ID';
COMMENT ON COLUMN ai_decisions.symbols IS '分析的币种列表';
COMMENT ON COLUMN ai_decisions.decision_type IS '决策类型: buy, sell, hold, rebalance, close';
COMMENT ON COLUMN ai_decisions.confidence IS '置信度 (0-1)';
COMMENT ON COLUMN ai_decisions.prompt_data IS '给AI的完整prompt数据（JSON格式）';
COMMENT ON COLUMN ai_decisions.ai_response IS 'AI的原始回复';
COMMENT ON COLUMN ai_decisions.reasoning IS 'AI的推理过程';
COMMENT ON COLUMN ai_decisions.suggested_actions IS '建议的具体操作（JSON格式）';
COMMENT ON COLUMN ai_decisions.executed IS '是否已执行';
COMMENT ON COLUMN ai_decisions.execution_result IS '执行结果（JSON格式）';


-- ============================================
-- 3. 交易记录表
-- ============================================

CREATE TABLE trades (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- 关联会话
    session_id BIGINT REFERENCES trading_sessions(id) ON DELETE CASCADE,

    -- 交易信息
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    order_type VARCHAR(20) CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit')),

    -- 数量和价格
    quantity NUMERIC(20, 8) NOT NULL,
    entry_price NUMERIC(20, 4) NOT NULL,
    exit_price NUMERIC(20, 4),
    price NUMERIC(20, 4) NOT NULL,  -- 向后兼容字段（等同于 entry_price）
    total_value NUMERIC(20, 4) NOT NULL,
    leverage INTEGER DEFAULT 1,

    -- 名义价值（用于杠杆交易）
    notional_entry NUMERIC(20, 4),
    notional_exit NUMERIC(20, 4),

    -- 时间信息（用于计算持仓时长）
    entry_time TIMESTAMPTZ,
    exit_time TIMESTAMPTZ,
    holding_duration INTERVAL,

    -- 费用
    entry_fee NUMERIC(20, 8),
    exit_fee NUMERIC(20, 8),
    total_fees NUMERIC(20, 8),
    fee NUMERIC(20, 8),  -- 向后兼容字段
    fee_currency VARCHAR(10),

    -- 盈亏（平仓时计算）
    pnl NUMERIC(20, 4) NOT NULL,
    pnl_pct NUMERIC(10, 4),

    -- 关联
    ai_decision_id BIGINT,
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

-- 注释
COMMENT ON TABLE trades IS '交易记录表 - 只在平仓时创建记录，记录完整交易周期';
COMMENT ON COLUMN trades.session_id IS '所属交易会话ID';
COMMENT ON COLUMN trades.symbol IS '交易对符号';
COMMENT ON COLUMN trades.side IS '持仓方向: long(多头), short(空头)';
COMMENT ON COLUMN trades.order_type IS '订单类型: market, limit, stop, stop_limit';
COMMENT ON COLUMN trades.quantity IS '交易数量';
COMMENT ON COLUMN trades.entry_price IS '开仓价格';
COMMENT ON COLUMN trades.exit_price IS '平仓价格';
COMMENT ON COLUMN trades.price IS '成交价格（向后兼容，等同于entry_price）';
COMMENT ON COLUMN trades.total_value IS '总价值';
COMMENT ON COLUMN trades.leverage IS '使用的杠杆倍数';
COMMENT ON COLUMN trades.notional_entry IS '开仓名义价值';
COMMENT ON COLUMN trades.notional_exit IS '平仓名义价值';
COMMENT ON COLUMN trades.entry_time IS '开仓时间';
COMMENT ON COLUMN trades.exit_time IS '平仓时间';
COMMENT ON COLUMN trades.holding_duration IS '持仓时长';
COMMENT ON COLUMN trades.entry_fee IS '开仓手续费';
COMMENT ON COLUMN trades.exit_fee IS '平仓手续费';
COMMENT ON COLUMN trades.total_fees IS '总手续费（entry_fee + exit_fee）';
COMMENT ON COLUMN trades.fee IS '手续费（向后兼容）';
COMMENT ON COLUMN trades.fee_currency IS '手续费币种';
COMMENT ON COLUMN trades.pnl IS '净盈亏金额（扣除手续费）';
COMMENT ON COLUMN trades.pnl_pct IS '盈亏百分比';
COMMENT ON COLUMN trades.ai_decision_id IS '关联的AI决策ID';
COMMENT ON COLUMN trades.entry_order_id IS '开仓订单ID';
COMMENT ON COLUMN trades.exit_order_id IS '平仓订单ID';
COMMENT ON COLUMN trades.exchange_order_id IS '交易所订单ID（向后兼容）';


-- ============================================
-- 触发器和函数
-- ============================================
-- 注意: positions 表已移除，持仓信息直接从交易所API获取


-- ============================================
-- 初始数据（可选）
-- ============================================

-- 可以在这里插入一些测试数据或默认配置
-- 例如：创建一个默认的测试会话
-- INSERT INTO trading_sessions (session_name, initial_capital, status) 
-- VALUES ('Test Session', 100000, 'running');

