from __future__ import annotations

import json
import sys
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import verify_api_key
from app.settings import settings, PROJECT_ROOT

router = APIRouter()

# Asegurar que src/ es importable
sys.path.insert(0, str(PROJECT_ROOT))


def _load_src_config():
    from src.config import load_experiment_config, load_queries
    return load_experiment_config, load_queries


@router.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0", "data_dir": str(settings.data_dir)}


@router.get("/config/target", dependencies=[Depends(verify_api_key)])
def config_target():
    load_experiment_config, _ = _load_src_config()
    cfg = load_experiment_config()
    engines = list(cfg.get("live_evaluation", {}).get("engines", {}).keys())
    queries_version = None
    try:
        with open(PROJECT_ROOT / "config" / "queries.json") as f:
            q = json.load(f)
            queries_version = q.get("version")
    except Exception:
        pass
    return {
        "target_url": cfg.get("target_url"),
        "target_brand": cfg.get("target_brand"),
        "config_version": cfg.get("version"),
        "queries_version": queries_version,
        "engines_configured": engines,
    }



@router.get("/config/competitors", dependencies=[Depends(verify_api_key)])
def config_competitors(top: int = Query(15)):
    competitors_path = settings.data_dir / "frozen_competitors.json"
    if not competitors_path.exists():
        raise HTTPException(status_code=404, detail="frozen_competitors.json no encontrado")

    with open(competitors_path) as f:
        data = json.load(f)

    # El fichero puede ser una lista o un dict con "competitors"
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("competitors", list(data.values()))
    else:
        items = []

    # Ordenar por score/citations si hay campo numérico
    def sort_key(x):
        if isinstance(x, dict):
            return x.get("total_score", x.get("citations", 0)) or 0
        return 0

    items = sorted(items, key=sort_key, reverse=True)[:top]
    return {"items": items, "total": len(items)}
