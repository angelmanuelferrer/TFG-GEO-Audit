def test_list_live_runs(client):
    r = client.get("/api/runs/live")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1


def test_get_latest_live(client):
    r = client.get("/api/runs/live/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] == "LIVE-2026-W14"
    assert "summary" in body
    assert "engine_coverage_avg" in body


def test_get_live_run(client):
    r = client.get("/api/runs/live/LIVE-2026-W14")
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] == "LIVE-2026-W14"


def test_get_live_run_query(client):
    r = client.get("/api/runs/live/LIVE-2026-W14/queries/Q001")
    assert r.status_code == 200
    body = r.json()
    assert body["query_id"] == "Q001"
    assert "engines" in body


def test_get_live_run_not_found(client):
    r = client.get("/api/runs/live/LIVE-9999-W99")
    assert r.status_code == 404
