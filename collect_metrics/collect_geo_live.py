#!/usr/bin/env python3
"""Live GEO evaluation: measure real visibility in AI generative engines.

Queries Gemini 2.5 Flash, Claude Haiku 4.5 and GPT-4o-mini with web search
enabled and measures whether programamos.es is cited in the responses.

Usage:
    python collect_metrics/collect_geo_live.py
    python collect_metrics/collect_geo_live.py --engines gemini --tier core
    python collect_metrics/collect_geo_live.py --engines gemini claude openai --tier light
    python collect_metrics/collect_geo_live.py --engines gemini claude openai \
        --engine-tiers gemini=full claude=light openai=medium
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from src.config import get_target_brand, get_target_url, load_queries
from src.rag.citation_extractor import CitationExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

_RATE_LIMIT_DELAY = 2.0
_GROUNDING_PROXY_DOMAIN = "vertexaisearch.cloud.google.com"
_TIER_RANK = {"core": 0, "light": 1, "medium": 2, "full": 3}


# ---------------------------------------------------------------------------
# Query loading
# ---------------------------------------------------------------------------


def _get_queries_with_ids(tier: str) -> List[Dict[str, str]]:
    """Return list of {id, text, category} for the given tier.

    Tiers:
        core   → 20 queries (always)
        light  → 40 queries (core + R1)
        medium → 60 queries (core + R1 + R2)
        full   → 100 queries (all)
    """
    data = load_queries()
    queries_db = data.get("queries", {})
    rotation = data.get("rotation", {})

    if tier == "full":
        ids = list(queries_db.keys())
    elif tier == "medium":
        ids = rotation.get("core", []) + rotation.get("R1", []) + rotation.get("R2", [])
    elif tier == "light":
        ids = rotation.get("core", []) + rotation.get("R1", [])
    else:  # core
        ids = rotation.get("core", list(queries_db.keys())[:20])

    return [
        {
            "id": qid,
            "text": queries_db[qid]["text"],
            "category": queries_db[qid].get("category", ""),
        }
        for qid in ids
        if qid in queries_db
    ]


# ---------------------------------------------------------------------------
# Delta tracking
# ---------------------------------------------------------------------------


def _load_prev_week_results(out_dir: Path, current_run_id: str) -> Optional[Dict]:
    """Return the results list from the most recent previous run file, or None."""
    files = sorted(out_dir.glob("LIVE-*.json"))
    for f in reversed(files):
        if current_run_id not in f.name:
            try:
                with open(f, encoding="utf-8") as fh:
                    return json.load(fh)
            except Exception as exc:
                logger.warning("Could not load prev week file %s: %s", f.name, exc)
    return None


def _compute_delta(current_results: List[Dict], prev_results: List[Dict]) -> Dict:
    """Compare is_visible per query/engine between current and previous week.

    Returns a dict keyed by engine with lists: gained, lost, stable_visible,
    stable_invisible. Only queries evaluated in both runs are compared.
    """
    prev_by_query = {r["query_id"]: r for r in prev_results}
    delta: Dict[str, Dict[str, List[str]]] = {}

    for result in current_results:
        qid = result["query_id"]
        if qid not in prev_by_query:
            continue
        for engine, metrics in result.get("engines", {}).items():
            prev_engine = prev_by_query[qid].get("engines", {}).get(engine)
            if prev_engine is None:
                continue
            curr_vis = metrics.get("is_visible", False)
            prev_vis = prev_engine.get("is_visible", False)

            if engine not in delta:
                delta[engine] = {
                    "gained": [],
                    "lost": [],
                    "stable_visible": [],
                    "stable_invisible": [],
                }

            if curr_vis and not prev_vis:
                delta[engine]["gained"].append(qid)
            elif not curr_vis and prev_vis:
                delta[engine]["lost"].append(qid)
            elif curr_vis and prev_vis:
                delta[engine]["stable_visible"].append(qid)
            else:
                delta[engine]["stable_invisible"].append(qid)

    return delta


# ---------------------------------------------------------------------------
# Sentiment Analyzer
# ---------------------------------------------------------------------------


class SentimentAnalyzer:
    """Classify brand mention sentiment using gemini-2.0-flash-lite."""

    _MODEL = "gemini-2.0-flash"
    _PROMPT = (
        "Clasifica el sentimiento con el que este motor de IA menciona la marca "
        '"Programamos" en su respuesta. '
        "Responde únicamente con una palabra: POSITIVO, NEUTRO o NEGATIVO.\n\n"
        "Contexto: {context}"
    )

    def __init__(self) -> None:
        self._client = None

    def classify(self, brand_mentions: List[Dict]) -> Optional[str]:
        """Return POSITIVO / NEUTRO / NEGATIVO, or None if no mentions."""
        if not brand_mentions:
            return None

        from google import genai

        if self._client is None:
            self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        context = " | ".join(m["context"] for m in brand_mentions)
        prompt = self._PROMPT.format(context=context)

        try:
            response = self._client.models.generate_content(
                model=self._MODEL,
                contents=prompt,
            )
            result = (response.text or "").strip().upper()
            if result in ("POSITIVO", "NEUTRO", "NEGATIVO"):
                return result
            # Fallback: check if any keyword appears
            for label in ("POSITIVO", "NEUTRO", "NEGATIVO"):
                if label in result:
                    return label
            return "NEUTRO"
        except Exception as exc:
            logger.warning("Sentiment classification failed: %s", exc)
            return None


# ---------------------------------------------------------------------------
# Live Evaluator
# ---------------------------------------------------------------------------


class LiveEvaluator:
    """Query AI engines with web search and extract GEO visibility metrics."""

    def __init__(self) -> None:
        self._gemini_model = "gemini-2.5-flash"
        self._claude_model = "claude-haiku-4-5-20251001"
        self._openai_model = "gpt-4o-mini"
        self._extractor = CitationExtractor(get_target_url(), get_target_brand())
        self._sentiment = SentimentAnalyzer()

        self._gemini_client = None
        self._anthropic_client = None
        self._openai_client = None

    # ------------------------------------------------------------------
    # Gemini 2.5 Flash — Google Search grounding
    # ------------------------------------------------------------------

    def _resolve_proxy_url(self, url: str) -> Optional[str]:
        if _GROUNDING_PROXY_DOMAIN not in url:
            return url
        try:
            import requests
            resp = requests.head(url, allow_redirects=False, timeout=5)
            location = resp.headers.get("Location", "")
            if location.startswith("http"):
                return location
        except Exception as exc:
            logger.debug("Failed to resolve proxy %s: %s", url[:80], exc)
        return None

    def _query_gemini(self, query: str) -> Dict[str, Any]:
        from google import genai
        from google.genai import types

        if self._gemini_client is None:
            self._gemini_client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

        for attempt in range(3):
            try:
                response = self._gemini_client.models.generate_content(
                    model=self._gemini_model,
                    contents=query,
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    ),
                )

                text = response.text or ""
                search_urls: List[str] = []
                citation_urls: List[str] = []

                grounding = getattr(response.candidates[0], "grounding_metadata", None)
                if grounding:
                    chunks = getattr(grounding, "grounding_chunks", None) or []
                    for chunk in chunks:
                        web = getattr(chunk, "web", None)
                        if web and getattr(web, "uri", None):
                            url = self._resolve_proxy_url(web.uri)
                            if url and url not in search_urls:
                                search_urls.append(url)

                    cited_indices: set = set()
                    for support in getattr(grounding, "grounding_supports", None) or []:
                        for idx in getattr(support, "grounding_chunk_indices", None) or []:
                            cited_indices.add(idx)
                    for idx in sorted(cited_indices):
                        if idx < len(chunks):
                            web = getattr(chunks[idx], "web", None)
                            if web and getattr(web, "uri", None):
                                url = self._resolve_proxy_url(web.uri)
                                if url and url not in citation_urls:
                                    citation_urls.append(url)

                unused = [u for u in search_urls if u not in citation_urls]
                return {
                    "answer": text,
                    "citations": [{"index": i + 1, "url": u, "quote": ""} for i, u in enumerate(citation_urls)],
                    "sources_used": citation_urls,
                    "sources_available_but_unused": unused,
                }

            except Exception as exc:
                wait = 30.0 * (attempt + 1)
                if attempt < 2:
                    logger.warning("Gemini attempt %d/3 failed: %s. Retrying in %.0fs...", attempt + 1, exc, wait)
                    time.sleep(wait)
                else:
                    logger.error("Gemini query failed after 3 attempts: %s", exc)

        return {"answer": "", "citations": [], "sources_used": [], "sources_available_but_unused": []}

    # ------------------------------------------------------------------
    # Claude Haiku 4.5 — web_search_20250305 tool
    # ------------------------------------------------------------------

    def _query_claude(self, query: str) -> Dict[str, Any]:
        import anthropic

        if self._anthropic_client is None:
            self._anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

        try:
            response = self._anthropic_client.messages.create(
                model=self._claude_model,
                max_tokens=1500,
                tools=[{"type": "web_search_20250305", "name": "web_search"}],
                messages=[{"role": "user", "content": query}],
            )

            answer = ""
            search_urls: List[str] = []

            for block in response.content:
                block_type = getattr(block, "type", "")
                if block_type == "text":
                    answer += getattr(block, "text", "")
                elif block_type == "tool_result":
                    for result in getattr(block, "content", None) or []:
                        url = getattr(result, "url", None)
                        if url and url not in search_urls:
                            search_urls.append(url)

            citations = [{"index": i + 1, "url": u, "quote": ""} for i, u in enumerate(search_urls)]
            return {
                "answer": answer,
                "citations": citations,
                "sources_used": search_urls,
                "sources_available_but_unused": [],
            }

        except Exception as exc:
            logger.error("Claude query failed: %s", exc)
            return {"answer": "", "citations": [], "sources_used": [], "sources_available_but_unused": []}

    # ------------------------------------------------------------------
    # GPT-4o-mini — web_search_preview (OpenAI Responses API)
    # ------------------------------------------------------------------

    def _query_openai(self, query: str) -> Dict[str, Any]:
        from openai import OpenAI

        if self._openai_client is None:
            self._openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

        try:
            response = self._openai_client.responses.create(
                model=self._openai_model,
                tools=[{"type": "web_search_preview"}],
                input=query,
            )

            answer = response.output_text
            citation_urls: List[str] = []

            for item in response.output:
                for content in getattr(item, "content", None) or []:
                    for ann in getattr(content, "annotations", None) or []:
                        if getattr(ann, "type", "") == "url_citation":
                            url = getattr(ann, "url", "")
                            if url and url not in citation_urls:
                                citation_urls.append(url)

            citations = [{"index": i + 1, "url": u, "quote": ""} for i, u in enumerate(citation_urls)]
            return {
                "answer": answer,
                "citations": citations,
                "sources_used": citation_urls,
                "sources_available_but_unused": [],
            }

        except Exception as exc:
            logger.error("OpenAI query failed: %s", exc)
            return {"answer": "", "citations": [], "sources_used": [], "sources_available_but_unused": []}

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    _ENGINE_METHODS: Dict[str, str] = {
        "gemini": "_query_gemini",
        "claude": "_query_claude",
        "openai": "_query_openai",
    }

    def run(
        self,
        queries: List[Dict[str, str]],
        engines: List[str],
        engine_tier_map: Dict[str, str],
        tier_query_ids: Dict[str, set],
    ) -> Dict[str, Any]:
        """Evaluate all queries across the requested engines.

        engine_tier_map: {engine -> tier}, e.g. {"gemini": "full", "claude": "light"}
        tier_query_ids:  {tier -> set of query IDs} for fast per-engine filtering
        """
        results = []
        totals: Dict[str, Dict] = {
            e: {"visible": 0, "total": 0, "som_sum": 0.0, "rank_sum": 0.0, "rank_count": 0}
            for e in engines
        }

        for i, q in enumerate(queries, 1):
            # Only run engines whose tier includes this query
            engines_for_query = [
                e for e in engines
                if q["id"] in tier_query_ids[engine_tier_map[e]]
            ]
            if not engines_for_query:
                continue

            print(f"\n[{i}/{len(queries)}] {q['text'][:70]}...")
            engine_results: Dict[str, Any] = {}

            for engine in engines_for_query:
                method = getattr(self, self._ENGINE_METHODS[engine])
                try:
                    judge_output = method(q["text"])
                    metrics = self._extractor.extract_metrics(judge_output)

                    # Remove metrics that don't apply in live mode
                    metrics.pop("pawc", None)
                    metrics.pop("citation_rate", None)

                    # Sentiment — only when visible and there are brand mentions
                    if metrics.get("is_visible"):
                        metrics["sentiment"] = self._sentiment.classify(
                            metrics.get("brand_mentions", [])
                        )
                    else:
                        metrics["sentiment"] = None

                    engine_results[engine] = metrics

                    t = totals[engine]
                    t["total"] += 1
                    if metrics.get("is_visible"):
                        t["visible"] += 1
                    t["som_sum"] += metrics.get("som", 0.0)
                    rank = metrics.get("first_citation_rank")
                    if rank is not None:
                        t["rank_sum"] += rank
                        t["rank_count"] += 1

                    label = "VISIBLE" if metrics["is_visible"] else "not visible"
                    sentiment_label = f" | {metrics['sentiment']}" if metrics["sentiment"] else ""
                    print(
                        f"  [{engine:8s}] {label} | "
                        f"SoM={metrics['som']}% | "
                        f"Citations={metrics['target_citations']}/{metrics['total_citations']}"
                        f"{sentiment_label}"
                    )

                except Exception as exc:
                    logger.error("Engine %s failed on %s: %s", engine, q["id"], exc)
                    engine_results[engine] = {"error": str(exc)}

                time.sleep(_RATE_LIMIT_DELAY)

            # Engine Coverage — denominator = engines that actually evaluated this query
            n_visible = sum(
                1 for e in engines_for_query
                if engine_results.get(e, {}).get("is_visible", False)
            )
            engine_coverage = round(n_visible / len(engines_for_query) * 100, 2)

            results.append({
                "query_id": q["id"],
                "query_text": q["text"],
                "query_category": q["category"],
                "engine_coverage": engine_coverage,
                "engines": engine_results,
            })

        # Per-engine summary
        summary = {
            e: {
                "visibility_rate": round(t["visible"] / t["total"] * 100, 2) if t["total"] else 0.0,
                "avg_som": round(t["som_sum"] / t["total"], 2) if t["total"] else 0.0,
                "avg_first_rank": round(t["rank_sum"] / t["rank_count"], 2) if t["rank_count"] else None,
                "n_queries": t["total"],
                "n_visible": t["visible"],
            }
            for e, t in totals.items()
        }

        # Global engine coverage average
        engine_coverage_avg = round(mean(r["engine_coverage"] for r in results), 2)

        return {"results": results, "summary": summary, "engine_coverage_avg": engine_coverage_avg}


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Live GEO evaluation across AI generative engines"
    )
    parser.add_argument(
        "--engines",
        nargs="+",
        default=["gemini", "claude", "openai"],
        choices=["gemini", "claude", "openai"],
        help="Engines to query (default: all three)",
    )
    parser.add_argument(
        "--tier",
        default="core",
        choices=["core", "light", "medium", "full"],
        help="Single tier for all engines — core=20, light=40, medium=60, full=100 (default: core)",
    )
    parser.add_argument(
        "--engine-tiers",
        nargs="+",
        metavar="ENGINE=TIER",
        help="Per-engine tiers, e.g. gemini=full claude=light openai=medium. "
             "Overrides --tier when specified.",
    )
    args = parser.parse_args()

    # Build engine→tier map (per-engine takes precedence over global --tier)
    if args.engine_tiers:
        engine_tier_map = dict(pair.split("=") for pair in args.engine_tiers)
    else:
        engine_tier_map = {e: args.tier for e in args.engines}

    # Load union of queries (max tier) and precompute ID sets per tier
    max_tier = max(engine_tier_map.values(), key=lambda t: _TIER_RANK[t])
    all_queries = _get_queries_with_ids(max_tier)
    tier_query_ids: Dict[str, set] = {
        tier: {q["id"] for q in _get_queries_with_ids(tier)}
        for tier in set(engine_tier_map.values())
    }

    now = datetime.now(timezone.utc)
    week = now.isocalendar()[1]
    run_id = f"LIVE-{now.year}-W{week:02d}"

    print(f"\n=== Live GEO Evaluation: {run_id} ===")
    print(f"Engines : {', '.join(args.engines)}")
    for engine, tier in engine_tier_map.items():
        print(f"  {engine:8s} → {tier} ({len(tier_query_ids[tier])} queries)")
    print(f"Total unique queries: {len(all_queries)}")

    evaluator = LiveEvaluator()
    run_data = evaluator.run(all_queries, args.engines, engine_tier_map, tier_query_ids)

    out_dir = PROJECT_ROOT / "data" / "geo" / "live"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Delta vs previous week
    prev_data = _load_prev_week_results(out_dir, run_id)
    delta = _compute_delta(run_data["results"], prev_data["results"]) if prev_data else None

    output = {
        "run_id": run_id,
        "timestamp": now.isoformat(),
        "engines": args.engines,
        "engine_tiers": engine_tier_map,
        "n_queries": len(all_queries),
        **run_data,
        "delta_vs_prev_week": delta,
    }

    out_path = out_dir / f"{run_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n=== Summary ===")
    for engine, stats in run_data["summary"].items():
        rank_str = f" | avg rank={stats['avg_first_rank']}" if stats["avg_first_rank"] else ""
        print(
            f"  {engine:8s} → {stats['visibility_rate']}% visible | "
            f"avg SoM={stats['avg_som']}%"
            f"{rank_str} | "
            f"{stats['n_visible']}/{stats['n_queries']} queries"
        )
    print(f"  Engine Coverage avg: {run_data['engine_coverage_avg']}%")

    if delta:
        print(f"\n=== Delta vs semana anterior ({prev_data['run_id']}) ===")
        for engine, d in delta.items():
            print(
                f"  {engine:8s} → +{len(d['gained'])} ganadas | "
                f"-{len(d['lost'])} perdidas | "
                f"{len(d['stable_visible'])} estables visibles"
            )
    else:
        print("\n(Sin semana anterior para comparar — primera ejecución)")

    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
