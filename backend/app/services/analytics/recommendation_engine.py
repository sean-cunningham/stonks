"""Generate human-review recommendation rows from trade statistics (never auto-applied)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.recommendation_item import RecommendationItem
from app.repositories.recommendation_repository import RecommendationRepository
from app.services.analytics.analytics_engine import (
    load_all_reviews,
    summarize_by_setup,
    summarize_global,
)


def _exists_similar(db: Session, title: str) -> bool:
    repo = RecommendationRepository(db)
    for row in repo.list_by_status(limit=200):
        if row.title == title and row.status == "suggested_for_review":
            return True
    return False


def refresh_recommendations(db: Session) -> int:
    """Evaluate aggregates and insert new suggestion rows; returns count added."""
    reviews = load_all_reviews(db)
    if not reviews:
        return 0
    repo = RecommendationRepository(db)
    added = 0
    glob = summarize_global(reviews)
    n = glob["trade_count"]
    if n >= 5 and glob["win_rate"] < 0.35:
        title = "Low win rate across recent completed trades"
        if not _exists_similar(db, title):
            repo.create(
                RecommendationItem(
                    created_at=utc_now(),
                    status="suggested_for_review",
                    title=title,
                    evidence_summary=(
                        f"Observed win rate {glob['win_rate']:.2%} over {n} trades; "
                        "review setup filters, confirmation gates, and risk sizing offline."
                    ),
                    confidence=min(0.95, 0.5 + (0.35 - glob["win_rate"])),
                    affected_scope={"scope": "global"},
                    suggested_parameter_delta={"action": "review_policy_and_replay", "metric": "win_rate"},
                )
            )
            added += 1

    for row in summarize_by_setup(reviews):
        if row["trade_count"] < 4:
            continue
        if row["expectancy"] < 0 and row["win_rate"] < 0.4:
            title = f"Setup underperformance: {row['setup_type']}"
            if not _exists_similar(db, title):
                repo.create(
                    RecommendationItem(
                        created_at=utc_now(),
                        status="suggested_for_review",
                        title=title,
                        evidence_summary=(
                            f"Setup {row['setup_type']}: expectancy {row['expectancy']:.2f} USD/trade "
                            f"across {row['trade_count']} trades; consider stricter scoring or different event mix."
                        ),
                        confidence=0.55,
                        affected_scope={"scope": "setup_type", "setup_type": row["setup_type"]},
                        suggested_parameter_delta={"setup_min_score_delta": 5, "note": "hypothesis only"},
                    )
                )
                added += 1

    if n >= 6 and glob["late_loss_rate"] > 0.25:
        title = "Elevated stop-after-MFE pattern"
        if not _exists_similar(db, title):
            repo.create(
                RecommendationItem(
                    created_at=utc_now(),
                    status="suggested_for_review",
                    title=title,
                    evidence_summary=(
                        f"{glob['late_loss_rate']:.0%} of trades flagged stop-after-favorable-excursion; "
                        "review stop width vs. volatility and event risk (no live change from this signal alone)."
                    ),
                    confidence=0.5,
                    affected_scope={"scope": "risk_management"},
                    suggested_parameter_delta={"initial_stop_widen_pct": 10, "validate_in_replay": True},
                )
            )
            added += 1

    enrich_wins = sum(1 for r in reviews if r.had_x_enrichment and r.realized_pnl_dollars > 0)
    enrich_n = sum(1 for r in reviews if r.had_x_enrichment)
    plain_wins = sum(1 for r in reviews if not r.had_x_enrichment and r.realized_pnl_dollars > 0)
    plain_n = sum(1 for r in reviews if not r.had_x_enrichment)
    if enrich_n >= 4 and plain_n >= 4:
        ew = enrich_wins / enrich_n
        pw = plain_wins / plain_n
        if ew > pw + 0.15:
            title = "xAI enrichment correlates with better outcomes in sample"
            if not _exists_similar(db, title):
                repo.create(
                    RecommendationItem(
                        created_at=utc_now(),
                        status="suggested_for_review",
                        title=title,
                        evidence_summary=(
                            f"Win rate with enrichment {ew:.2%} vs without {pw:.2%} on this sample; "
                            "could inform optional gating — confirm with larger N and paper replay."
                        ),
                        confidence=0.45,
                        affected_scope={"scope": "enrichment", "provider": "xai"},
                        suggested_parameter_delta={"note": "Do not auto-tighten filters from correlation alone."},
                    )
                )
                added += 1

    return added
