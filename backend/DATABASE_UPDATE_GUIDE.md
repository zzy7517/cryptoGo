# 数据库更新指南

## Schema V3 更新 (2025-11-01)

### 主要变更

本次更新优化了 `trades` 表的设计，改为只在平仓时创建完整的交易记录。

#### 核心改进：
1. **开仓时不创建数据库记录** - 持仓信息从交易所 API 实时获取
2. **平仓时创建完整记录** - 包含完整的交易周期数据（entry/exit/fees/pnl）
3. **支持分批平仓** - 每次平仓创建一条独立记录

### 新增字段

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `entry_price` | NUMERIC(20, 4) | 开仓价格 |
| `exit_price` | NUMERIC(20, 4) | 平仓价格 |
| `entry_fee` | NUMERIC(20, 8) | 开仓手续费 |
| `exit_fee` | NUMERIC(20, 8) | 平仓手续费 |
| `total_fees` | NUMERIC(20, 8) | 总手续费 |
| `entry_order_id` | VARCHAR(100) | 开仓订单ID |
| `exit_order_id` | VARCHAR(100) | 平仓订单ID |

### 修改约束

- `side` 字段：只允许 `'long'` 和 `'short'`（移除 `'buy'` 和 `'sell'`）
- `pnl` 字段：设置为 `NOT NULL`（已平仓的交易必须有盈亏）

### 新增索引

```sql
CREATE INDEX idx_trade_entry_time ON trades(entry_time);
CREATE INDEX idx_trade_exit_time ON trades(exit_time);
```

---

## 更新步骤

### ⚠️ 注意事项

**此更新会删除所有现有数据！请在更新前备份重要数据。**

如果你需要保留现有数据，请不要执行此脚本。

### 方法 1: 使用 psql 命令行

```bash
# 1. 连接到数据库
psql -U your_username -d your_database

# 2. 执行 schema 脚本
\i /path/to/backend/schema.sql

# 3. 验证表结构
\d trades

# 4. 退出
\q
```

### 方法 2: 使用 Supabase SQL Editor

1. 登录 Supabase Dashboard
2. 进入 SQL Editor
3. 复制 `backend/schema.sql` 的全部内容
4. 粘贴到 SQL Editor 中
5. 点击 "Run" 执行

### 方法 3: 使用数据库管理工具

如果使用 pgAdmin、DBeaver 等工具：

1. 打开 `backend/schema.sql` 文件
2. 复制全部内容
3. 在查询窗口中粘贴并执行

---

## 验证更新

执行以下 SQL 验证表结构是否正确：

```sql
-- 查看 trades 表结构
\d trades

-- 验证新字段存在
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'trades'
AND column_name IN ('entry_price', 'exit_price', 'entry_fee', 'exit_fee', 'total_fees', 'entry_order_id', 'exit_order_id');

-- 验证约束
SELECT constraint_name, check_clause
FROM information_schema.check_constraints
WHERE constraint_name = 'trades_side_check';

-- 验证索引
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'trades'
AND indexname IN ('idx_trade_entry_time', 'idx_trade_exit_time');
```

---

## 应用层更新

数据库更新后，请确保后端服务已更新到对应版本：

1. ✅ 后端代码已更新（使用新的字段结构）
2. ✅ 前端展示已更新（显示完整的交易数据）
3. ✅ 交易逻辑已更新（开仓不记录，平仓才记录）

---

## 回滚

如果需要回滚到 V2 版本，请使用 Git 恢复旧版本：

```bash
git checkout <previous-commit> backend/schema.sql
```

然后重新执行旧版本的 schema.sql。

**注意：回滚会删除所有现有数据。**

---

## 问题排查

### 问题 1: 外键约束错误

如果遇到 `foreign key constraint` 错误，请确保按照脚本顺序删除表：
1. trades
2. ai_decisions
3. trading_sessions

### 问题 2: 权限不足

如果遇到权限错误，请使用具有 `DROP TABLE` 和 `CREATE TABLE` 权限的用户。

### 问题 3: 连接超时

如果数据库连接超时，请检查：
- 数据库服务是否正常运行
- 防火墙设置是否正确
- 连接字符串是否正确

---

## 支持

如有问题，请查看：
- 项目 README
- 代码提交记录
- 相关 Issue

