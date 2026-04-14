def test_bot_start_stop(client):
    r = client.post("/bot/start")
    assert r.status_code == 200
    assert r.json()["state"] == "running"
    r2 = client.post("/bot/stop")
    assert r2.status_code == 200
    assert r2.json()["state"] == "stopped"
    # scheduler stopped with /bot/stop — avoid background jobs in test process
