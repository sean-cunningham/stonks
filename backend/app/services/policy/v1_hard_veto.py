from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

from app.core.config import Settings
from app.core.enums import RegimeState
from app.models.account import Account
from app.models.active_position import ActivePosition
from app.models.candidate_trade import CandidateTrade
from app.models.event_analysis import EventAnalysis
from app.models.market_snapshot import MarketSnapshot
from app.services.strategy.v1_feature_engine import V1FeatureSet
from app.services.strategy.v1_strategy_rules import SetupEvaluation


APPROVED_UNIVERSE = {"SPY", "QQQ", "IWM", "XLF", "XLK", "TLT", "SLV"}


@dataclass
class VetoResult:
    ok: bool
    reasons: list[str]
    codes: list[str]


def _et_now(now: datetime) -> datetime:
    return now.astimezone(ZoneInfo("America/New_York"))


def _in_entry_windows(et: datetime) -> bool:
    t = et.time()
    return (time(9, 50) <= t <= time(11, 30)) or (time(13, 30) <= t <= time(15, 15))


def _force_flat_cutoff(et: datetime) -> bool:
    return et.time() >= time(15, 30)


def evaluate_hard_veto(
    *,
    now: datetime,
    candidate: CandidateTrade,
    snapshot: MarketSnapshot | None,
    event_row: EventAnalysis | None,
    account: Account,
    open_positions: list[ActivePosition],
    setup_eval: SetupEvaluation,
    features: V1FeatureSet | None,
    settings: Settings,
    losses_today: int,
    require_confirmation: bool,
) -> VetoResult:
    reasons: list[str] = []
    codes: list[str] = []

    def fail(code: str, reason: str) -> None:
        codes.append(code)
        reasons.append(reason)

    sym = candidate.symbol.upper()
    if sym not in APPROVED_UNIVERSE:
        fail("SYMBOL_NOT_APPROVED", "symbol not in approved v1 universe")
    et = _et_now(now)
    if not _in_entry_windows(et):
        fail("OUTSIDE_WINDOW", "outside entry window")
    if _force_flat_cutoff(et):
        fail("FORCE_FLAT_WINDOW", "new entries blocked after 15:30 ET")
    event_lockout = bool((snapshot.extra or {}).get("event_lockout_active", False))
    if event_lockout:
        fail("EVENT_LOCKOUT", "event lockout active")
    if features and features.regime == RegimeState.FREEZE:
        fail("FREEZE", "regime freeze active")
    if require_confirmation and snapshot:
        confirm_ratio = float((snapshot.extra or {}).get("trigger_volume_ratio", 1.0))
        hold_confirmed = bool((snapshot.extra or {}).get("hold_one_candle_confirmed", False))
        if confirm_ratio < 1.2 and not hold_confirmed:
            fail("ADVERSARIAL_CONFIRMATION", "adversarial agent requires stronger confirmation")
    if snapshot:
        quote_ts = float((snapshot.extra or {}).get("quote_ts_epoch", now.timestamp()))
        chain_ts = float((snapshot.extra or {}).get("chain_ts_epoch", now.timestamp()))
        if now.replace(tzinfo=UTC).timestamp() - quote_ts > 3.0:
            fail("QUOTE_STALE", "quote stale > 3 seconds")
        if now.replace(tzinfo=UTC).timestamp() - chain_ts > 10.0:
            fail("CHAIN_STALE", "option chain stale > 10 seconds")
        if bool((snapshot.extra or {}).get("api_degraded", False)):
            fail("API_DEGRADED", "broker/order API degraded")
    else:
        fail("NO_SNAPSHOT", "missing market snapshot")

    if not setup_eval.ok:
        fail("NO_VALID_SETUP", "no valid setup family")
    if setup_eval.stop_price is None:
        fail("NO_STOP", "no valid stop/invalidation")
    if setup_eval.r_to_target < 1.5:
        fail("RR_TOO_LOW", "reward to first target < 1.5R")

    option = (snapshot.extra or {}).get("option_contract", {}) if snapshot else {}
    dte = int(option.get("dte", 0))
    delta = abs(float(option.get("delta", 0.0)))
    spread_abs = float(option.get("spread_abs", 999.0))
    mid = float(option.get("mid", 0.01))
    spread_pct = spread_abs / max(mid, 1e-9)
    if spread_abs > min(0.08, 0.04 * max(mid, 0.01)):
        fail("OPTION_SPREAD_WIDE", "option spread too wide")
    if dte < 7 or dte > 14:
        fail("DTE_OUTSIDE_RANGE", "DTE outside allowed range")
    if delta < 0.50 or delta > 0.65:
        fail("DELTA_OUTSIDE_RANGE", "delta outside allowed range")
    if float(option.get("chain_activity_score", 0.0)) < 0.5:
        fail("CHAIN_INACTIVE", "option chain not active enough")

    # Exposure/risk guards.
    if losses_today >= 3:
        fail("DAILY_LOSS_COUNT", "3 losses already today")
    grade = float((candidate.setup_score or 0.0))
    if losses_today >= 2 and grade < 85.0:
        fail("LOSS_STREAK_GRADE", "2 losses today and setup is not A-grade")
    if len(open_positions) >= 2:
        fail("MAX_OPEN_POSITIONS", "max 2 open positions total")
    if any(p.symbol == sym and p.status == "open" for p in open_positions):
        fail("SYMBOL_ALREADY_OPEN", "max 1 open position per symbol")

    open_risk = sum(abs((p.average_entry_price - (p.initial_stop_price or p.average_entry_price * 0.95))) * 100 * p.quantity for p in open_positions)
    max_combined = account.equity * (settings.paper_max_combined_open_risk_pct / 100.0)
    if open_risk >= max_combined:
        fail("OPEN_RISK_LIMIT", "combined open risk limit exceeded")
    daily_dd_limit = account.equity * (settings.paper_daily_drawdown_stop_pct / 100.0)
    if account.realized_pnl <= -daily_dd_limit:
        fail("DAILY_STOP_HIT", "daily stop hit")
    return VetoResult(ok=len(codes) == 0, reasons=reasons, codes=codes)
