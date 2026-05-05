from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional

from app.settings import settings


def _live_dir() -> pathlib.Path:
    return settings.data_dir / "geo" / "live"


def _load_json(path: pathlib.Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_live_files() -> List[pathlib.Path]:
    base = _live_dir()
    if not base.exists():
        return []
    files = sorted(
        [f for f in base.iterdir() if f.name.startswith("LIVE-") and f.suffix == ".json"],
        key=lambda f: f.stem,
        reverse=True,
    )
    return files


def list_live_summaries() -> List[Dict[str, Any]]:
    summaries = []
    for f in list_live_files():
        data = _load_json(f)
        summaries.append(
            {
                "run_id": data.get("run_id", f.stem),
                "timestamp": data.get("timestamp", ""),
                "engines": data.get("engines", []),
                "n_queries": data.get("n_queries", 0),
                "engine_coverage_avg": data.get("engine_coverage_avg", 0.0),
            }
        )
    return summaries


def _enrich_live(data: Dict[str, Any]) -> Dict[str, Any]:
    """Añade engine_coverage_avg si no está presente en el fichero."""
    if "engine_coverage_avg" not in data:
        results = data.get("results", [])
        if results:
            coverages = [r.get("engine_coverage", 0.0) for r in results]
            data["engine_coverage_avg"] = round(sum(coverages) / len(coverages), 2)
        else:
            data["engine_coverage_avg"] = 0.0
    return data


def load_live_run(run_id: str) -> Optional[Dict[str, Any]]:
    if run_id == "latest":
        return load_latest_live()
    path = _live_dir() / f"{run_id}.json"
    if not path.exists():
        return None
    return _enrich_live(_load_json(path))


def load_latest_live() -> Optional[Dict[str, Any]]:
    files = list_live_files()
    if not files:
        return None
    return _enrich_live(_load_json(files[0]))
