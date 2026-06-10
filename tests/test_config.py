"""Tests del cargador de configuración (src/config.py) sobre los ficheros reales.

Verifican los invariantes del protocolo experimental: 100 consultas, 20 core,
40 por run (core + bloque de rotación) y exclusión de navegacionales en discovery.
"""
from __future__ import annotations

import pytest

from src import config


def test_experiment_config_has_required_keys():
    cfg = config.load_experiment_config()
    for key in ("target_url", "target_brand", "chunking", "retrieval"):
        assert key in cfg


def test_queries_v2_has_100_queries_with_ids():
    data = config.load_queries()
    assert isinstance(data["queries"], dict)
    assert len(data["queries"]) == 100
    assert "Q001" in data["queries"] and "Q100" in data["queries"]


def test_all_queries_returns_100_texts():
    queries = config.get_all_queries()
    assert len(queries) == 100
    assert all(isinstance(q, str) and q for q in queries)


def test_core_queries_are_20():
    assert len(config.get_core_queries()) == 20


@pytest.mark.parametrize("block", ["R1", "R2", "R3", "R4"])
def test_each_run_has_40_queries(block):
    queries = config.get_queries_for_run(block)
    assert len(queries) == 40
    # Las 20 core están siempre incluidas
    core = set(config.get_core_queries())
    assert core.issubset(set(queries))


def test_discovery_queries_exclude_navigational():
    data = config.load_queries()
    navigational = {
        q["text"] for q in data["queries"].values() if q["category"] == "navegacional"
    }
    discovery = set(config.get_discovery_queries())
    assert discovery, "el set de discovery no puede estar vacío"
    assert not (discovery & navigational)


def test_target_url_and_brand():
    assert "programamos.es" in config.get_target_url()
    assert config.get_target_brand() == "Programamos"
