from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import get_settings
from app.repositories.account_repository import AccountRepository
from app.schemas.account import BalancesRead

router = APIRouter(tags=["balances"])


@router.get("/balances", response_model=BalancesRead)
def balances(db: Session = Depends(get_db)) -> BalancesRead:
    settings = get_settings()
    repo = AccountRepository(db)
    acc = repo.ensure_primary(settings.bot_default_starting_cash)
    in_trades = repo.funds_in_open_positions()
    return BalancesRead(
        cash=acc.cash_balance,
        in_trades=in_trades,
        total=acc.equity,
        currency=acc.currency,
    )
