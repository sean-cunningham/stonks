from pydantic import BaseModel


class BalancesRead(BaseModel):
    cash: float
    in_trades: float
    total: float
    currency: str
