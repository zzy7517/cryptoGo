-- CryptoGo 数据库表结构 V2
-- 在 Supabase SQL Editor 中执行此脚本
-- 本脚本会删除现有表并重新创建

-- ============================================
-- 清理现有表（按依赖关系倒序删除）
-- ============================================

DROP TABLE IF EXISTS trades CASCADE;
DROP TABLE IF EXISTS positions CASCADE;
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
    
    -- 最终统计（会话结束时计算）
    final_capital NUMERIC(20, 4),
    total_pnl NUMERIC(20, 4),
    total_return_pct NUMERIC(10, 4),
    
    -- 交易统计
    total_trades INTEGER DEFAULT 0,
    winning_trades INTEGER DEFAULT 0,
    losing_trades INTEGER DEFAULT 0,
    
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
COMMENT ON COLUMN trading_sessions.final_capital IS '最终资金';
COMMENT ON COLUMN trading_sessions.total_pnl IS '总盈亏';
COMMENT ON COLUMN trading_sessions.total_return_pct IS '总收益率 (%)';
COMMENT ON COLUMN trading_sessions.config IS '运行配置（JSON格式）';


-- ============================================
-- 2. 持仓记录表
-- ============================================

CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- 关联会话
    session_id BIGINT REFERENCES trading_sessions(id) ON DELETE CASCADE,
    
    -- 基本信息
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('long', 'short')),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'closed')),
    
    -- 持仓详情
    quantity NUMERIC(20, 8) NOT NULL,
    entry_price NUMERIC(20, 4) NOT NULL,
    current_price NUMERIC(20, 4),
    liquidation_price NUMERIC(20, 4),
    leverage INTEGER DEFAULT 1,
    margin NUMERIC(20, 4),
    
    -- 时间信息
    entry_time TIMESTAMPTZ,
    exit_time TIMESTAMPTZ,
    holding_duration INTERVAL,
    
    -- 盈亏
    unrealized_pnl NUMERIC(20, 4),
    realized_pnl NUMERIC(20, 4),
    
    -- 风控
    stop_loss NUMERIC(20, 4),
    take_profit NUMERIC(20, 4),
    
    -- 关联信息
    entry_order_id BIGINT,
    exit_order_id BIGINT,
    ai_decision_id BIGINT
);

-- 索引
CREATE INDEX idx_position_session ON positions(session_id);
CREATE INDEX idx_position_symbol_status ON positions(symbol, status);
CREATE INDEX idx_position_created_at ON positions(created_at);
CREATE INDEX idx_position_status ON positions(status);

-- 注释
COMMENT ON TABLE positions IS '持仓记录表';
COMMENT ON COLUMN positions.session_id IS '所属交易会话ID';
COMMENT ON COLUMN positions.symbol IS '交易对符号（如 BTCUSDT）';
COMMENT ON COLUMN positions.side IS '持仓方向: long, short';
COMMENT ON COLUMN positions.status IS '状态: active, closed';
COMMENT ON COLUMN positions.quantity IS '持仓数量';
COMMENT ON COLUMN positions.entry_price IS '入场价格';
COMMENT ON COLUMN positions.current_price IS '当前价格';
COMMENT ON COLUMN positions.liquidation_price IS '强平价格';
COMMENT ON COLUMN positions.leverage IS '杠杆倍数';
COMMENT ON COLUMN positions.margin IS '保证金金额';
COMMENT ON COLUMN positions.entry_time IS '开仓时间';
COMMENT ON COLUMN positions.exit_time IS '平仓时间';
COMMENT ON COLUMN positions.holding_duration IS '持仓时长';
COMMENT ON COLUMN positions.unrealized_pnl IS '未实现盈亏';
COMMENT ON COLUMN positions.realized_pnl IS '已实现盈亏';
COMMENT ON COLUMN positions.stop_loss IS '止损价';
COMMENT ON COLUMN positions.take_profit IS '止盈价';


-- ============================================
-- 3. AI 决策记录表
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
    
    -- AI 输入/输出
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
-- 4. 交易记录表
-- ============================================

CREATE TABLE trades (
    id BIGSERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- 关联会话
    session_id BIGINT REFERENCES trading_sessions(id) ON DELETE CASCADE,
    
    -- 交易信息
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL CHECK (side IN ('buy', 'sell', 'long', 'short')),
    order_type VARCHAR(20) CHECK (order_type IN ('market', 'limit', 'stop', 'stop_limit')),
    
    -- 数量和价格
    quantity NUMERIC(20, 8) NOT NULL,
    price NUMERIC(20, 4) NOT NULL,
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
    fee NUMERIC(20, 8),
    fee_currency VARCHAR(10),
    
    -- 盈亏（仅平仓时）
    pnl NUMERIC(20, 4),
    pnl_pct NUMERIC(10, 4),
    
    -- 关联
    position_id BIGINT,
    ai_decision_id BIGINT,
    exchange_order_id VARCHAR(100)
);

-- 索引
CREATE INDEX idx_trade_session ON trades(session_id);
CREATE INDEX idx_trade_symbol_created ON trades(symbol, created_at);
CREATE INDEX idx_trade_position_id ON trades(position_id);
CREATE INDEX idx_trade_created_at ON trades(created_at);

-- 注释
COMMENT ON TABLE trades IS '交易记录表';
COMMENT ON COLUMN trades.session_id IS '所属交易会话ID';
COMMENT ON COLUMN trades.symbol IS '交易对符号';
COMMENT ON COLUMN trades.side IS '方向: buy, sell, long, short';
COMMENT ON COLUMN trades.order_type IS '订单类型: market, limit, stop, stop_limit';
COMMENT ON COLUMN trades.quantity IS '交易数量';
COMMENT ON COLUMN trades.price IS '成交价格';
COMMENT ON COLUMN trades.total_value IS '总价值';
COMMENT ON COLUMN trades.leverage IS '使用的杠杆倍数';
COMMENT ON COLUMN trades.notional_entry IS '名义入场价值';
COMMENT ON COLUMN trades.notional_exit IS '名义出场价值';
COMMENT ON COLUMN trades.entry_time IS '开仓时间';
COMMENT ON COLUMN trades.exit_time IS '平仓时间';
COMMENT ON COLUMN trades.holding_duration IS '持仓时长（仅已平仓交易）';
COMMENT ON COLUMN trades.fee IS '手续费';
COMMENT ON COLUMN trades.fee_currency IS '手续费币种';
COMMENT ON COLUMN trades.pnl IS '盈亏金额';
COMMENT ON COLUMN trades.pnl_pct IS '盈亏百分比';
COMMENT ON COLUMN trades.position_id IS '关联的持仓ID';
COMMENT ON COLUMN trades.ai_decision_id IS '关联的AI决策ID';
COMMENT ON COLUMN trades.exchange_order_id IS '交易所订单ID';


-- ============================================
-- 触发器和函数
-- ============================================

-- 创建更新时间自动更新触发器函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

-- 应用触发器到 positions 表
CREATE TRIGGER update_positions_updated_at 
    BEFORE UPDATE ON positions
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================
-- 初始数据（可选）
-- ============================================

-- 可以在这里插入一些测试数据或默认配置
-- 例如：创建一个默认的测试会话
-- INSERT INTO trading_sessions (session_name, initial_capital, status) 
-- VALUES ('Test Session', 100000, 'running');

