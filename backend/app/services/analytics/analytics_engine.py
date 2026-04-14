"""Aggregated post-trade metrics grouped by setup, symbol, and other dimensions."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.trade_review import TradeReview
from app.repositories.trade_review_repository import TradeReviewRepository


@dataclass
class GroupMetrics:
    trade_count: int
    win_rate: float
    avg_win: float
    avg_loss: float
    expectancy: float
    profit_factor: float
    avg_hold_seconds: float | None
    avg_mfe: float | None
    avg_mae: float | None
    avg_realized_r: float | None
    hit_1r_rate: float
    hit_1_5r_rate: float
    hit_2r_rate: float
    premature_exit_rate: float
    late_loss_rate: float


def _mean(xs: list[float]) -> float | None:
    return sum(xs) / len(xs) if xs else None


def _compute_metrics(rows: list[TradeReview]) -> GroupMetrics:
    n = len(rows)
    if n == 0:
        return GroupMetrics(
            trade_count=0,
            win_rate=0.0,
            avg_win=0.0,
            avg_loss=0.0,
            expectancy=0.0,
            profit_factor=0.0,
            avg_hold_seconds=None,
            avg_mfe=None,
            avg_mae=None,
            avg_realized_r=None,
            hit_1r_rate=0.0,
            hit_1_5r_rate=0.0,
            hit_2r_rate=0.0,
            premature_exit_rate=0.0,
            late_loss_rate=0.0,
        )
    wins = [r for r in rows if r.realized_pnl_dollars > 0]
    losses = [r for r in rows if r.realized_pnl_dollars < 0]
    win_rate = len(wins) / n
    avg_win = _mean([r.realized_pnl_dollars for r in wins]) or 0.0
    avg_loss = _mean([r.realized_pnl_dollars for r in losses]) or 0.0
    gross_win = sum(r.realized_pnl_dollars for r in wins)
    gross_loss = abs(sum(r.realized_pnl_dollars for r in losses))
    profit_factor = (gross_win / gross_loss) if gross_loss > 1e-9 else (gross_win if gross_win > 0 else 0.0)
    expectancy = sum(r.realized_pnl_dollars for r in rows) / n
    holds = [r.holding_seconds for r in rows if r.holding_seconds is not None]
    mfes = [r.mfe_dollars for r in rows if r.mfe_dollars is not None]
    maes = [r.mae_dollars for r in rows if r.mae_dollars is not None]
    rs = [r.realized_r_multiple for r in rows if r.realized_r_multiple is not None]
    hit_1r = sum(1 for r in rows if r.hit_plus_1r) / n
    hit_15 = sum(1 for r in rows if r.hit_plus_1_5r) / n
    hit_2 = sum(1 for r in rows if r.hit_plus_2r) / n
    premature = sum(
        1 for r in rows if r.exit_quality_label in ("small_win_pre_milestone", "gave_back_winner")
    ) / n
    late_loss = sum(1 for r in rows if r.exit_quality_label == "stop_after_favorable_excursion") / n
    return GroupMetrics(
        trade_count=n,
        win_rate=win_rate,
        avg_win=avg_win,
        avg_loss=avg_loss,
        expectancy=expectancy,
        profit_factor=profit_factor,
        avg_hold_seconds=_mean([float(h) for h in holds]) if holds else None,
        avg_mfe=_mean([float(x) for x in mfes]) if mfes else None,
        avg_mae=_mean([float(x) for x in maes]) if maes else None,
        avg_realized_r=_mean([float(x) for x in rs]) if rs else None,
        hit_1r_rate=hit_1r,
        hit_1_5r_rate=hit_15,
        hit_2r_rate=hit_2,
        premature_exit_rate=premature,
        late_loss_rate=late_loss,
    )


def _metrics_to_dict(m: GroupMetrics) -> dict:
    return {
        "trade_count": m.trade_count,
        "win_rate": m.win_rate,
        "avg_win": m.avg_win,
        "avg_loss": m.avg_loss,
        "expectancy": m.expectancy,
        "profit_factor": m.profit_factor,
        "avg_hold_seconds": m.avg_hold_seconds,
        "avg_mfe": m.avg_mfe,
        "avg_mae": m.avg_mae,
        "avg_realized_r": m.avg_realized_r,
        "hit_1r_rate": m.hit_1r_rate,
        "hit_1_5r_rate": m.hit_1_5r_rate,
        "hit_2r_rate": m.hit_2r_rate,
        "premature_exit_rate": m.premature_exit_rate,
        "late_loss_rate": m.late_loss_rate,
    }


def _group_by(rows: list[TradeReview], key_fn: Callable[[TradeReview], str]) -> dict[str, list[TradeReview]]:
    out: dict[str, list[TradeReview]] = defaultdict(list)
    for r in rows:
        out[key_fn(r)].append(r)
    return dict(out)


def load_all_reviews(db: Session, limit: int = 5000) -> list[TradeReview]:
    return TradeReviewRepository(db).list_recent(limit)


def summarize_global(rows: list[TradeReview]) -> dict:
    return _metrics_to_dict(_compute_metrics(rows))


def summarize_by_setup(rows: list[TradeReview]) -> list[dict]:
    groups = _group_by(rows, lambda r: r.setup_type or "unknown")
    out: list[dict] = []
    for k in sorted(groups.keys()):
        out.append({"setup_type": k, **_metrics_to_dict(_compute_metrics(groups[k]))})
    return out


def summarize_by_symbol(rows: list[TradeReview]) -> list[dict]:
    groups = _group_by(rows, lambda r: r.symbol)
    out: list[dict] = []
    for k in sorted(groups.keys()):
        out.append({"symbol": k, **_metrics_to_dict(_compute_metrics(groups[k]))})
    return out


def exit_quality_counts(rows: list[TradeReview]) -> dict[str, int]:
    c: dict[str, int] = defaultdict(int)
    for r in rows:
        lab = r.exit_quality_label or "unknown"
        c[lab] += 1
    return dict(c)


def top_reason_codes(rows: list[TradeReview], top_n: int = 8) -> list[dict]:
    c: dict[str, int] = defaultdict(int)
    for r in rows:
        for code in r.reason_codes_snapshot or []:
            c[str(code)] += 1
    ranked = sorted(c.items(), key=lambda x: -x[1])[:top_n]
    return [{"reason_code": k, "count": v} for k, v in ranked]


def anticipatory_vs_confirmed(rows: list[TradeReview]) -> dict[str, dict]:
    fams = _group_by(rows, lambda r: r.trade_family or "unknown")
    return {k: _metrics_to_dict(_compute_metrics(v)) for k, v in fams.items()}


def compact_summary_for_status(rows: list[TradeReview]) -> dict:
    g = _compute_metrics(rows)
    setups = summarize_by_setup(rows)
    return {
        "trade_review_count": g.trade_count,
        "overall_win_rate": g.win_rate,
        "overall_expectancy_usd": g.expectancy,
        "avg_realized_r": g.avg_realized_r,
        "exit_quality_top": [
            {"label": k, "count": v}
            for k, v in sorted(exit_quality_counts(rows).items(), key=lambda x: -x[1])[:5]
        ],
        "setup_expectancy_preview": [
            {"setup_type": s["setup_type"], "expectancy": s["expectancy"], "n": s["trade_count"]}
            for s in setups
            if s["trade_count"] > 0
        ][:6],
        "governance_note": "Analytics only — human review required before changing live rules.",
    }
