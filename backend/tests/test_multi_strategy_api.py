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
    assert isinstance(body["logs"], list)
    assert body["logs"] == []


def test_config_shapes_are_normalized(client: TestClient) -> None:
    ee = client.get("/strategies/event-edge-v1/config")
    assert ee.status_code == 200
    ee_body = ee.json()
    assert set(ee_body.keys()) == {"read_only", "effective", "overrides", "notes"}
    assert ee_body["read_only"] is True
    assert ee_body["overrides"] is None

    spy = client.get("/strategies/spy-0dte-scalper/config")
    assert spy.status_code == 200
    spy_body = spy.json()
    assert set(spy_body.keys()) == {"read_only", "effective", "overrides", "notes"}
    assert spy_body["read_only"] is False


def test_daily_summary_shape_is_normalized(client: TestClient) -> None:
    ee = client.get("/strategies/event-edge-v1/summary/daily")
    assert ee.status_code == 200
    ee_body = ee.json()
    assert set(ee_body.keys()) == {"strategy_id", "trade_day", "metrics", "details"}
    assert ee_body["strategy_id"] == "event-edge-v1"

    spy = client.get("/strategies/spy-0dte-scalper/summary/daily")
    assert spy.status_code == 200
    spy_body = spy.json()
    assert set(spy_body.keys()) == {"strategy_id", "trade_day", "metrics", "details"}
    assert spy_body["strategy_id"] == "spy-0dte-scalper"


def test_strategy_scoped_paper_reset_endpoint(client: TestClient) -> None:
    r = client.post("/strategies/event-edge-v1/paper-reset")
    assert r.status_code == 200
    body = r.json()
    assert body["strategy_id"] == "event-edge-v1"


def test_spy_scalper_signals_skipped(client: TestClient) -> None:
    r = client.get("/strategies/spy-0dte-scalper/signals/skipped")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
