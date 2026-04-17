"""Local paper execution — default path; live adapter can mirror validation."""

import logging
import math
from typing import Any

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import Settings
from app.models.approved_trade import ApprovedTrade
from app.models.candidate_trade import CandidateTrade
from app.repositories.account_repository import AccountRepository
from app.services.execution.fill_engine import compute_open_fill
from app.services.execution.order_dry_run_interface import ValidationResult
from app.services.execution.order_validator import validate_spread_order

log = logging.getLogger(__name__)

# Single-leg option premium must be well below spot; catches underlying-as-premium bugs.
_MAX_OPTION_MID_VS_UNDERLYING = 0.35


def _f(x: Any) -> float | None:
    try:
        if x is None:
            return None
        v = float(x)
        if not math.isfinite(v) or v <= 0:
            return None
        return v
    except (TypeError, ValueError):
        return None


def _option_nbbo_for_fill(
    option_contract: dict[str, Any],
    *,
    strategy: str,
    reference_underlying: float | None,
) -> tuple[float, float, float] | None:
    """Derive option bid/ask/mid for fill pricing from metadata only (never underlying NBBO)."""
    if strategy == "debit_spread":
        mid = _f(option_contract.get("spread_mid")) or _f(option_contract.get("mid"))
        spread = _f(option_contract.get("spread_bid_ask")) or _f(option_contract.get("spread_abs"))
        if mid is None:
            return None
        half = max((spread or 0.08) / 2.0, 1e-4)
        return mid - half, mid + half, mid

    mid = _f(option_contract.get("mid"))
    if mid is None:
        return None
    spread = _f(option_contract.get("spread_abs")) or _f(option_contract.get("spread_bid_ask"))
    half = max((spread or 0.04) / 2.0, 1e-4)
    return mid - half, mid + half, mid


def _validate_option_fill(
    bid: float,
    ask: float,
    mid: float,
    *,
    reference_underlying: float | None,
) -> bool:
    if bid <= 0 or ask <= 0 or mid <= 0 or ask < bid:
        return False
    if reference_underlying and reference_underlying > 0 and mid >= reference_underlying * _MAX_OPTION_MID_VS_UNDERLYING:
        log.warning(
            "paper open rejected: option mid %.4f too large vs reference underlying %.4f (likely wrong price source)",
            mid,
            reference_underlying,
        )
        return False
    return True


class PaperBroker:
    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._acct = AccountRepository(db)

    def dry_run(self, order: dict[str, Any]) -> ValidationResult:
        return validate_spread_order(order)

    def execute_approved_open(
        self,
        approved: ApprovedTrade,
        *,
        bid: float | None,
        ask: float | None,
        mid: float | None,
        reference_underlying: float | None = None,
    ) -> int | None:
        cand = self._db.get(CandidateTrade, approved.candidate_trade_id)
        if not cand:
            return None
        option_contract = ((cand.metadata_json or {}).get("option_contract") or {})
        order = {"strategy": cand.strategy, "legs": cand.legs, "option_contract": option_contract}
        v = self.dry_run(order)
        if not v.ok:
            return None

        nbbo = _option_nbbo_for_fill(option_contract, strategy=cand.strategy, reference_underlying=reference_underlying)
        if nbbo is None:
            log.warning("paper open rejected: missing option_contract premium fields for candidate id=%s", cand.id)
            return None
        obid, oask, omid = nbbo
        if not _validate_option_fill(obid, oask, omid, reference_underlying=reference_underlying):
            log.warning("paper open rejected: invalid option NBBO for candidate id=%s", cand.id)
            return None

        qty = 1
        structure = "debit_spread" if cand.strategy == "debit_spread" else "single_leg"
        fr = compute_open_fill(
            side="buy",
            bid=obid,
            ask=oask,
            mid=omid,
            quantity=qty,
            slippage_bps=self._settings.paper_slippage_bps,
            partial_max_fraction=self._settings.paper_partial_fill_max_fraction,
            structure=structure,
        )
        fee = self._settings.paper_fee_per_contract * max(1, len(cand.legs))
        cost = fr.price * fr.quantity * 100 + fee
        acc = self._acct.ensure_primary(self._settings.bot_default_starting_cash)
        if acc.cash_balance < cost:
            return None
        acc.cash_balance -= cost
        acc.equity = acc.cash_balance + self._acct.funds_in_open_positions()
        acc.updated_at = utc_now()
        from app.models.active_position import ActivePosition
        from app.models.fill import Fill

        pos = ActivePosition(
            approved_trade_id=approved.id,
            symbol=cand.symbol,
            strategy=cand.strategy,
            status="open",
            legs=cand.legs,
            quantity=fr.quantity,
            average_entry_price=fr.price,
            market_value=fr.price * fr.quantity * 100,
            unrealized_pnl=0.0,
            initial_stop_price=fr.price * 0.93,
            emergency_premium_stop_pct=30.0,
            current_trailing_stop=fr.price * 0.93,
            breakeven_armed=False,
            partial_exit_taken=False,
            partial_exit_qty=0,
            thesis_expires_at=None,
            high_water_mark_price=fr.price,
            low_water_mark_price=fr.price,
            reached_1r=False,
            reached_1_5r=False,
            reached_2r=False,
            opened_at=utc_now(),
        )
        self._db.add(pos)
        self._db.flush()
        fl = Fill(
            created_at=utc_now(),
            active_position_id=pos.id,
            approved_trade_id=approved.id,
            side="buy",
            quantity=fr.quantity,
            price=fr.price,
            fee=fee,
            slip_bps=fr.slip_bps_applied,
            is_partial=fr.is_partial,
            leg_index=0,
        )
        self._db.add(fl)
        approved.status = "filled"
        self._db.commit()
        log.info("paper open filled position id=%s fill_price=%.4f option_mid=%.4f", pos.id, fr.price, omid)
        return pos.id
