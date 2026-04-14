export interface BotStateRead {
  state: string;
  pause_reason: string | null;
  cooldown_until: string | null;
}

export interface BalancesRead {
  cash: number;
  in_trades: number;
  total: number;
  currency: string;
}

export interface ActivePositionRead {
  id: number;
  symbol: string;
  strategy: string;
  status: string;
  quantity: number;
  average_entry_price: number;
  market_value: number | null;
  unrealized_pnl: number | null;
  initial_stop_price: number | null;
  emergency_premium_stop_pct: number | null;
  current_trailing_stop: number | null;
  breakeven_armed: boolean;
  partial_exit_taken: boolean;
  partial_exit_qty: number;
  thesis_expires_at: string | null;
  high_water_mark_price?: number | null;
  low_water_mark_price?: number | null;
  reached_1r?: boolean;
  reached_1_5r?: boolean;
  reached_2r?: boolean;
  opened_at: string;
  closed_at: string | null;
  legs: unknown[];
}

export interface ApprovedTradeRead {
  id: number;
  candidate_trade_id: number;
  event_analysis_id: number | null;
  status: string;
  created_at: string;
  risk_snapshot: Record<string, unknown> | null;
  policy_trace: Record<string, unknown> | null;
}

export interface FillRead {
  id: number;
  active_position_id: number;
  side: string;
  quantity: number;
  price: number;
  fee: number;
  is_partial: boolean;
  created_at: string;
}

export interface EventAnalysisRead {
  id: number;
  symbol: string;
  event_type: string;
  event_source_tier: string;
  materiality_score: number;
  surprise_score: number;
  direction_bias: string;
  confidence_score: number;
  time_horizon: string;
  priced_in_risk: string;
  narrative_summary: string;
  key_evidence_points: string[];
  tradeability_flag: boolean;
  recommended_strategy: string;
  validation_ok: boolean;
  escalation_used: boolean;
  setup_score: number | null;
  reason_codes: string[] | null;
  created_at: string;
}

export interface CandidateTradeRead {
  id: number;
  symbol: string;
  strategy: string;
  candidate_kind: string;
  direction_bias: string;
  legs: unknown[];
  is_event_driven: boolean;
  setup_type: string | null;
  setup_score: number | null;
  reason_codes: string[] | null;
  confirmation_state: string | null;
  event_id: string | null;
  event_analysis_id: number | null;
  created_at: string;
  notes: string | null;
}

export interface RejectedTradeRead {
  id: number;
  candidate_trade_id: number | null;
  event_analysis_id: number | null;
  reasons: string[];
  rule_codes: string[];
  detail: string | null;
  created_at: string;
}

export interface XEnrichmentRead {
  id: number;
  symbol: string;
  provider: string;
  model_name: string;
  sentiment_bias: string;
  acceleration_flag: boolean;
  rumor_risk_flag: boolean;
  confidence_score: number;
  summary: string;
  evidence_points: string[];
  event_analysis_id: number | null;
  candidate_trade_id: number | null;
  created_at: string;
}

export interface AnalyticsCompactBlock {
  trade_review_count: number;
  overall_win_rate: number;
  overall_expectancy_usd: number;
  avg_realized_r: number | null;
  exit_quality_top: { label: string; count: number }[];
  setup_expectancy_preview: { setup_type: string; expectancy: number; n: number }[];
  governance_note: string;
}

export interface StatusResponse {
  bot: BotStateRead;
  balances: BalancesRead;
  active_positions: ActivePositionRead[];
  recent_trades: ApprovedTradeRead[];
  recent_fills: FillRead[];
  recent_event_analyses: EventAnalysisRead[];
  recent_x_enrichments: XEnrichmentRead[];
  recent_candidates: CandidateTradeRead[];
  recent_rejections: RejectedTradeRead[];
  latest_account_snapshot_at: string | null;
  realized_pnl: number;
  unrealized_pnl: number;
  analytics_compact: AnalyticsCompactBlock;
}

export interface AnalyticsSummaryResponse {
  overall: Record<string, unknown>;
  exit_quality: Record<string, number>;
  top_reason_codes: { reason_code: string; count: number }[];
  anticipatory_vs_confirmed: Record<string, Record<string, unknown>>;
  governance_note: string;
}

export interface SetupSliceResponse {
  setups: Record<string, unknown>[];
}

export interface RecommendationRead {
  id: number;
  created_at: string;
  status: string;
  title: string;
  evidence_summary: string;
  confidence: number;
  affected_scope: Record<string, unknown>;
  suggested_parameter_delta: Record<string, unknown> | null;
  trade_review_id: number | null;
}

export interface ParameterExperimentRead {
  id: number;
  experiment_name: string;
  parameters_json: Record<string, unknown>;
  outcome_summary: string;
  metrics_json: Record<string, unknown> | null;
  created_at: string;
}

export interface TradeReviewRead {
  id: number;
  created_at: string;
  approved_trade_id: number;
  candidate_trade_id: number | null;
  active_position_id: number | null;
  event_analysis_id: number | null;
  symbol: string;
  setup_type: string | null;
  setup_score: number | null;
  confirmation_state: string | null;
  event_id: string | null;
  event_type: string | null;
  trade_family: string;
  entry_price: number;
  exit_price: number | null;
  exit_reason: string | null;
  quantity: number;
  realized_pnl_dollars: number;
  realized_r_multiple: number | null;
  mfe_dollars: number | null;
  mae_dollars: number | null;
  holding_seconds: number | null;
  hit_plus_1r: boolean;
  hit_plus_1_5r: boolean;
  hit_plus_2r: boolean;
  rule_adherence_ok: boolean;
  had_x_enrichment: boolean;
  had_thenewsapi_supplement: boolean;
  reason_codes_snapshot: string[] | null;
  exit_quality_label: string | null;
  exit_quality_explanation: string | null;
  shadow_experiments: ParameterExperimentRead[];
}

export interface DashboardBundle {
  status: StatusResponse;
  analyticsSummary: AnalyticsSummaryResponse;
  setups: SetupSliceResponse;
  recommendations: RecommendationRead[];
}
