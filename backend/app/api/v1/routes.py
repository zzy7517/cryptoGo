"""
集中式路由定义
创建时间: 2025-10-29
更新时间: 2025-11-01（清理未使用的路由，保持精简）
"""
from fastapi import APIRouter
from . import session_handlers, agent_handlers, account_handlers

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

# GET /api/v1/session/{session_id}/asset-timeline - 获取资产变化时序数据
session_router.add_api_route(
    "/{session_id}/asset-timeline",
    session_handlers.get_asset_timeline,
    methods=["GET"],
    summary="获取会话的资产变化时序数据"
)


# ============================================
# Agent 路由
# ============================================
agent_router = APIRouter(prefix="/agent", tags=["Agent"])

# POST /api/v1/agent/sessions/{session_id}/start-background - 启动后台Agent
# 注意：此端点已废弃（2025-11-02），Agent 现在由 session/start 接口自动启动
# 保留此端点仅供向后兼容或手动启动场景
agent_router.add_api_route(
    "/sessions/{session_id}/start-background",
    agent_handlers.start_background_agent,
    methods=["POST"],
    summary="[已废弃] 启动后台挂机 Agent（请使用 session/start 接口）",
    deprecated=True
)

# POST /api/v1/agent/sessions/{session_id}/stop-background - 停止后台Agent
# 注意：此端点被内部逻辑使用（会话结束、程序关闭时自动停止Agent）
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


# ============================================
# Account 路由（通用，自动根据配置使用对应交易所）
# ============================================
account_router = APIRouter(prefix="/account", tags=["account"])

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
api_v1_router.include_router(account_router)

