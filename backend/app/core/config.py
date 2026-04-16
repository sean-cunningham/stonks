from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.enums import AppMode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_mode: AppMode = Field(default=AppMode.MOCK, validation_alias="APP_MODE")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    database_url: str = Field(
        default="sqlite:///./stonks.db",
        validation_alias="DATABASE_URL",
    )
    backend_host: str = Field(default="0.0.0.0", validation_alias="BACKEND_HOST")
    backend_port: int = Field(default=8000, validation_alias="BACKEND_PORT")
    frontend_origin: str = Field(
        default="http://localhost:5173",
        validation_alias="FRONTEND_ORIGIN",
    )

    bot_default_starting_cash: float = Field(
        default=2000.0,
        validation_alias="BOT_DEFAULT_STARTING_CASH",
    )
    bot_default_max_risk_per_trade_pct: float = Field(
        default=1.0,
        validation_alias="BOT_DEFAULT_MAX_RISK_PER_TRADE_PCT",
    )
    bot_default_max_daily_loss_pct: float = Field(
        default=5.0,
        validation_alias="BOT_DEFAULT_MAX_DAILY_LOSS_PCT",
    )
    bot_default_max_weekly_loss_pct: float = Field(
        default=8.0,
        validation_alias="BOT_DEFAULT_MAX_WEEKLY_LOSS_PCT",
    )
    bot_default_max_open_positions: int = Field(
        default=2,
        validation_alias="BOT_DEFAULT_MAX_OPEN_POSITIONS",
    )
    bot_default_max_open_positions_per_symbol: int = Field(
        default=1,
        validation_alias="BOT_DEFAULT_MAX_OPEN_POSITIONS_PER_SYMBOL",
    )
    bot_default_approved_universe: str = Field(
        default="SPY,QQQ,IWM,XLF,XLK,TLT,SLV",
        validation_alias="BOT_DEFAULT_APPROVED_UNIVERSE",
    )
    paper_normal_risk_tier_pct: float = Field(
        default=1.0,
        validation_alias="PAPER_NORMAL_RISK_TIER_PCT",
    )
    paper_strong_risk_tier_pct: float = Field(
        default=1.5,
        validation_alias="PAPER_STRONG_RISK_TIER_PCT",
    )
    paper_max_risk_tier_pct: float = Field(
        default=2.0,
        validation_alias="PAPER_MAX_RISK_TIER_PCT",
    )
    paper_max_combined_open_risk_pct: float = Field(
        default=3.0,
        validation_alias="PAPER_MAX_COMBINED_OPEN_RISK_PCT",
    )
    paper_daily_drawdown_stop_pct: float = Field(
        default=5.0,
        validation_alias="PAPER_DAILY_DRAWDOWN_STOP_PCT",
    )
    paper_stop_new_entries_after_losses: int = Field(
        default=3,
        validation_alias="PAPER_STOP_NEW_ENTRIES_AFTER_LOSSES",
    )
    paper_recommendation_max_per_day: int = Field(
        default=3,
        validation_alias="PAPER_RECOMMENDATION_MAX_PER_DAY",
    )
    paper_recommendation_max_per_symbol_per_day: int = Field(
        default=1,
        validation_alias="PAPER_RECOMMENDATION_MAX_PER_SYMBOL_PER_DAY",
    )
    bot_no_new_trades_minutes_before_close: int = Field(
        default=30,
        validation_alias="BOT_NO_NEW_TRADES_MINUTES_BEFORE_CLOSE",
    )
    bot_loss_cooldown_minutes: int = Field(
        default=0,
        validation_alias="BOT_LOSS_COOLDOWN_MINUTES",
    )
    enable_range_credit_spread: bool = Field(
        default=False,
        validation_alias="ENABLE_RANGE_CREDIT_SPREAD",
    )

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    openai_api_base_url: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="OPENAI_API_BASE_URL",
    )
    openai_triage_model: str = Field(
        default="gpt-5.4-mini",
        validation_alias="OPENAI_TRIAGE_MODEL",
    )
    openai_escalation_model: str = Field(
        default="gpt-5.4",
        validation_alias="OPENAI_ESCALATION_MODEL",
    )
    openai_request_timeout_seconds: float = Field(
        default=120.0,
        validation_alias="OPENAI_REQUEST_TIMEOUT_SECONDS",
    )
    openai_enable_real_calls: bool = Field(
        default=False,
        validation_alias="OPENAI_ENABLE_REAL_CALLS",
    )
    use_mock_openai: bool = Field(default=True, validation_alias="USE_MOCK_OPENAI")

    xai_api_key: str | None = Field(default=None, validation_alias="XAI_API_KEY")
    xai_api_base_url: str = Field(
        default="https://api.x.ai/v1",
        validation_alias="XAI_API_BASE_URL",
    )
    xai_request_timeout_seconds: float = Field(
        default=120.0,
        validation_alias="XAI_REQUEST_TIMEOUT_SECONDS",
    )
    xai_enable_real_calls: bool = Field(default=False, validation_alias="XAI_ENABLE_REAL_CALLS")
    xai_enrichment_model: str = Field(
        default="grok-4.1-fast",
        validation_alias="XAI_ENRICHMENT_MODEL",
    )
    xai_enable_x_search_enrichment: bool = Field(
        default=False,
        validation_alias="XAI_ENABLE_X_SEARCH_ENRICHMENT",
    )
    v1_disable_xai_runtime: bool = Field(
        default=True,
        validation_alias="V1_DISABLE_XAI_RUNTIME",
    )
    xai_enrichment_max_calls_per_day: int = Field(
        default=25,
        validation_alias="XAI_ENRICHMENT_MAX_CALLS_PER_DAY",
    )
    xai_enrichment_min_materiality_score: int = Field(
        default=60,
        validation_alias="XAI_ENRICHMENT_MIN_MATERIALITY_SCORE",
    )
    xai_enrichment_symbol_allowlist: str = Field(
        default="SPY,QQQ,IWM,NVDA,TSLA,AAPL,AMZN,META,AMD,SMCI",
        validation_alias="XAI_ENRICHMENT_SYMBOL_ALLOWLIST",
    )
    xai_enrichment_event_types: str = Field(
        default="earnings,sec_filing,macro_announcement,headline,guidance_change,transcript,other",
        validation_alias="XAI_ENRICHMENT_EVENT_TYPES",
    )
    use_mock_xai: bool = Field(default=True, validation_alias="USE_MOCK_XAI")

    tastytrade_api_base_url: str = Field(
        default="https://api.tastytrade.com",
        validation_alias="TASTYTRADE_API_BASE_URL",
    )
    tastytrade_dx_url: str = Field(
        default="wss://feed.dxfeed.com/dxlink-ws",
        validation_alias="TASTYTRADE_DX_URL",
    )
    tastytrade_oauth_client_id: str | None = Field(
        default=None,
        validation_alias="TASTYTRADE_OAUTH_CLIENT_ID",
    )
    tastytrade_oauth_client_secret: str | None = Field(
        default=None,
        validation_alias="TASTYTRADE_OAUTH_CLIENT_SECRET",
    )
    tastytrade_oauth_redirect_uri: str | None = Field(
        default=None,
        validation_alias="TASTYTRADE_OAUTH_REDIRECT_URI",
    )
    tastytrade_refresh_token: str | None = Field(
        default=None,
        validation_alias="TASTYTRADE_REFRESH_TOKEN",
    )
    tastytrade_account_number: str | None = Field(
        default=None,
        validation_alias="TASTYTRADE_ACCOUNT_NUMBER",
    )
    tastytrade_use_sandbox: bool = Field(
        default=False,
        validation_alias="TASTYTRADE_USE_SANDBOX",
    )

    use_mock_events: bool = Field(default=True, validation_alias="USE_MOCK_EVENTS")
    news_provider: str = Field(default="mock", validation_alias="NEWS_PROVIDER")
    news_api_key: str | None = Field(default=None, validation_alias="NEWS_API_KEY")
    thenewsapi_api_key: str | None = Field(default=None, validation_alias="THENEWSAPI_API_KEY")
    thenewsapi_enable_real_calls: bool = Field(
        default=False,
        validation_alias="THENEWSAPI_ENABLE_REAL_CALLS",
    )
    thenewsapi_request_limit_per_day: int = Field(
        default=100,
        validation_alias="THENEWSAPI_REQUEST_LIMIT_PER_DAY",
    )
    sec_user_agent: str = Field(
        default="StonksPaperBot/1.0",
        validation_alias="SEC_USER_AGENT",
    )

    paper_slippage_bps: float = Field(default=5.0, validation_alias="PAPER_SLIPPAGE_BPS")
    paper_partial_fill_max_fraction: float = Field(
        default=0.5,
        validation_alias="PAPER_PARTIAL_FILL_MAX_FRACTION",
    )
    paper_fee_per_contract: float = Field(
        default=0.0,
        validation_alias="PAPER_FEE_PER_CONTRACT",
    )

    spy_scalper_paper_only: bool = Field(default=True, validation_alias="SPY_SCALPER_PAPER_ONLY")
    spy_scalper_job_interval_seconds: int = Field(
        default=60,
        validation_alias="SPY_SCALPER_JOB_INTERVAL_SECONDS",
    )
    spy_scalper_recon_interval_seconds: int = Field(
        default=60,
        validation_alias="SPY_SCALPER_RECON_INTERVAL_SECONDS",
    )
    spy_scalper_reserve_cash: float = Field(default=1000.0, validation_alias="SPY_SCALPER_RESERVE_CASH")
    spy_scalper_deployable_target: float = Field(
        default=4000.0,
        validation_alias="SPY_SCALPER_DEPLOYABLE_TARGET",
    )
    spy_scalper_max_trades_per_day: int = Field(default=15, validation_alias="SPY_SCALPER_MAX_TRADES_PER_DAY")
    spy_scalper_max_consecutive_losses: int = Field(
        default=3,
        validation_alias="SPY_SCALPER_MAX_CONSECUTIVE_LOSSES",
    )
    spy_scalper_pre_ai_min_score: float = Field(default=60.0, validation_alias="SPY_SCALPER_PRE_AI_MIN_SCORE")
    spy_scalper_ai_max_calls_per_day: int = Field(
        default=30,
        validation_alias="SPY_SCALPER_AI_MAX_CALLS_PER_DAY",
    )
    spy_scalper_contract_delta_min: float = Field(default=0.45, validation_alias="SPY_SCALPER_CONTRACT_DELTA_MIN")
    spy_scalper_contract_delta_max: float = Field(default=0.60, validation_alias="SPY_SCALPER_CONTRACT_DELTA_MAX")
    spy_scalper_premium_target_min: float = Field(
        default=150.0,
        validation_alias="SPY_SCALPER_PREMIUM_TARGET_MIN",
    )
    spy_scalper_premium_target_max: float = Field(
        default=250.0,
        validation_alias="SPY_SCALPER_PREMIUM_TARGET_MAX",
    )
    spy_scalper_premium_hard_max: float = Field(default=300.0, validation_alias="SPY_SCALPER_PREMIUM_HARD_MAX")
    spy_scalper_max_hold_minutes: float = Field(default=8.0, validation_alias="SPY_SCALPER_MAX_HOLD_MINUTES")
    spy_scalper_fast_fail_minutes: float = Field(default=3.0, validation_alias="SPY_SCALPER_FAST_FAIL_MINUTES")
    spy_scalper_cooldown_after_exit_seconds: int = Field(
        default=60,
        validation_alias="SPY_SCALPER_COOLDOWN_AFTER_EXIT_SECONDS",
    )
    spy_scalper_cooldown_after_fast_loser_seconds: int = Field(
        default=120,
        validation_alias="SPY_SCALPER_COOLDOWN_AFTER_FAST_LOSER_SECONDS",
    )
    spy_scalper_daily_hard_stop_loss: float = Field(
        default=500.0,
        validation_alias="SPY_SCALPER_DAILY_HARD_STOP_LOSS",
    )
    spy_scalper_daily_soft_stop_loss: float = Field(
        default=300.0,
        validation_alias="SPY_SCALPER_DAILY_SOFT_STOP_LOSS",
    )
    spy_scalper_limit_offset_from_mid: float = Field(
        default=0.02,
        validation_alias="SPY_SCALPER_LIMIT_OFFSET_FROM_MID",
    )
    spy_scalper_cancel_window_seconds: int = Field(
        default=45,
        validation_alias="SPY_SCALPER_CANCEL_WINDOW_SECONDS",
    )
    spy_scalper_slippage_bps: float = Field(default=8.0, validation_alias="SPY_SCALPER_SLIPPAGE_BPS")

    def validate_mode_requirements(self) -> None:
        if self.app_mode == AppMode.MOCK:
            return
        if self.app_mode in (AppMode.MARKET_DATA, AppMode.FULL_ANALYSIS):
            missing = []
            if not self.tastytrade_refresh_token:
                missing.append("TASTYTRADE_REFRESH_TOKEN")
            if not self.tastytrade_account_number:
                missing.append("TASTYTRADE_ACCOUNT_NUMBER")
            if not self.tastytrade_oauth_client_id:
                missing.append("TASTYTRADE_OAUTH_CLIENT_ID")
            if not self.tastytrade_oauth_client_secret:
                missing.append("TASTYTRADE_OAUTH_CLIENT_SECRET")
            if missing:
                msg = (
                    f"APP_MODE={self.app_mode} requires broker credentials: "
                    + ", ".join(missing)
                )
                raise RuntimeError(msg)
        if self.app_mode == AppMode.FULL_ANALYSIS:
            if not self.openai_api_key:
                raise RuntimeError("APP_MODE=full_analysis requires OPENAI_API_KEY")
            if self.use_mock_openai:
                raise RuntimeError("APP_MODE=full_analysis requires USE_MOCK_OPENAI=false")
            if not self.openai_enable_real_calls:
                raise RuntimeError(
                    "APP_MODE=full_analysis requires OPENAI_ENABLE_REAL_CALLS=true"
                )


@lru_cache
def get_settings() -> Settings:
    return Settings()
