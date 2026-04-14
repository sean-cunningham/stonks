def test_analytics_summary(client):
    r = client.get("/analytics/summary")
    assert r.status_code == 200
    body = r.json()
    assert "overall" in body
    assert "exit_quality" in body
    assert "governance_note" in body


def test_analytics_trade_review_not_found(client):
    r = client.get("/analytics/trades/99999/review")
    assert r.status_code == 404


def test_status_includes_analytics_compact(client):
    r = client.get("/status")
    assert r.status_code == 200
    body = r.json()
    assert "analytics_compact" in body
    ac = body["analytics_compact"]
    assert "governance_note" in ac
    assert "trade_review_count" in ac
