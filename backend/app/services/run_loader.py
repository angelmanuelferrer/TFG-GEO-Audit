"""Carga scorecards y raw_results de runs experimentales.

Maneja dos formatos de scorecard:
- v1 (run_20260405_163337): sin query_id en per_query_metrics, sin by_category
- v2 (run_20260405_173413+): con query_id, by_category, category en cada query
"""
from __future__ import annotations

import json
import pathlib
from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.settings import settings


def _experimental_dir() -> pathlib.Path:
    return settings.data_dir / "geo" / "experimental"


def list_run_dirs() -> List[pathlib.Path]:
    base = _experimental_dir()
    if not base.exists():
        return []
    dirs = sorted(
        [d for d in base.iterdir() if d.is_dir() and d.name.startswith("run_")],
        key=lambda d: d.name,
        reverse=True,
    )
    return dirs


def _load_json(path: pathlib.Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _query_text_to_id_map() -> Dict[str, str]:
    """Mapea texto de query → query_id leyendo config/queries.json (para v1)."""
    try:
        import sys
        sys.path.insert(0, str(pathlib.Path(__file__).parents[4]))
        from src.config import load_queries

        data = load_queries()
        if "queries" in data and isinstance(data["queries"], dict):
            return {v["text"]: k for k, v in data["queries"].items()}
    except Exception:
        pass
    return {}


def _normalize_scorecard(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normaliza scorecard a formato v2 (con query_id y by_category)."""
    per_query = raw.get("per_query_metrics", [])

    # Añadir query_id si falta (v1)
    if per_query and "query_id" not in per_query[0]:
        text_to_id = _query_text_to_id_map()
        for q in per_query:
            q["query_id"] = text_to_id.get(q.get("query", ""), None)

    # Añadir by_category si falta (v1)
    if "by_category" not in raw:
        raw["by_category"] = _compute_by_category(per_query)

    return raw


def _compute_by_category(per_query: List[Dict]) -> Dict[str, Dict]:
    buckets: Dict[str, List] = defaultdict(list)
    for q in per_query:
        cat = q.get("category") or "unknown"
        buckets[cat].append(q)

    result = {}
    for cat, queries in buckets.items():
        n = len(queries)
        successful = [q for q in queries if not q.get("_error")]
        n_errors = n - len(successful)
        visible = [q for q in successful if q.get("is_visible")]
        soms = [q["som"] for q in successful if q.get("som") is not None]
        citations = [q["avg_citations"] if "avg_citations" in q else q.get("total_citations", 0) for q in successful]
        result[cat] = {
            "n": n,
            "n_errors": n_errors,
            "n_successful": len(successful),
            "visibility_rate": round(len(visible) / len(successful) * 100, 2) if successful else 0.0,
            "avg_som": round(sum(soms) / len(soms), 2) if soms else 0.0,
            "avg_citations": round(sum(citations) / len(citations), 2) if citations else 0.0,
        }
    return result


def load_scorecard(run_id: str) -> Optional[Dict[str, Any]]:
    path = _experimental_dir() / run_id / "scorecard.json"
    if not path.exists():
        return None
    raw = _load_json(path)
    return _normalize_scorecard(raw)


def load_raw_results(run_id: str) -> Optional[List[Dict[str, Any]]]:
    path = _experimental_dir() / run_id / "raw_results.json"
    if not path.exists():
        return None
    return _load_json(path)


def list_runs_summary() -> List[Dict[str, Any]]:
    summaries = []
    for run_dir in list_run_dirs():
        sc_path = run_dir / "scorecard.json"
        if not sc_path.exists():
            continue
        raw = _load_json(sc_path)
        summaries.append(
            {
                "run_id": raw.get("run_id", run_dir.name),
                "timestamp": raw.get("timestamp", ""),
                "rotation_block": raw.get("rotation_block"),
                "n_queries": raw.get("n_queries", 0),
                "n_successful": raw.get("n_successful", 0),
                "n_errors": raw.get("n_errors", 0),
                "visibility_rate": raw.get("visibility_rate", 0.0),
                "avg_som": raw.get("avg_som", 0.0),
                "avg_citations": raw.get("avg_citations", 0.0),
            }
        )
    return summaries


def compute_derived(scorecard: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula avg_first_rank_by_category y avg_pawc_by_category."""
    per_query = scorecard.get("per_query_metrics", [])

    rank_by_cat: Dict[str, List[float]] = defaultdict(list)
    pawc_by_cat: Dict[str, List[float]] = defaultdict(list)

    for q in per_query:
        cat = q.get("category") or "unknown"
        if q.get("first_citation_rank") is not None:
            rank_by_cat[cat].append(q["first_citation_rank"])
        if q.get("pawc") is not None:
            pawc_by_cat[cat].append(q["pawc"])

    avg_rank = {
        cat: round(sum(v) / len(v), 2) if v else None
        for cat, v in rank_by_cat.items()
    }
    avg_pawc = {
        cat: round(sum(v) / len(v), 2) if v else None
        for cat, v in pawc_by_cat.items()
    }
    return {"avg_first_rank_by_category": avg_rank, "avg_pawc_by_category": avg_pawc}
