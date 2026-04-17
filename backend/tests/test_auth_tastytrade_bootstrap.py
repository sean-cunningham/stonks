from app.repositories.tastytrade_credential_repository import TastytradeCredentialRepository


def test_tastytrade_bootstrap_flow(client, db_session, monkeypatch):
    from app.core.config import get_settings

    s = get_settings()
    s.tastytrade_oauth_client_id = "cid"
    s.tastytrade_oauth_client_secret = "secret"
    s.tastytrade_oauth_redirect_uri = "http://localhost:8000/auth/tastytrade/callback"

    async def fake_exchange(self, code: str):
        return {"access_token": "acc-token", "refresh_token": "ref-token", "expires_in": 3600}

    async def fake_accounts(self, access_token: str):
        return {"data": [{"account-number": "5WT12345", "nickname": "paper"}]}

    async def fake_refresh(self):
        return None

    async def fake_dx(self):
        return {"token": "dx-token"}

    async def fake_chain(self, symbol: str):
        return {"data": {"symbol": symbol, "items": [1, 2, 3]}}

    monkeypatch.setattr("app.services.market_data.tastytrade_rest.TastytradeRestClient.exchange_auth_code", fake_exchange)
    monkeypatch.setattr("app.services.market_data.tastytrade_rest.TastytradeRestClient.list_accounts", fake_accounts)
    monkeypatch.setattr("app.services.market_data.tastytrade_broker.TastytradeBrokerAdapter.refresh_oauth_if_needed", fake_refresh)
    monkeypatch.setattr("app.services.market_data.tastytrade_broker.TastytradeBrokerAdapter.get_dxlink_token", fake_dx)
    monkeypatch.setattr("app.services.market_data.tastytrade_broker.TastytradeBrokerAdapter.get_option_chain", fake_chain)

    r = client.get("/auth/tastytrade/login", follow_redirects=False)
    assert r.status_code in (302, 307)
    repo = TastytradeCredentialRepository(db_session)
    state = repo.get().oauth_state
    assert state

    cb = client.get(f"/auth/tastytrade/callback?code=test-code&state={state}")
    assert cb.status_code == 200
    body = cb.json()
    assert body["ok"] is True
    assert body["accounts"][0]["account_number"] == "5WT12345"

    ac = client.get("/auth/tastytrade/accounts")
    assert ac.status_code == 200
    assert ac.json()["accounts"][0]["account_number"] == "5WT12345"

    sel = client.post("/auth/tastytrade/select-account", json={"account_number": "5WT12345"})
    assert sel.status_code == 200
    smoke = sel.json()["smoke_test"]
    assert smoke["dxlink_token_ok"] is True
    assert smoke["spy_chain_ok"] is True
