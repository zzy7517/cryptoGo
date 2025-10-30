"""
Pydantic Schemas
用于 API 请求和响应的数据验证和序列化
创建时间: 2025-10-29
"""

# Market schemas
from .market import (
    KlineData,
    KlineResponse,
    TickerData,
    SymbolInfo,
    SymbolListResponse,
    FundingRateData,
    OpenInterestData,
    IndicatorLatestValues,
    IndicatorSeriesData,
    IndicatorsResponse,
)

# Agent schemas
from .agent import (
    RunAgentRequest,
    RunAgentResponse,
    ToolUsage,
    BackgroundAgentStatus,
    StartBackgroundAgentRequest,
    StartBackgroundAgentResponse,
    StopBackgroundAgentResponse,
    BackgroundAgentListItem,
)

# Session schemas
from .session import (
    SessionConfig,
    StartSessionRequest,
    EndSessionRequest,
    SessionBase,
    SessionBasic,
    SessionDetail,
    SessionWithAgentStatus,
    StartSessionResponse,
    EndSessionResponse,
    SessionListResponse,
    SessionDetailResponse,
    CreateSnapshotRequest,
    SnapshotResponse,
)

# Trade schemas
from .trade import (
    TradeBase,
    TradeDetail,
    CreateTradeRequest,
    TradeListResponse,
    TradeDetailResponse,
    TradeStatistics,
)

# Position schemas
from .position import (
    PositionBase,
    PositionDetail,
    CreatePositionRequest,
    UpdatePositionRequest,
    ClosePositionRequest,
    PositionListResponse,
    PositionDetailResponse,
    PositionSummary,
)

# AI Decision schemas
from .ai_decision import (
    AIDecisionBase,
    AIDecisionDetail,
    CreateAIDecisionRequest,
    UpdateAIDecisionRequest,
    AIDecisionListResponse,
    AIDecisionDetailResponse,
    AIDecisionStatistics,
    SuggestedAction,
)

# Account Snapshot schemas
from .account_snapshot import (
    AccountSnapshotBase,
    AccountSnapshotDetail,
    CreateSnapshotRequest as CreateAccountSnapshotRequest,
    SnapshotListResponse,
    SnapshotDetailResponse,
    EquityCurvePoint,
    EquityCurveResponse,
    PerformanceMetrics,
)

__all__ = [
    # Market
    "KlineData",
    "KlineResponse",
    "TickerData",
    "SymbolInfo",
    "SymbolListResponse",
    "FundingRateData",
    "OpenInterestData",
    "IndicatorLatestValues",
    "IndicatorSeriesData",
    "IndicatorsResponse",
    # Agent
    "RunAgentRequest",
    "RunAgentResponse",
    "ToolUsage",
    "BackgroundAgentStatus",
    "StartBackgroundAgentRequest",
    "StartBackgroundAgentResponse",
    "StopBackgroundAgentResponse",
    "BackgroundAgentListItem",
    # Session
    "SessionConfig",
    "StartSessionRequest",
    "EndSessionRequest",
    "SessionBase",
    "SessionBasic",
    "SessionDetail",
    "SessionWithAgentStatus",
    "StartSessionResponse",
    "EndSessionResponse",
    "SessionListResponse",
    "SessionDetailResponse",
    "CreateSnapshotRequest",
    "SnapshotResponse",
    # Trade
    "TradeBase",
    "TradeDetail",
    "CreateTradeRequest",
    "TradeListResponse",
    "TradeDetailResponse",
    "TradeStatistics",
    # Position
    "PositionBase",
    "PositionDetail",
    "CreatePositionRequest",
    "UpdatePositionRequest",
    "ClosePositionRequest",
    "PositionListResponse",
    "PositionDetailResponse",
    "PositionSummary",
    # AI Decision
    "AIDecisionBase",
    "AIDecisionDetail",
    "CreateAIDecisionRequest",
    "UpdateAIDecisionRequest",
    "AIDecisionListResponse",
    "AIDecisionDetailResponse",
    "AIDecisionStatistics",
    "SuggestedAction",
    # Account Snapshot
    "AccountSnapshotBase",
    "AccountSnapshotDetail",
    "CreateAccountSnapshotRequest",
    "SnapshotListResponse",
    "SnapshotDetailResponse",
    "EquityCurvePoint",
    "EquityCurveResponse",
    "PerformanceMetrics",
]

