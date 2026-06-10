"""Tests del router /api/optimizer.

Todos los tests mockean `prioritize` y `GEOOptimizer` para evitar
cualquier llamada real a APIs externas (Gemini, Anthropic, OpenAI).
"""
from __future__ import annotations

import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURE_PRIORITIZE_RESULT = {
    "mode": "experimental",
    "run_id": "run_fixture_001",
    "queries": [
        {
            "query_id": "Q001",
            "query_text": "cursos de programación online",
            "score": 3.6,
            "reason": "No apareces en esta query (3 citas de competidores)",
            "competitors_cited": [
                {"url": "https://competidor.es/cursos", "excerpt": "Aprende a programar…"}
            ],
            "relevant_urls": [],
        },
        {
            "query_id": "Q002",
            "query_text": "aprender python desde cero",
            "score": 2.4,
            "reason": "Apareces pero con SoM bajo (40%). 2 citas de competidores.",
            "competitors_cited": [],
            "relevant_urls": ["https://programamos.es/python"],
        },
    ],
}


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ── GET /api/optimizer/prioritize ─────────────────────────────────────────────


@patch("app.routers.optimizer.prioritize")
def test_prioritize_experimental_ok(mock_prioritize, client):
    mock_prioritize.return_value = FIXTURE_PRIORITIZE_RESULT

    r = client.get("/api/optimizer/prioritize")

    assert r.status_code == 200
    body = r.json()
    assert body["run_id"] == "run_fixture_001"
    assert body["mode"] == "experimental"
    assert len(body["queries"]) == 2
    assert body["queries"][0]["query_id"] == "Q001"


@patch("app.routers.optimizer.prioritize")
def test_prioritize_live_mode_ok(mock_prioritize, client):
    mock_prioritize.return_value = {**FIXTURE_PRIORITIZE_RESULT, "mode": "live"}

    r = client.get("/api/optimizer/prioritize?mode=live")

    assert r.status_code == 200
    assert r.json()["mode"] == "live"
    mock_prioritize.assert_called_once()
    _, kwargs = mock_prioritize.call_args
    assert kwargs.get("mode") == "live" or mock_prioritize.call_args[0][0] == "live"


@patch("app.routers.optimizer.prioritize")
def test_prioritize_top_k_param(mock_prioritize, client):
    mock_prioritize.return_value = FIXTURE_PRIORITIZE_RESULT

    r = client.get("/api/optimizer/prioritize?top_k=5")

    assert r.status_code == 200
    mock_prioritize.assert_called_once()


@patch("app.routers.optimizer.prioritize")
def test_prioritize_no_runs_returns_404(mock_prioritize, client):
    mock_prioritize.return_value = {"mode": "experimental", "run_id": None, "queries": []}

    r = client.get("/api/optimizer/prioritize")

    assert r.status_code == 404


@patch("app.routers.optimizer.prioritize")
def test_prioritize_top_k_out_of_range(mock_prioritize, client):
    r = client.get("/api/optimizer/prioritize?top_k=0")
    assert r.status_code == 422

    r = client.get("/api/optimizer/prioritize?top_k=51")
    assert r.status_code == 422


# ── POST /api/optimizer/analyze ───────────────────────────────────────────────


@patch("app.routers.optimizer.prioritize")
def test_analyze_too_many_queries_returns_422(mock_prioritize, client):
    """El endpoint rechaza más de 4 query_ids sin llamar a ningún LLM."""
    mock_prioritize.return_value = FIXTURE_PRIORITIZE_RESULT

    r = client.post(
        "/api/optimizer/analyze",
        json={"query_ids": ["Q001", "Q002", "Q003", "Q004", "Q005"]},
    )

    assert r.status_code == 422


@patch("app.routers.optimizer.prioritize")
def test_analyze_no_matching_queries_returns_404(mock_prioritize, client):
    """Si los query_ids enviados no coinciden con ninguna query priorizada → 404."""
    mock_prioritize.return_value = FIXTURE_PRIORITIZE_RESULT

    r = client.post(
        "/api/optimizer/analyze",
        json={"query_ids": ["Q999"]},
    )

    assert r.status_code == 404


@patch("app.routers.optimizer.prioritize")
def test_analyze_happy_path(mock_prioritize, client):
    """Happy path: GEOOptimizer se mockea completamente para evitar llamadas a Gemini."""
    mock_prioritize.return_value = FIXTURE_PRIORITIZE_RESULT

    fake_geo_module = MagicMock()
    fake_instance = MagicMock()
    fake_instance.analyze = AsyncMock(
        return_value={
            "run_id": "run_fixture_001",
            "recommendations": [
                {
                    "query_id": "Q001",
                    "query_text": "cursos de programación online",
                    "content_gap": "Falta contenido introductorio",
                    "suggested_actions": ["Añadir sección de cursos gratuitos"],
                }
            ],
        }
    )
    fake_geo_module.GEOOptimizer.return_value = fake_instance

    with patch.dict(sys.modules, {"src.optimizer.geo_optimizer": fake_geo_module}):
        r = client.post(
            "/api/optimizer/analyze",
            json={"query_ids": ["Q001"]},
        )

    assert r.status_code == 200
    body = r.json()
    assert "recommendations" in body


@patch("app.routers.optimizer.prioritize")
def test_analyze_gemini_quota_error_returns_429(mock_prioritize, client):
    """Simula error de cuota de Gemini → espera 429."""
    mock_prioritize.return_value = FIXTURE_PRIORITIZE_RESULT

    fake_geo_module = MagicMock()
    fake_instance = MagicMock()
    fake_instance.analyze = AsyncMock(side_effect=Exception("429 RESOURCE_EXHAUSTED"))
    fake_geo_module.GEOOptimizer.return_value = fake_instance

    with patch.dict(sys.modules, {"src.optimizer.geo_optimizer": fake_geo_module}):
        r = client.post(
            "/api/optimizer/analyze",
            json={"query_ids": ["Q001"]},
        )

    assert r.status_code == 429


@patch("app.routers.optimizer.prioritize")
def test_analyze_invalid_body_returns_422(mock_prioritize, client):
    """Body mal formado → validación Pydantic → 422."""
    mock_prioritize.return_value = FIXTURE_PRIORITIZE_RESULT

    r = client.post("/api/optimizer/analyze", json={"query_ids": "no-es-lista"})

    assert r.status_code == 422
