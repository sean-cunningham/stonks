from datetime import timedelta

from sqlalchemy.orm import Session

from app.core.clock import utc_now
from app.models.tastytrade_credential import TastytradeCredential


class TastytradeCredentialRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get(self) -> TastytradeCredential:
        row = self._db.get(TastytradeCredential, 1)
        if row:
            return row
        row = TastytradeCredential(id=1, updated_at=utc_now())
        self._db.add(row)
        self._db.commit()
        self._db.refresh(row)
        return row

    def set_oauth_state(self, state: str, *, ttl_minutes: int = 10) -> TastytradeCredential:
        row = self.get()
        row.oauth_state = state
        row.oauth_state_expires_at = utc_now() + timedelta(minutes=ttl_minutes)
        row.updated_at = utc_now()
        self._db.commit()
        self._db.refresh(row)
        return row

    def verify_oauth_state(self, state: str) -> bool:
        row = self.get()
        if not row.oauth_state or row.oauth_state != state:
            return False
        exp = row.oauth_state_expires_at
        if exp and exp.tzinfo is None:
            exp = exp.replace(tzinfo=utc_now().tzinfo)
        if exp and exp < utc_now():
            return False
        row.oauth_state = None
        row.oauth_state_expires_at = None
        row.updated_at = utc_now()
        self._db.commit()
        return True

    def save_tokens(
        self,
        *,
        refresh_token: str | None,
        access_token: str | None,
        access_expires_at,
        refresh_expires_at=None,
    ) -> TastytradeCredential:
        row = self.get()
        if refresh_token:
            row.refresh_token = refresh_token
        row.access_token = access_token
        row.access_expires_at = access_expires_at
        row.refresh_expires_at = refresh_expires_at
        row.updated_at = utc_now()
        self._db.commit()
        self._db.refresh(row)
        return row

    def set_selected_account(self, account_number: str) -> TastytradeCredential:
        row = self.get()
        row.selected_account_number = account_number
        row.bootstrap_complete = bool(row.refresh_token and row.selected_account_number)
        row.updated_at = utc_now()
        self._db.commit()
        self._db.refresh(row)
        return row
