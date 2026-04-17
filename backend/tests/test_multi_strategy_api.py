from __future__ import annotations

from fastapi.testclient import TestClient

from app.repositories.bot_state_repository import BotStateRepository
from app.repositories.strategy_bot_state_repository import SPY_SCALPER_SLUG, StrategyBotStateRepository


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
    rh = body["extensions"]["runtime_health"]
    assert isinstance(rh.get("live_candidate_pipeline_enabled"), bool)
    assert "app_mode" in rh


def test_spy_scalper_dashboard_ok(client: TestClient) -> None:
    r = client.get("/strategies/spy-0dte-scalper/dashboard")
    assert r.status_code == 200
    body = r.json()
    assert body["status"]["strategy_id"] == "spy-0dte-scalper"
    assert isinstance(body["logs"], list)
    assert "runtime_health" in (body.get("extensions") or {})


def test_config_shapes_are_normalized(client: TestClient) -> None:
    ee = client.get("/strategies/event-edge-v1/config")
    assert ee.status_code == 200
    ee_body = ee.json()
    assert set(ee_body.keys()) == {"read_only", "effective", "overrides", "notes"}
    assert ee_body["read_only"] is True
    assert ee_body["overrides"] is None
    assert "live_candidate_pipeline_enabled" in ee_body["effective"]

    spy = client.get("/strategies/spy-0dte-scalper/config")
    assert spy.status_code == 200
    spy_body = spy.json()
    assert set(spy_body.keys()) == {"read_only", "effective", "overrides", "notes"}
    assert spy_body["read_only"] is False
    assert "live_candidate_pipeline_enabled" in spy_body["effective"]


def test_strategy_scoped_config_put_dispatch(client: TestClient) -> None:
    ee_put = client.put("/strategies/event-edge-v1/config", json={"overrides": {"paper_only": True}})
    assert ee_put.status_code == 405

    spy_put = client.put("/strategies/spy-0dte-scalper/config", json={"overrides": {"paper_only": True}})
    assert spy_put.status_code == 200
    spy_body = spy_put.json()
    assert set(spy_body.keys()) == {"read_only", "effective", "overrides", "notes"}
    assert spy_body["overrides"]["paper_only"] is True


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


def test_metrics_daily_shape_is_normalized(client: TestClient) -> None:
    ee = client.get("/strategies/event-edge-v1/metrics/daily")
    assert ee.status_code == 200
    ee_body = ee.json()
    assert set(ee_body.keys()) == {"strategy_id", "trade_day", "metrics", "details"}
    assert ee_body["strategy_id"] == "event-edge-v1"

    spy = client.get("/strategies/spy-0dte-scalper/metrics/daily")
    assert spy.status_code == 200
    spy_body = spy.json()
    assert set(spy_body.keys()) == {"strategy_id", "trade_day", "metrics", "details"}
    assert spy_body["strategy_id"] == "spy-0dte-scalper"


def test_strategy_scoped_paper_reset_endpoint(client: TestClient) -> None:
    r = client.post("/strategies/event-edge-v1/paper-reset")
    assert r.status_code == 200
    body = r.json()
    assert body["strategy_id"] == "event-edge-v1"


def test_spy_paper_reset_clears_runtime_state(client: TestClient, db_session) -> None:
    strat_repo = StrategyBotStateRepository(db_session)
    strat_repo.update_scalper_state_json(SPY_SCALPER_SLUG, {"deployable_cash": 1234.0})
    row = strat_repo.get_or_create(SPY_SCALPER_SLUG)
    assert row.scalper_state_json is not None

    r = client.post("/strategies/spy-0dte-scalper/paper-reset")
    assert r.status_code == 200
    body = r.json()
    assert body["strategy_id"] == "spy-0dte-scalper"

    refreshed = strat_repo.get_or_create(SPY_SCALPER_SLUG)
    assert refreshed.scalper_state_json is None


def test_spy_scalper_signals_skipped(client: TestClient) -> None:
    r = client.get("/strategies/spy-0dte-scalper/signals/skipped")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_strategy_scoped_collection_endpoints_are_consistent(client: TestClient) -> None:
    strategy_ids = ("event-edge-v1", "spy-0dte-scalper")
    suffixes = (
        "signals/recent",
        "signals/skipped",
        "trades/recent",
        "logs/recent",
        "position",
        "status",
    )

    for strategy_id in strategy_ids:
        for suffix in suffixes:
            r = client.get(f"/strategies/{strategy_id}/{suffix}")
            assert r.status_code == 200
            payload = r.json()
            if suffix == "position":
                assert payload is None or isinstance(payload, dict)
            elif suffix == "status":
                assert isinstance(payload, dict)
                assert payload["strategy_id"] == strategy_id
            else:
                assert isinstance(payload, list)


def test_strategy_enable_disable_state_is_isolated(client: TestClient, db_session) -> None:
    event_edge_repo = BotStateRepository(db_session)
    scalper_repo = StrategyBotStateRepository(db_session)

    event_edge_repo.set_state("stopped")
    scalper_repo.set_state(SPY_SCALPER_SLUG, "stopped")

    r_enable_scalper = client.post("/strategies/spy-0dte-scalper/enable")
    assert r_enable_scalper.status_code == 200
    assert r_enable_scalper.json()["strategy_id"] == "spy-0dte-scalper"
    assert event_edge_repo.get().state == "stopped"
    assert scalper_repo.get_or_create(SPY_SCALPER_SLUG).state == "running"

    r_enable_event_edge = client.post("/strategies/event-edge-v1/enable")
    assert r_enable_event_edge.status_code == 200
    assert r_enable_event_edge.json()["strategy_id"] == "event-edge-v1"
    assert event_edge_repo.get().state == "running"
    assert scalper_repo.get_or_create(SPY_SCALPER_SLUG).state == "running"

    r_disable_scalper = client.post("/strategies/spy-0dte-scalper/disable")
    assert r_disable_scalper.status_code == 200
    assert event_edge_repo.get().state == "running"
    assert scalper_repo.get_or_create(SPY_SCALPER_SLUG).state == "stopped"

    r_disable_event_edge = client.post("/strategies/event-edge-v1/disable")
    assert r_disable_event_edge.status_code == 200
    assert event_edge_repo.get().state == "stopped"
    assert scalper_repo.get_or_create(SPY_SCALPER_SLUG).state == "stopped"
