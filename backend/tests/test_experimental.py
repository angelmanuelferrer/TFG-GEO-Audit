def test_list_experimental_runs(client):
    r = client.get("/api/runs/experimental")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 2
    items = body["items"]
    # Ordenados descendente por timestamp
    assert items[0]["run_id"] == "run_20260405_173413"


def test_get_experimental_run(client):
    r = client.get("/api/runs/experimental/run_20260405_173413")
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] == "run_20260405_173413"
    assert "by_category" in body
    assert "_derived" in body
    assert "avg_first_rank_by_category" in body["_derived"]


def test_get_experimental_run_not_found(client):
    r = client.get("/api/runs/experimental/run_noexiste")
    assert r.status_code == 404


def test_get_raw_results(client):
    r = client.get("/api/runs/experimental/run_20260405_173413/raw?limit=5")
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 5
    assert len(body["items"]) <= 5


def test_get_run_query(client):
    r = client.get("/api/runs/experimental/run_20260405_173413/queries/Q001")
    assert r.status_code == 200
    body = r.json()
    assert body["query_id"] == "Q001"
    assert "metrics" in body
    assert "raw" in body


def test_compare_runs(client):
    r = client.get(
        "/api/runs/experimental/compare?a=run_20260405_163337&b=run_20260405_173413"
    )
    assert r.status_code == 200
    body = r.json()
    assert "deltas" in body
    assert "queries_gained" in body
    assert "queries_lost" in body
