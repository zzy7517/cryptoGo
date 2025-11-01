"""
集中式路由定义
创建时间: 2025-10-29
更新时间: 2025-11-01（使用通用 account_handlers）
"""
from fastapi import APIRouter
from . import session_handlers, agent_handlers, market_handlers, account_handlers

# 创建 v1 API 路由器
api_v1_router = APIRouter(prefix="/api/v1")


# ============================================
# Session 路由
# ============================================
session_router = APIRouter(prefix="/session", tags=["session"])

# POST /api/v1/session/start - 开始新的交易会话
session_router.add_api_route(
    "/start",
    session_handlers.start_session,
    methods=["POST"],
    summary="开始新的交易会话"
)

# POST /api/v1/session/end - 结束交易会话
session_router.add_api_route(
    "/end",
    session_handlers.end_session,
    methods=["POST"],
    summary="结束交易会话"
)

# GET /api/v1/session/active - 获取当前活跃会话
session_router.add_api_route(
    "/active",
    session_handlers.get_active_session,
    methods=["GET"],
    summary="获取当前活跃的交易会话"
)

# GET /api/v1/session/list - 获取会话列表
session_router.add_api_route(
    "/list",
    session_handlers.get_session_list,
    methods=["GET"],
    summary="获取交易会话列表"
)

# GET /api/v1/session/{session_id} - 获取会话详情
session_router.add_api_route(
    "/{session_id}",
    session_handlers.get_session_details,
    methods=["GET"],
    summary="获取会话详细信息"
)

# GET /api/v1/session/{session_id}/ai-decisions - 获取AI决策记录
session_router.add_api_route(
    "/{session_id}/ai-decisions",
    session_handlers.get_ai_decisions,
    methods=["GET"],
    summary="获取会话的AI决策记录"
)


# ============================================
# Agent 路由
# ============================================
agent_router = APIRouter(prefix="/agent", tags=["Agent"])

# POST /api/v1/agent/sessions/{session_id}/run-once - 运行一次决策
agent_router.add_api_route(
    "/sessions/{session_id}/run-once",
    agent_handlers.run_agent_once,
    methods=["POST"],
    summary="运行一次决策周期（单次执行）",
    response_model=agent_handlers.RunAgentResponse
)

# POST /api/v1/agent/sessions/{session_id}/start-background - 启动后台Agent
agent_router.add_api_route(
    "/sessions/{session_id}/start-background",
    agent_handlers.start_background_agent,
    methods=["POST"],
    summary="启动后台挂机 Agent"
)

# POST /api/v1/agent/sessions/{session_id}/stop-background - 停止后台Agent
agent_router.add_api_route(
    "/sessions/{session_id}/stop-background",
    agent_handlers.stop_background_agent,
    methods=["POST"],
    summary="停止后台 Agent"
)

# GET /api/v1/agent/sessions/{session_id}/background-status - 获取后台Agent状态
agent_router.add_api_route(
    "/sessions/{session_id}/background-status",
    agent_handlers.get_background_status,
    methods=["GET"],
    summary="获取后台 Agent 状态"
)

# GET /api/v1/agent/background-agents/list - 列出所有后台Agent
agent_router.add_api_route(
    "/background-agents/list",
    agent_handlers.list_background_agents,
    methods=["GET"],
    summary="列出所有后台运行的 Agent"
)

# POST /api/v1/agent/test - 测试Agent
agent_router.add_api_route(
    "/test",
    agent_handlers.test_agent,
    methods=["POST"],
    summary="测试 Agent（单次运行，不需要真实会话）"
)


# ============================================
# Market 路由
# ============================================
market_router = APIRouter(prefix="/market", tags=["market"])

# GET /api/v1/market/klines - 获取K线数据
market_router.add_api_route(
    "/klines",
    market_handlers.get_klines,
    methods=["GET"],
    summary="获取K线数据",
    response_model=market_handlers.KlineResponse
)

# GET /api/v1/market/ticker - 获取实时行情
market_router.add_api_route(
    "/ticker",
    market_handlers.get_ticker,
    methods=["GET"],
    summary="获取实时行情数据",
    response_model=market_handlers.TickerData
)

# GET /api/v1/market/symbols - 获取交易对列表
market_router.add_api_route(
    "/symbols",
    market_handlers.get_symbols,
    methods=["GET"],
    summary="获取交易对列表",
    response_model=market_handlers.SymbolListResponse
)

# GET /api/v1/market/funding-rate - 获取资金费率
market_router.add_api_route(
    "/funding-rate",
    market_handlers.get_funding_rate,
    methods=["GET"],
    summary="获取资金费率（仅限合约市场）",
    response_model=market_handlers.FundingRateData
)

# GET /api/v1/market/open-interest - 获取持仓量
market_router.add_api_route(
    "/open-interest",
    market_handlers.get_open_interest,
    methods=["GET"],
    summary="获取持仓量（仅限合约市场）",
    response_model=market_handlers.OpenInterestData
)

# GET /api/v1/market/indicators - 获取技术指标
market_router.add_api_route(
    "/indicators",
    market_handlers.get_indicators,
    methods=["GET"],
    summary="获取技术指标",
    response_model=market_handlers.IndicatorsResponse
)


# ============================================
# Account 路由（通用，自动根据配置使用对应交易所）
# ============================================
account_router = APIRouter(prefix="/account", tags=["account"])

# GET /api/v1/account/info - 获取账户信息
account_router.add_api_route(
    "/info",
    account_handlers.get_account_info,
    methods=["GET"],
    summary="获取账户信息（自动根据配置使用对应交易所）"
)

# GET /api/v1/account/positions - 获取持仓信息
account_router.add_api_route(
    "/positions",
    account_handlers.get_positions,
    methods=["GET"],
    summary="获取持仓信息（自动根据配置使用对应交易所）"
)

# GET /api/v1/account/summary - 获取账户摘要
account_router.add_api_route(
    "/summary",
    account_handlers.get_account_summary,
    methods=["GET"],
    summary="获取账户摘要（账户+持仓，自动根据配置使用对应交易所）"
)


# ============================================
# 注册所有子路由到 v1 router
# ============================================
api_v1_router.include_router(session_router)
api_v1_router.include_router(agent_router)
api_v1_router.include_router(market_router)
api_v1_router.include_router(account_router)

