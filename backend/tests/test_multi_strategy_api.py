from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_strategies(client: TestClient) -> None:
    r = client.get("/strategies")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    ids = {x["strategy_id"] for x in data}
    assert "event-edge-v1" in ids
    assert "spy-0dte-scalper" in ids


def test_unknown_strategy_404(client: TestClient) -> None:
    r = client.get("/strategies/not-a-strategy/dashboard")
    assert r.status_code == 404


def test_event_edge_dashboard_ok(client: TestClient) -> None:
    r = client.get("/strategies/event-edge-v1/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["status"]["strategy_id"] == "event-edge-v1"
    assert "extensions" in body
    assert body["extensions"]["full_status"] is not None


def test_spy_scalper_dashboard_ok(client: TestClient) -> None:
    r = client.get("/strategies/spy-0dte-scalper/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["status"]["strategy_id"] == "spy-0dte-scalper"


def test_spy_scalper_signals_skipped(client: TestClient) -> None:
    r = client.get("/strategies/spy-0dte-scalper/signals/skipped")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
