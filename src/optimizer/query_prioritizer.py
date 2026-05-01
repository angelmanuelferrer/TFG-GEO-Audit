"""QueryPrioritizer — identifica queries donde programamos.es tiene mayor margen de mejora.

Dos modos:
- experimental: lee scorecard.json + raw_results.json del último run experimental.
  Sweet spot: is_visible=False (o SoM bajo) Y competidores citados → problema de contenido.
- live: lee LIVE-*.json del último run live.
  Prioriza queries con engine_coverage baja.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

TARGET_DOMAIN = "programamos.es"

CATEGORY_WEIGHT = {
    "informacional": 1.5,
    "comparativa": 1.2,
    "navegacional": 0.5,
}


@dataclass
class CompetitorCitation:
    url: str
    excerpt: str


@dataclass
class PriorityQuery:
    query_id: str
    query_text: str
    score: float
    reason: str
    competitors_cited: List[CompetitorCitation] = field(default_factory=list)
    relevant_urls: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "query_text": self.query_text,
            "score": round(self.score, 2),
            "reason": self.reason,
            "competitors_cited": [{"url": c.url, "excerpt": c.excerpt} for c in self.competitors_cited],
            "relevant_urls": self.relevant_urls,
        }


def _is_target(url: str) -> bool:
    return TARGET_DOMAIN in url


def _load_json(path: pathlib.Path) -> Any:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _latest_experimental_run(data_dir: pathlib.Path) -> Optional[pathlib.Path]:
    base = data_dir / "geo" / "experimental"
    if not base.exists():
        return None
    dirs = sorted(
        [d for d in base.iterdir() if d.is_dir() and d.name.startswith("run_")],
        key=lambda d: d.name,
        reverse=True,
    )
    return dirs[0] if dirs else None


def _latest_live_run(data_dir: pathlib.Path) -> Optional[pathlib.Path]:
    base = data_dir / "geo" / "live"
    if not base.exists():
        return None
    files = sorted(
        [f for f in base.iterdir() if f.is_file() and f.suffix == ".json" and f.stem.startswith("LIVE-")],
        key=lambda f: f.name,
        reverse=True,
    )
    return files[0] if files else None


def prioritize_experimental(data_dir: pathlib.Path, top_k: int = 15) -> Dict[str, Any]:
    run_dir = _latest_experimental_run(data_dir)
    if not run_dir:
        return {"mode": "experimental", "run_id": None, "queries": []}

    scorecard = _load_json(run_dir / "scorecard.json")
    raw_results = _load_json(run_dir / "raw_results.json")

    raw_by_id: Dict[str, Any] = {}
    for entry in raw_results:
        qid = entry.get("query_id") or entry.get("query", "")
        raw_by_id[qid] = entry

    priority_queries: List[PriorityQuery] = []

    for q in scorecard.get("per_query_metrics", []):
        query_id = q.get("query_id", "")
        query_text = q.get("query", q.get("query_text", ""))
        is_visible = q.get("is_visible", False)
        target_citations = q.get("target_citations", 0)
        total_citations = q.get("total_citations", 0)
        category = q.get("category", "informacional")

        competitor_citations_count = total_citations - target_citations
        if competitor_citations_count <= 0:
            continue

        weight = CATEGORY_WEIGHT.get(category, 1.0)

        if not is_visible:
            score = competitor_citations_count * weight * 2.0
            reason = f"No apareces en esta query ({competitor_citations_count} citas de competidores)"
        else:
            som = q.get("som", 100.0)
            if som >= 80:
                continue
            score = competitor_citations_count * weight * (1.0 - som / 100)
            reason = f"Apareces pero con SoM bajo ({som:.0f}%). {competitor_citations_count} citas de competidores."

        raw = raw_by_id.get(query_id, {})
        answer = raw.get("answer", {})
        citations = answer.get("citations", [])

        competitors: List[CompetitorCitation] = []
        target_urls: List[str] = []

        for c in citations:
            url = c.get("url", "")
            quote = c.get("quote", "")
            if _is_target(url):
                target_urls.append(url)
            else:
                if len(competitors) < 3:
                    excerpt = (quote[:200] + "…") if len(quote) > 200 else quote
                    competitors.append(CompetitorCitation(url=url, excerpt=excerpt))

        sources_unused = answer.get("sources_available_but_unused", [])
        for url in sources_unused:
            if _is_target(url) and url not in target_urls:
                target_urls.append(url)

        priority_queries.append(
            PriorityQuery(
                query_id=query_id,
                query_text=query_text,
                score=score,
                reason=reason,
                competitors_cited=competitors,
                relevant_urls=target_urls[:5],
            )
        )

    priority_queries.sort(key=lambda x: x.score, reverse=True)

    return {
        "mode": "experimental",
        "run_id": scorecard.get("run_id", run_dir.name),
        "queries": [q.to_dict() for q in priority_queries[:top_k]],
    }


def prioritize_live(data_dir: pathlib.Path, top_k: int = 15) -> Dict[str, Any]:
    live_file = _latest_live_run(data_dir)
    if not live_file:
        return {"mode": "live", "run_id": None, "queries": []}

    data = _load_json(live_file)
    engines = data.get("engines", [])
    n_engines = len(engines) if engines else 1

    priority_queries: List[PriorityQuery] = []

    for entry in data.get("results", []):
        query_id = entry.get("query_id", "")
        query_text = entry.get("query_text", "")
        category = entry.get("query_category", "informacional")
        engine_coverage = entry.get("engine_coverage", 100.0)

        engines_data: Dict[str, Any] = entry.get("engines", {})

        engines_visible = [e for e, v in engines_data.items() if v.get("is_visible")]
        engines_missing = [e for e in engines_data if e not in engines_visible]

        if not engines_missing:
            continue

        weight = CATEGORY_WEIGHT.get(category, 1.0)
        score = len(engines_missing) * weight * (1.0 - engine_coverage / 100)

        if score <= 0:
            continue

        reason = (
            f"No apareces en: {', '.join(engines_missing)}. "
            f"Cobertura actual: {engine_coverage:.0f}%."
        )

        priority_queries.append(
            PriorityQuery(
                query_id=query_id,
                query_text=query_text,
                score=score,
                reason=reason,
                competitors_cited=[],
                relevant_urls=[],
            )
        )

    priority_queries.sort(key=lambda x: x.score, reverse=True)

    return {
        "mode": "live",
        "run_id": data.get("run_id", live_file.stem),
        "queries": [q.to_dict() for q in priority_queries[:top_k]],
    }


def prioritize(mode: str, data_dir: pathlib.Path, top_k: int = 15) -> Dict[str, Any]:
    if mode == "live":
        return prioritize_live(data_dir, top_k)
    return prioritize_experimental(data_dir, top_k)
