"""Local paper execution — default path; live adapter can mirror validation."""

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
    ) -> int | None:
        cand = self._db.get(CandidateTrade, approved.candidate_trade_id)
        if not cand:
            return None
        order = {"strategy": cand.strategy, "legs": cand.legs}
        v = self.dry_run(order)
        if not v.ok:
            return None
        qty = 1
        fr = compute_open_fill(
            side="buy",
            bid=bid,
            ask=ask,
            mid=mid,
            quantity=qty,
            slippage_bps=self._settings.paper_slippage_bps,
            partial_max_fraction=self._settings.paper_partial_fill_max_fraction,
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
        return pos.id
