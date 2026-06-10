"""Fixtures compartidos para los tests del backend GEO-Audit.

Los tests usan un directorio de datos congelado (tests/data/) en lugar del
data/ del repositorio, para que la suite sea determinista e independiente
de qué runs se publiquen.
"""
from __future__ import annotations

import os
import pathlib

FIXTURE_DATA_DIR = pathlib.Path(__file__).parent / "data"
os.environ["DATA_DIR"] = str(FIXTURE_DATA_DIR)

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c
