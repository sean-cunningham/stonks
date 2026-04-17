from __future__ import annotations

from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.enums import AppMode
from app.models.active_position import ActivePosition
from app.models.spy_scalper_candidate_event import SpyScalperCandidateEvent
from app.repositories.strategy_bot_state_repository import SPY_SCALPER_SLUG, StrategyBotStateRepository
from app.services.market_data.quote_cache import QuoteCache, QuoteTick
from app.strategies.spy_0dte_scalper.ai_filter import run_ai_filter_sync
from app.strategies.spy_0dte_scalper.config import ScalperEffectiveConfig, effective_config
from app.strategies.spy_0dte_scalper.contract_selector import select_contract
from app.strategies.spy_0dte_scalper.features import compute_features, synthesize_bars
from app.strategies.spy_0dte_scalper.risk_manager import evaluate_new_entry
from app.strategies.spy_0dte_scalper.setup_detector import DetectedSetup, OR_CONT
from app.strategies.spy_0dte_scalper.state import ScalperRuntimeState
from app.strategies.spy_0dte_scalper.strategy import run_spy_scalper_tick


def _scalper_cfg_for_tests() -> ScalperEffectiveConfig:
    return ScalperEffectiveConfig(
        paper_only=True,
        reserve_cash=1000.0,
        deployable_target=4000.0,
        max_trades_per_day=15,
        max_consecutive_losses=3,
        pre_ai_min_score=60.0,
        ai_max_calls_per_day=30,
        delta_min=0.45,
        delta_max=0.60,
        premium_target_min=150.0,
        premium_target_max=250.0,
        premium_hard_max=300.0,
        max_hold_minutes=8.0,
        fast_fail_minutes=3.0,
        cooldown_after_exit_seconds=60,
        cooldown_after_fast_loser_seconds=120,
        daily_hard_stop_loss=500.0,
        daily_soft_stop_loss=300.0,
        limit_offset_from_mid=0.02,
        cancel_window_seconds=45,
        slippage_bps=8.0,
    )


def test_effective_config_forces_paper_when_global_flag(monkeypatch):
    monkeypatch.setenv("SPY_SCALPER_PAPER_ONLY", "true")
    get_settings.cache_clear()
    s = get_settings()
    cfg = effective_config(s, {"paper_only": False})
    assert cfg.paper_only is True


def test_contract_selector_returns_delta_band():
    s = get_settings()
    cfg = effective_config(s, None)
    leg = select_contract(500.0, "call", cfg)
    assert leg is not None
    assert cfg.delta_min <= leg.delta <= cfg.delta_max
    assert leg.mid <= cfg.premium_hard_max


def test_features_and_scorer_pipeline():
    bars = synthesize_bars(500.0, n=90, seed=42)
    f = compute_features(500.0, bars)
    assert "vwap" in f and "time_bucket" in f


def test_risk_manager_blocks_open_position():
    s = get_settings()
    cfg = effective_config(s, None)
    rt = ScalperRuntimeState.from_json(None, "2099-01-01", cfg.deployable_target)
    d = evaluate_new_entry(cfg, rt, trades_today=0, daily_net_pnl=0.0, setup_family=OR_CONT, has_open_position=True)
    assert d.ok is False


def test_ai_filter_mock_respects_daily_cap(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "use_mock_openai", True)
    monkeypatch.setattr(s, "openai_enable_real_calls", False)
    cfg = ScalperEffectiveConfig(**{**_scalper_cfg_for_tests().__dict__, "ai_max_calls_per_day": 0})
    setup = DetectedSetup(family=OR_CONT, direction="call")
    adj, verdict, err = run_ai_filter_sync(s, cfg, setup, 80.0, {"mid": 500}, ai_calls_today=0)
    assert err == "ai_daily_cap"
    assert verdict is None
    assert adj == 0.0


def test_ai_filter_provider_guard_blocks_disabled_provider(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "ai_provider", "xai")
    monkeypatch.setattr(s, "openai_enabled", True)
    cfg = _scalper_cfg_for_tests()
    setup = DetectedSetup(family=OR_CONT, direction="call")
    adj, verdict, err = run_ai_filter_sync(s, cfg, setup, 75.0, {"mid": 500}, ai_calls_today=0)
    assert adj == 0.0
    assert verdict is None
    assert err is not None
    assert "disabled for v1 runtime" in err


def test_ai_filter_handles_empty_openai_output(monkeypatch):
    import app.strategies.spy_0dte_scalper.ai_filter as ai_filter_module

    class _Resp:
        def raise_for_status(self):
            return None

        def json(self):
            return {"output": [{"type": "message", "content": []}]}

    class _Client:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def post(self, url, headers=None, json=None):
            return _Resp()

    s = get_settings()
    monkeypatch.setattr(s, "ai_provider", "openai")
    monkeypatch.setattr(s, "openai_enabled", True)
    monkeypatch.setattr(s, "use_mock_openai", False)
    monkeypatch.setattr(s, "openai_enable_real_calls", True)
    monkeypatch.setattr(s, "openai_api_key", "test-key")
    monkeypatch.setattr(ai_filter_module.httpx, "Client", _Client)
    cfg = _scalper_cfg_for_tests()
    setup = DetectedSetup(family=OR_CONT, direction="put")
    adj, verdict, err = run_ai_filter_sync(s, cfg, setup, 76.0, {"mid": 500}, ai_calls_today=0)
    assert adj == 0.0
    assert verdict is None
    assert err == "empty_ai_output"


def test_spy_scalper_blocks_synthetic_path_in_market_data_mode(db_session, monkeypatch):
    monkeypatch.setenv("APP_MODE", "market_data")
    monkeypatch.setenv("TASTYTRADE_REFRESH_TOKEN", "test-refresh")
    monkeypatch.setenv("TASTYTRADE_ACCOUNT_NUMBER", "123456")
    monkeypatch.setenv("TASTYTRADE_OAUTH_CLIENT_ID", "id")
    monkeypatch.setenv("TASTYTRADE_OAUTH_CLIENT_SECRET", "secret")
    get_settings.cache_clear()
    s = get_settings()
    assert s.app_mode == AppMode.MARKET_DATA
    qc = QuoteCache()
    strat = StrategyBotStateRepository(db_session)
    strat.set_state(SPY_SCALPER_SLUG, "running")
    run_spy_scalper_tick(db_session, s, qc)
    blocked = db_session.scalar(
        select(SpyScalperCandidateEvent).where(SpyScalperCandidateEvent.outcome == "blocked_synthetic_execution"),
    )
    assert blocked is not None
    get_settings.cache_clear()


def test_scalper_tick_does_not_touch_strategy1_positions(db_session, monkeypatch):
    monkeypatch.setenv("APP_MODE", "mock")
    qc = QuoteCache()
    qc.update(QuoteTick(symbol="SPY", bid=499.0, ask=501.0, last=500.0))
    strat = StrategyBotStateRepository(db_session)
    strat.set_state(SPY_SCALPER_SLUG, "running")
    before = db_session.scalar(select(func.count()).select_from(ActivePosition)) or 0
    run_spy_scalper_tick(db_session, get_settings(), qc)
    after = db_session.scalar(select(func.count()).select_from(ActivePosition)) or 0
    assert after == before
    cand = db_session.scalar(select(func.count()).select_from(SpyScalperCandidateEvent)) or 0
    assert cand >= 1
