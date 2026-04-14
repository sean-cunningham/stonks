def test_status(client):
    r = client.get("/status")
    assert r.status_code == 200
    body = r.json()
    assert "bot" in body
    assert body["balances"]["currency"] == "USD"
    assert body["bot"]["state"] in ("stopped", "running", "paused")
