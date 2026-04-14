from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.active_position import ActivePosition


class AccountRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_primary(self) -> Account | None:
        return self._db.scalar(select(Account).where(Account.id == 1))

    def ensure_primary(self, starting_cash: float) -> Account:
        acc = self.get_primary()
        if acc:
            return acc
        from app.core.clock import utc_now

        acc = Account(
            id=1,
            cash_balance=starting_cash,
            equity=starting_cash,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            currency="USD",
            updated_at=utc_now(),
        )
        self._db.add(acc)
        self._db.commit()
        self._db.refresh(acc)
        return acc

    def update_balances(
        self,
        *,
        cash: float | None = None,
        equity: float | None = None,
        realized: float | None = None,
        unrealized: float | None = None,
    ) -> Account:
        acc = self.ensure_primary(2000.0)
        if cash is not None:
            acc.cash_balance = cash
        if equity is not None:
            acc.equity = equity
        if realized is not None:
            acc.realized_pnl = realized
        if unrealized is not None:
            acc.unrealized_pnl = unrealized
        from app.core.clock import utc_now

        acc.updated_at = utc_now()
        self._db.commit()
        self._db.refresh(acc)
        return acc

    def funds_in_open_positions(self) -> float:
        q = select(func.coalesce(func.sum(ActivePosition.market_value), 0.0)).where(
            ActivePosition.status == "open",
        )
        return float(self._db.scalar(q) or 0.0)
