import json
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.settings import settings


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ── /api/health ───────────────────────────────────────────────────────────────


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "version" in body
    assert "data_dir" in body


# ── /api/config/target ────────────────────────────────────────────────────────


def test_config_target(client):
    r = client.get("/api/config/target")
    assert r.status_code == 200
    body = r.json()
    assert body["target_url"] == "https://programamos.es"
    assert body["target_brand"] == "Programamos"
    assert isinstance(body["engines_configured"], list)


# ── /api/config/competitors ───────────────────────────────────────────────────


def test_config_competitors_not_found(client, tmp_path):
    """Si frozen_competitors.json no existe → 404."""
    with patch.object(settings, "data_dir", tmp_path):
        r = client.get("/api/config/competitors")
    assert r.status_code == 404


def test_config_competitors_with_list_data(client, tmp_path):
    """Formato lista: el endpoint devuelve items y total."""
    data = [
        {"domain": "competidor1.es", "total_score": 10, "citations": 5},
        {"domain": "competidor2.es", "total_score": 7, "citations": 3},
        {"domain": "competidor3.es", "total_score": 2, "citations": 1},
    ]
    (tmp_path / "frozen_competitors.json").write_text(json.dumps(data))

    with patch.object(settings, "data_dir", tmp_path):
        r = client.get("/api/config/competitors?top=2")

    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 2
    # Debe estar ordenado descendente por total_score
    assert body["items"][0]["domain"] == "competidor1.es"


def test_config_competitors_with_dict_data(client, tmp_path):
    """Formato dict con clave 'competitors'."""
    data = {
        "competitors": [
            {"domain": "a.es", "citations": 8},
            {"domain": "b.es", "citations": 3},
        ]
    }
    (tmp_path / "frozen_competitors.json").write_text(json.dumps(data))

    with patch.object(settings, "data_dir", tmp_path):
        r = client.get("/api/config/competitors")

    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1


def test_config_competitors_default_top(client, tmp_path):
    """Sin parámetro top devuelve hasta 15 resultados."""
    data = [{"domain": f"c{i}.es", "total_score": i} for i in range(20)]
    (tmp_path / "frozen_competitors.json").write_text(json.dumps(data))

    with patch.object(settings, "data_dir", tmp_path):
        r = client.get("/api/config/competitors")

    assert r.status_code == 200
    assert r.json()["total"] == 15


# ── Autenticación (deps.py) ───────────────────────────────────────────────────


def test_api_key_rejected_when_configured(client):
    """Con DASHBOARD_API_KEY configurada, una clave incorrecta devuelve 401."""
    with patch.object(settings, "dashboard_api_key", "mi-clave-secreta"):
        r = client.get("/api/config/target", headers={"X-API-Key": "clave-incorrecta"})
    assert r.status_code == 401


def test_api_key_accepted_when_correct(client):
    """Con DASHBOARD_API_KEY configurada, la clave correcta devuelve 200."""
    with patch.object(settings, "dashboard_api_key", "mi-clave-secreta"):
        r = client.get("/api/config/target", headers={"X-API-Key": "mi-clave-secreta"})
    assert r.status_code == 200


def test_no_auth_required_when_key_not_set(client):
    """Sin DASHBOARD_API_KEY, cualquier petición pasa sin cabecera."""
    r = client.get("/api/config/target")
    assert r.status_code == 200
