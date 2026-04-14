"""Rule-based, explainable exit-quality labels for post-trade review."""


def classify_exit(
    *,
    realized_pnl_dollars: float,
    mfe_dollars: float | None,
    mae_dollars: float | None,
    exit_reason: str | None,
    hit_plus_1r: bool,
    hit_plus_2r: bool,
) -> tuple[str, str]:
    if exit_reason == "thesis_expired":
        return (
            "thesis_expired_exit",
            "Position closed because the thesis expiry rule fired.",
        )
    if realized_pnl_dollars < 0:
        mfe = mfe_dollars or 0.0
        if mfe > abs(realized_pnl_dollars) * 0.35:
            return (
                "stop_after_favorable_excursion",
                "Price traded favorably (MFE) before the stop produced a loss; review stop placement and volatility.",
            )
        return (
            "adverse_stop_exit",
            "Loss exit with limited favorable excursion; stop likely behaved as a hard risk cap.",
        )
    if hit_plus_2r and mfe_dollars and mfe_dollars > 0 and realized_pnl_dollars < mfe_dollars * 0.35:
        return (
            "gave_back_winner",
            "MFE was materially larger than what was realized; trailing/partials may have given back gains.",
        )
    if hit_plus_1r or hit_plus_2r:
        return (
            "structured_win_exit",
            "Profitable exit after at least +1R was achieved; consistent with structured management.",
        )
    if realized_pnl_dollars > 0:
        return (
            "small_win_pre_milestone",
            "Positive P&L but +1R milestone was not recorded; review early exits vs. plan.",
        )
    return ("flat_exit", "Near-breakeven outcome; limited edge realization.")
