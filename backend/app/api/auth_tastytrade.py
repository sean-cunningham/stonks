import secrets
from datetime import timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.clock import utc_now
from app.core.config import get_settings
from app.repositories.tastytrade_credential_repository import TastytradeCredentialRepository
from app.services.market_data.tastytrade_broker import TastytradeBrokerAdapter
from app.services.market_data.tastytrade_rest import TastytradeRestClient
from app.services.market_data.token_manager import TokenManager

router = APIRouter(prefix="/auth/tastytrade", tags=["auth-tastytrade"])


class SelectAccountRequest(BaseModel):
    account_number: str


def _extract_accounts(raw: dict) -> list[dict]:
    # Defensive parsing for varying upstream response shapes.
    candidates = [
        raw.get("data"),
        raw.get("accounts"),
        (raw.get("data") or {}).get("items") if isinstance(raw.get("data"), dict) else None,
    ]
    for c in candidates:
        if isinstance(c, list):
            out: list[dict] = []
            for a in c:
                if not isinstance(a, dict):
                    continue
                num = str(a.get("account-number") or a.get("account_number") or a.get("number") or "")
                out.append(
                    {
                        "account_number": num,
                        "nickname": a.get("nickname"),
                        "raw": a,
                    }
                )
            if out:
                return out
    return []


def _seconds_until(dt) -> int:
    if not dt:
        return 0
    exp = dt
    if exp.tzinfo is None:
        exp = exp.replace(tzinfo=utc_now().tzinfo)
    return int((exp - utc_now()).total_seconds())


@router.get("/login")
async def tastytrade_login(db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    if not settings.tastytrade_oauth_client_id or not settings.tastytrade_oauth_redirect_uri:
        raise HTTPException(status_code=400, detail="Missing tastytrade OAuth client id or redirect uri")
    state = secrets.token_urlsafe(24)
    TastytradeCredentialRepository(db).set_oauth_state(state)
    query = urlencode(
        {
            "client_id": settings.tastytrade_oauth_client_id,
            "redirect_uri": settings.tastytrade_oauth_redirect_uri,
            "response_type": "code",
            "state": state,
            "scope": "offline_access",
        }
    )
    url = f"{settings.tastytrade_api_base_url.rstrip('/')}/oauth/authorize?{query}"
    return RedirectResponse(url=url, status_code=302)


@router.get("/callback")
async def tastytrade_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
) -> dict:
    settings = get_settings()
    repo = TastytradeCredentialRepository(db)
    if not repo.verify_oauth_state(state):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    rest = TastytradeRestClient(settings)
    token_payload = await rest.exchange_auth_code(code)
    access = token_payload.get("access_token")
    refresh = token_payload.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=400, detail="OAuth exchange missing refresh_token")
    exp_in = int(token_payload.get("expires_in", 3600))
    access_expires = utc_now() + timedelta(seconds=max(30, exp_in))
    repo.save_tokens(
        refresh_token=refresh,
        access_token=access,
        access_expires_at=access_expires,
        refresh_expires_at=None,
    )
    accounts_raw = await rest.list_accounts(access or "")
    accounts = _extract_accounts(accounts_raw)
    return {
        "ok": True,
        "message": "OAuth bootstrap callback succeeded. Select account next.",
        "accounts": [{"account_number": a["account_number"], "nickname": a.get("nickname")} for a in accounts],
    }


@router.get("/accounts")
async def tastytrade_accounts(db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    repo = TastytradeCredentialRepository(db)
    row = repo.get()
    if not row.refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token stored; run /auth/tastytrade/login first")
    tm = TokenManager()
    if row.access_token and row.access_expires_at:
        ttl = int(max(60, _seconds_until(row.access_expires_at)))
        tm.set_oauth(row.access_token, ttl, row.refresh_token)
    adapter = TastytradeBrokerAdapter(settings, tm, refresh_token_override=row.refresh_token)
    await adapter.refresh_oauth_if_needed()
    raw = await TastytradeRestClient(settings).list_accounts(tm.get_access_token() or "")
    accounts = _extract_accounts(raw)
    return {
        "ok": True,
        "selected_account_number": row.selected_account_number,
        "accounts": [{"account_number": a["account_number"], "nickname": a.get("nickname")} for a in accounts],
    }


@router.post("/select-account")
async def tastytrade_select_account(req: SelectAccountRequest, db: Session = Depends(get_db)) -> dict:
    settings = get_settings()
    repo = TastytradeCredentialRepository(db)
    row = repo.get()
    if not row.refresh_token:
        raise HTTPException(status_code=400, detail="No refresh token stored; run /auth/tastytrade/login first")
    repo.set_selected_account(req.account_number)

    # Smoke test via existing adapter path.
    tm = TokenManager()
    if row.access_token and row.access_expires_at:
        ttl = int(max(60, _seconds_until(row.access_expires_at)))
        tm.set_oauth(row.access_token, ttl, row.refresh_token)
    adapter = TastytradeBrokerAdapter(settings, tm, refresh_token_override=row.refresh_token)
    await adapter.refresh_oauth_if_needed()
    dx = await adapter.get_dxlink_token()
    chain = await adapter.get_option_chain("SPY")

    return {
        "ok": True,
        "selected_account_number": req.account_number,
        "bootstrap_storage": "database table tastytrade_credentials",
        "smoke_test": {
            "oauth_refresh_ok": bool(tm.get_access_token()),
            "dxlink_token_ok": bool(dx.get("token")),
            "spy_chain_ok": bool(chain),
        },
    }
