from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories.parameter_experiment_repository import ParameterExperimentRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.repositories.trade_review_repository import TradeReviewRepository
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    ParameterExperimentRead,
    RecommendationRead,
    SetupSliceResponse,
    SymbolSliceResponse,
    TradeReviewRead,
)
from app.services.analytics.analytics_engine import (
    anticipatory_vs_confirmed,
    compact_summary_for_status,
    exit_quality_counts,
    load_all_reviews,
    summarize_by_setup,
    summarize_by_symbol,
    summarize_global,
    top_reason_codes,
)
from app.services.analytics.recommendation_engine import refresh_recommendations

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _iso(dt) -> str:
    return dt.isoformat() if dt else ""


@router.get("/summary", response_model=AnalyticsSummaryResponse)
def analytics_summary(db: Session = Depends(get_db)) -> AnalyticsSummaryResponse:
    rows = load_all_reviews(db)
    return AnalyticsSummaryResponse(
        overall=summarize_global(rows),
        exit_quality=exit_quality_counts(rows),
        top_reason_codes=top_reason_codes(rows),
        anticipatory_vs_confirmed=anticipatory_vs_confirmed(rows),
        governance_note=(
            "Analytics-only learning layer: suggestions require human review; "
            "no autonomous live adaptation or self-rewriting strategy code."
        ),
    )


@router.get("/setups", response_model=SetupSliceResponse)
def analytics_setups(db: Session = Depends(get_db)) -> SetupSliceResponse:
    return SetupSliceResponse(setups=summarize_by_setup(load_all_reviews(db)))


@router.get("/symbols", response_model=SymbolSliceResponse)
def analytics_symbols(db: Session = Depends(get_db)) -> SymbolSliceResponse:
    return SymbolSliceResponse(symbols=summarize_by_symbol(load_all_reviews(db)))


@router.get("/recommendations", response_model=list[RecommendationRead])
def analytics_recommendations(
    refresh: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> list[RecommendationRead]:
    if refresh:
        refresh_recommendations(db)
    repo = RecommendationRepository(db)
    return [
        RecommendationRead(
            id=r.id,
            created_at=_iso(r.created_at),
            status=r.status,
            title=r.title,
            evidence_summary=r.evidence_summary,
            confidence=r.confidence,
            affected_scope=r.affected_scope,
            suggested_parameter_delta=r.suggested_parameter_delta,
            trade_review_id=r.trade_review_id,
        )
        for r in repo.list_by_status(limit=100)
    ]


@router.get("/trades/{trade_id}/review", response_model=TradeReviewRead)
def trade_review_detail(trade_id: int, db: Session = Depends(get_db)) -> TradeReviewRead:
    repo = TradeReviewRepository(db)
    row = repo.get_by_approved_trade_id(trade_id)
    if not row:
        raise HTTPException(status_code=404, detail="trade review not found for approved_trade_id")
    exp_repo = ParameterExperimentRepository(db)
    exps = exp_repo.list_for_review(row.id)
    return TradeReviewRead(
        id=row.id,
        created_at=_iso(row.created_at),
        approved_trade_id=row.approved_trade_id,
        candidate_trade_id=row.candidate_trade_id,
        active_position_id=row.active_position_id,
        event_analysis_id=row.event_analysis_id,
        symbol=row.symbol,
        setup_type=row.setup_type,
        setup_score=row.setup_score,
        confirmation_state=row.confirmation_state,
        event_id=row.event_id,
        event_type=row.event_type,
        trade_family=row.trade_family,
        entry_price=row.entry_price,
        exit_price=row.exit_price,
        exit_reason=row.exit_reason,
        quantity=row.quantity,
        realized_pnl_dollars=row.realized_pnl_dollars,
        realized_r_multiple=row.realized_r_multiple,
        mfe_dollars=row.mfe_dollars,
        mae_dollars=row.mae_dollars,
        holding_seconds=row.holding_seconds,
        hit_plus_1r=row.hit_plus_1r,
        hit_plus_1_5r=row.hit_plus_1_5r,
        hit_plus_2r=row.hit_plus_2r,
        rule_adherence_ok=row.rule_adherence_ok,
        had_x_enrichment=row.had_x_enrichment,
        had_thenewsapi_supplement=row.had_thenewsapi_supplement,
        reason_codes_snapshot=row.reason_codes_snapshot,
        exit_quality_label=row.exit_quality_label,
        exit_quality_explanation=row.exit_quality_explanation,
        shadow_experiments=[
            ParameterExperimentRead(
                id=e.id,
                experiment_name=e.experiment_name,
                parameters_json=e.parameters_json,
                outcome_summary=e.outcome_summary,
                metrics_json=e.metrics_json,
                created_at=_iso(e.created_at),
            )
            for e in exps
        ],
    )

