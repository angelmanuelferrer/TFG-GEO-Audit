"""Cómputos derivados que el backend calcula al vuelo sobre los datos raw."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional

from app.services import live_loader, run_loader, seo_loader


# ── Timeline experimental ─────────────────────────────────────────────────────

def timeline_experimental(
    metric: str,
    category: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    valid = {"visibility_rate", "avg_som", "avg_citations"}
    if metric not in valid:
        raise ValueError(f"metric debe ser uno de {valid}")

    points = []
    for run_dir in reversed(run_loader.list_run_dirs()):
        sc_path = run_dir / "scorecard.json"
        if not sc_path.exists():
            continue
        import json
        with open(sc_path) as f:
            raw = json.load(f)

        ts = raw.get("timestamp", "")
        if from_date and ts < from_date:
            continue
        if to_date and ts > to_date:
            continue

        if category:
            by_cat = raw.get("by_category", {})
            cat_data = by_cat.get(category)
            value = cat_data.get(metric) if cat_data else None
        else:
            value = raw.get(metric)

        points.append(
            {
                "run_id": raw.get("run_id", run_dir.name),
                "timestamp": ts,
                "value": value,
            }
        )
    return points


# ── Timeline Live ─────────────────────────────────────────────────────────────

def timeline_live(
    metric: str,
    engine: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    global_metrics = {"engine_coverage_avg"}
    engine_metrics = {"visibility_rate", "avg_som", "avg_first_rank"}

    if metric not in global_metrics | engine_metrics:
        raise ValueError(f"metric debe ser uno de {global_metrics | engine_metrics}")
    if metric in engine_metrics and not engine:
        raise ValueError(f"Se requiere 'engine' para la métrica '{metric}'")

    points = []
    for f in reversed(live_loader.list_live_files()):
        import json
        with open(f) as fp:
            data = json.load(fp)

        ts = data.get("timestamp", "")
        if from_date and ts < from_date:
            continue
        if to_date and ts > to_date:
            continue

        if metric == "engine_coverage_avg":
            value = data.get("engine_coverage_avg")
        else:
            summary = data.get("summary", {})
            engine_summary = summary.get(engine, {})
            value = engine_summary.get(metric)

        points.append(
            {"run_id": data.get("run_id", f.stem), "timestamp": ts, "value": value}
        )
    return points


# ── Timeline SEO ──────────────────────────────────────────────────────────────

def timeline_seo(
    device: str,
    metric: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    if device not in ("mobile", "desktop"):
        raise ValueError("device debe ser 'mobile' o 'desktop'")

    points = []
    for snapshot in seo_loader.load_seo_history(from_date, to_date):
        device_data = snapshot.get(device, {})
        value = device_data.get(metric)
        points.append(
            {"run_id": snapshot.get("fecha", ""), "timestamp": snapshot.get("fecha", ""), "value": value}
        )
    return points


# ── Coverage matrix categoría × motor ────────────────────────────────────────

def coverage_matrix(run_id: str) -> Dict[str, Dict[str, float]]:
    data = live_loader.load_live_run(run_id)
    if not data:
        return {}

    # buckets[category][engine] = [is_visible, ...]
    buckets: Dict[str, Dict[str, List[bool]]] = defaultdict(lambda: defaultdict(list))

    for result in data.get("results", []):
        cat = result.get("query_category") or "unknown"
        engines_data = result.get("engines", {})
        for eng, eng_data in engines_data.items():
            buckets[cat][eng].append(bool(eng_data.get("is_visible", False)))

    matrix: Dict[str, Dict[str, float]] = {}
    for cat, engines in buckets.items():
        matrix[cat] = {}
        for eng, visibles in engines.items():
            rate = round(sum(visibles) / len(visibles) * 100, 2) if visibles else 0.0
            matrix[cat][eng] = rate
    return matrix


# ── Sentiment distribution ────────────────────────────────────────────────────

def sentiment_distribution(
    run_id: str,
    engine: Optional[str] = None,
    category: Optional[str] = None,
) -> Dict[str, Dict[str, int]]:
    data = live_loader.load_live_run(run_id)
    if not data:
        return {}

    dist: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for result in data.get("results", []):
        if category and result.get("query_category") != category:
            continue
        engines_data = result.get("engines", {})
        for eng, eng_data in engines_data.items():
            if engine and eng != engine:
                continue
            sentiment = eng_data.get("sentiment") or "null"
            dist[eng][sentiment] += 1

    return {eng: dict(counts) for eng, counts in dist.items()}


# ── Brand mentions ────────────────────────────────────────────────────────────

def brand_mentions(
    run_id: str,
    query_id: Optional[str] = None,
    engine: Optional[str] = None,
) -> List[Dict[str, Any]]:
    # Try experimental first, then live
    experimental_sc = run_loader.load_scorecard(run_id)
    if experimental_sc:
        mentions = []
        for q in experimental_sc.get("per_query_metrics", []):
            if query_id and q.get("query_id") != query_id:
                continue
            for m in q.get("brand_mentions", []):
                mentions.append(
                    {
                        "run_id": run_id,
                        "query_id": q.get("query_id"),
                        "engine": None,
                        "source": m.get("source", ""),
                        "position": m.get("position", 0),
                        "context": m.get("context", ""),
                    }
                )
        return mentions

    live_data = live_loader.load_live_run(run_id)
    if not live_data:
        return []

    mentions = []
    for result in live_data.get("results", []):
        if query_id and result.get("query_id") != query_id:
            continue
        for eng, eng_data in result.get("engines", {}).items():
            if engine and eng != engine:
                continue
            for m in eng_data.get("brand_mentions", []):
                mentions.append(
                    {
                        "run_id": run_id,
                        "query_id": result.get("query_id"),
                        "engine": eng,
                        "source": m.get("source", ""),
                        "position": m.get("position", 0),
                        "context": m.get("context", ""),
                    }
                )
    return mentions


# ── Compare experimental runs ─────────────────────────────────────────────────

def compare_experimental(run_a: str, run_b: str) -> Dict[str, Any]:
    sc_a = run_loader.load_scorecard(run_a)
    sc_b = run_loader.load_scorecard(run_b)
    if not sc_a or not sc_b:
        raise ValueError("Uno o ambos run_id no encontrados")

    # Indexar per-query por query_id (o texto como fallback)
    def index_queries(sc: Dict) -> Dict[str, Dict]:
        idx = {}
        for q in sc.get("per_query_metrics", []):
            key = q.get("query_id") or q.get("query", "")
            idx[key] = q
        return idx

    idx_a = index_queries(sc_a)
    idx_b = index_queries(sc_b)
    common_keys = set(idx_a) & set(idx_b)

    gained, lost, stable_visible = [], [], []
    ranking_shifts, som_shifts = [], []

    for key in common_keys:
        qa = idx_a[key]
        qb = idx_b[key]
        vis_a = qa.get("is_visible", False)
        vis_b = qb.get("is_visible", False)

        qid = qb.get("query_id") or key

        if not vis_a and vis_b:
            gained.append(qid)
        elif vis_a and not vis_b:
            lost.append(qid)
        elif vis_a and vis_b:
            stable_visible.append(qid)

        rank_a = qa.get("first_citation_rank")
        rank_b = qb.get("first_citation_rank")
        if rank_a != rank_b:
            ranking_shifts.append({"query_id": qid, "from_rank": rank_a, "to_rank": rank_b})

        som_a = qa.get("som", 0.0)
        som_b = qb.get("som", 0.0)
        if som_a != som_b:
            som_shifts.append(
                {"query_id": qid, "from_som": som_a, "to_som": som_b, "delta": round(som_b - som_a, 2)}
            )

    def delta(field: str) -> Optional[float]:
        va = sc_a.get(field)
        vb = sc_b.get(field)
        if va is not None and vb is not None:
            return round(vb - va, 2)
        return None

    return {
        "run_a": run_a,
        "run_b": run_b,
        "deltas": {
            "visibility_rate": delta("visibility_rate"),
            "avg_som": delta("avg_som"),
            "avg_citations": delta("avg_citations"),
        },
        "queries_gained": gained,
        "queries_lost": lost,
        "queries_stable_visible": stable_visible,
        "ranking_shifts": ranking_shifts,
        "som_shifts": som_shifts,
    }
