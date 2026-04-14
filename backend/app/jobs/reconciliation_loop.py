import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.core.config import get_settings
from app.models.active_position import ActivePosition
from app.repositories.account_repository import AccountRepository
from app.services.analytics.trade_review_service import persist_trade_review_on_close
from app.services.execution.pnl_engine import update_unrealized
from app.services.execution.trade_management import update_trade_management

log = logging.getLogger(__name__)


def run_reconciliation_tick(db: Session) -> None:
    q = select(func.count()).select_from(ActivePosition).where(ActivePosition.status == "open")
    n = db.scalar(q) or 0
    acc_repo = AccountRepository(db)
    acc = acc_repo.get_primary()
    settings = get_settings()
    open_rows = list(db.scalars(select(ActivePosition).where(ActivePosition.status == "open")).all())
    journal_queue: list[tuple[int, float, str | None]] = []
    for pos in open_rows:
        if pos.market_value is None:
            continue
        mark = max(0.01, pos.market_value / max(1, pos.quantity) / 100)
        update_unrealized(pos, mark)
        if pos.high_water_mark_price is None:
            pos.high_water_mark_price = mark
        if pos.low_water_mark_price is None:
            pos.low_water_mark_price = mark
        pos.high_water_mark_price = max(pos.high_water_mark_price, mark)
        pos.low_water_mark_price = min(pos.low_water_mark_price, mark)

        entry = pos.average_entry_price
        risk = abs(entry - (pos.initial_stop_price or entry * 0.95))
        if risk <= 0:
            risk = entry * 0.05
        r_mult = (mark - entry) / risk
        if r_mult >= 1.0:
            pos.reached_1r = True
        if r_mult >= 1.5:
            pos.reached_1_5r = True
        if r_mult >= 2.0:
            pos.reached_2r = True

        update = update_trade_management(position=pos, mark_price=mark)
        pos.current_trailing_stop = update.stop_price
        if update.take_partial and not pos.partial_exit_taken:
            pos.partial_exit_taken = True
            pos.partial_exit_qty = update.partial_qty
        if update.exit_all:
            pos.status = "closed"
            pos.closed_at = utc_now()
            journal_queue.append((pos.id, mark, update.reason))
    db.commit()
    for pos_id, exit_mark, reason in journal_queue:
        closed = db.get(ActivePosition, pos_id)
        if closed:
            persist_trade_review_on_close(db, closed, exit_mark, reason, settings=settings)
    if acc and n >= 0:
        log.debug("reconcile: open=%s cash=%s", n, acc.cash_balance)
