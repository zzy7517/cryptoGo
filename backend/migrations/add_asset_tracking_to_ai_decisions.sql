-- 数据库迁移脚本
-- 功能：在 ai_decisions 表添加资产追踪字段
-- 日期：2025-11-03
-- 说明：用于追踪每次AI决策时的账户余额、浮动盈亏和总资产

-- 添加账户余额字段
ALTER TABLE ai_decisions
ADD COLUMN IF NOT EXISTS account_balance NUMERIC(20, 4);

-- 添加浮动盈亏字段
ALTER TABLE ai_decisions
ADD COLUMN IF NOT EXISTS unrealized_pnl NUMERIC(20, 4);

-- 添加总资产字段
ALTER TABLE ai_decisions
ADD COLUMN IF NOT EXISTS total_asset NUMERIC(20, 4);

-- 添加字段注释
COMMENT ON COLUMN ai_decisions.account_balance IS '决策时的账户总余额';
COMMENT ON COLUMN ai_decisions.unrealized_pnl IS '决策时的浮动盈亏（未实现盈亏）';
COMMENT ON COLUMN ai_decisions.total_asset IS '决策时的总资产（余额 + 浮动盈亏）';

-- 验证字段是否添加成功
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ai_decisions'
  AND column_name IN ('account_balance', 'unrealized_pnl', 'total_asset');

