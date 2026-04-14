from enum import StrEnum


class AppMode(StrEnum):
    MOCK = "mock"
    MARKET_DATA = "market_data"
    FULL_ANALYSIS = "full_analysis"


class BotRunState(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"


class StrategyType(StrEnum):
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    DEBIT_SPREAD = "debit_spread"
    CREDIT_SPREAD = "credit_spread"


class CandidateKind(StrEnum):
    BULLISH_CONTINUATION = "bullish_continuation"
    BEARISH_CONTINUATION = "bearish_continuation"
    BULLISH_POST_EVENT = "bullish_post_event"
    BEARISH_POST_EVENT = "bearish_post_event"
    RANGE_CREDIT_SPREAD = "range_credit_spread"


class DirectionBias(StrEnum):
    LONG = "long"
    SHORT = "short"
    NEUTRAL = "neutral"


class PositionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class TradeApprovalStatus(StrEnum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"
