from pydantic import BaseModel


class ParameterExperimentRead(BaseModel):
    id: int
    experiment_name: str
    parameters_json: dict
    outcome_summary: str
    metrics_json: dict | None
    created_at: str


class TradeReviewRead(BaseModel):
    id: int
    created_at: str
    approved_trade_id: int
    candidate_trade_id: int | None
    active_position_id: int | None
    event_analysis_id: int | None
    symbol: str
    setup_type: str | None
    setup_score: float | None
    confirmation_state: str | None
    event_id: str | None
    event_type: str | None
    trade_family: str
    entry_price: float
    exit_price: float | None
    exit_reason: str | None
    quantity: int
    realized_pnl_dollars: float
    realized_r_multiple: float | None
    mfe_dollars: float | None
    mae_dollars: float | None
    holding_seconds: int | None
    hit_plus_1r: bool
    hit_plus_1_5r: bool
    hit_plus_2r: bool
    rule_adherence_ok: bool
    had_x_enrichment: bool
    had_thenewsapi_supplement: bool
    reason_codes_snapshot: list | None
    exit_quality_label: str | None
    exit_quality_explanation: str | None
    shadow_experiments: list[ParameterExperimentRead] = []


class RecommendationRead(BaseModel):
    id: int
    created_at: str
    status: str
    title: str
    evidence_summary: str
    confidence: float
    affected_scope: dict
    suggested_parameter_delta: dict | None
    trade_review_id: int | None


class AnalyticsSummaryResponse(BaseModel):
    overall: dict
    exit_quality: dict[str, int]
    top_reason_codes: list[dict]
    anticipatory_vs_confirmed: dict[str, dict]
    governance_note: str


class SetupSliceResponse(BaseModel):
    setups: list[dict]


class SymbolSliceResponse(BaseModel):
    symbols: list[dict]


class AnalyticsCompactBlock(BaseModel):
    trade_review_count: int
    overall_win_rate: float
    overall_expectancy_usd: float
    avg_realized_r: float | None
    exit_quality_top: list[dict]
    setup_expectancy_preview: list[dict]
    governance_note: str
