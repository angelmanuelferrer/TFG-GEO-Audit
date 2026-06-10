import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# Helper: obtener el run más reciente sin depender de un ID hardcodeado
def _latest_run_id(client) -> str:
    return client.get("/api/runs/live/latest").json()["run_id"]


# ── List ──────────────────────────────────────────────────────────────────────


def test_list_live_runs(client):
    r = client.get("/api/runs/live")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1


# ── Latest ────────────────────────────────────────────────────────────────────


def test_get_latest_live(client):
    r = client.get("/api/runs/live/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["run_id"].startswith("LIVE-")
    assert "summary" in body
    assert "engine_coverage_avg" in body


# ── Run por ID ────────────────────────────────────────────────────────────────


def test_get_live_run(client):
    run_id = _latest_run_id(client)
    r = client.get(f"/api/runs/live/{run_id}")
    assert r.status_code == 200
    assert r.json()["run_id"] == run_id


def test_get_live_run_not_found(client):
    r = client.get("/api/runs/live/LIVE-9999-W99")
    assert r.status_code == 404


# ── Query dentro de run ───────────────────────────────────────────────────────


def test_get_live_run_query(client):
    run_id = _latest_run_id(client)
    r = client.get(f"/api/runs/live/{run_id}/queries/Q001")
    assert r.status_code == 200
    body = r.json()
    assert body["query_id"] == "Q001"
    assert "engines" in body


def test_get_live_run_query_run_not_found(client):
    """Run no existe → 404 en el endpoint de query."""
    r = client.get("/api/runs/live/LIVE-9999-W99/queries/Q001")
    assert r.status_code == 404


def test_get_live_run_query_query_not_found(client):
    """Run existe pero query_id no existe → 404."""
    run_id = _latest_run_id(client)
    r = client.get(f"/api/runs/live/{run_id}/queries/Q999")
    assert r.status_code == 404


# ── Compare ───────────────────────────────────────────────────────────────────


def test_compare_live_runs(client):
    """Comparar dos runs reales disponibles."""
    items = client.get("/api/runs/live").json()["items"]
    if len(items) < 2:
        pytest.skip("Se necesitan al menos 2 runs live para este test")

    run_a = items[1]["run_id"]  # el segundo más reciente
    run_b = items[0]["run_id"]  # el más reciente

    r = client.get(f"/api/runs/live/compare?a={run_a}&b={run_b}")
    assert r.status_code == 200
    body = r.json()
    assert body["run_a"] == run_a
    assert body["run_b"] == run_b
    assert "delta_engine_coverage_avg" in body
    assert "deltas_by_engine" in body


def test_compare_live_run_a_not_found(client):
    run_b = _latest_run_id(client)
    r = client.get(f"/api/runs/live/compare?a=LIVE-NOEXISTE&b={run_b}")
    assert r.status_code == 404


def test_compare_live_run_b_not_found(client):
    run_a = _latest_run_id(client)
    r = client.get(f"/api/runs/live/compare?a={run_a}&b=LIVE-NOEXISTE")
    assert r.status_code == 404
