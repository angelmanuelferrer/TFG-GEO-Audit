"""Discover real competitors by querying Gemini with Google Search grounding.

Asks the discovery queries (informational + comparative, no navigational) to Gemini
with Google Search enabled, extracts the URLs it cites via grounding metadata, and
ranks them by domain frequency. The result is saved as frozen_competitors.json and
used as the fixed competitor set for all experimental runs.
See ADR-004 and ADR-010 in docs/DECISIONS.md.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests as _requests

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(r"https?://[^\s\)\]\"\' <>]+")

# Domains to exclude (not real competitors)
_EXCLUDED_DOMAINS = {
    # Social / general platforms
    "google.com",
    "youtube.com",
    "wikipedia.org",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "linkedin.com",
    "amazon.com",
    "github.com",
    "godaddy.com",
    "reddit.com",
    "medium.com",
    "sites.google.com",
    # Not educational programming competitors
    "lenovo.com",
    "xataka.com",
    "bluehost.com",
}

# Gemini grounding infrastructure domains (not real sources)
_GROUNDING_PROXY_DOMAINS = {
    "vertexaisearch.cloud.google.com",
    "vertexaisearch.google.com",
}

# Citation URLs get more weight than text-extracted URLs
_CITATION_WEIGHT = 2
_TEXT_WEIGHT = 1


class CompetitorFinder:
    """Queries Gemini with Google Search grounding to discover which sources it cites."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is None:
            from src.config import load_experiment_config

            config = load_experiment_config()

        self.config = config
        self._target_domain = (
            urlparse(config["target_url"]).netloc.replace("www.", "")
        )
        discovery = config.get("discovery", {})
        self._gemini_model = discovery.get("model", "gemini-2.5-flash")
        self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover_competitors(
        self, queries: List[str], delay: float = 2.0
    ) -> Dict[str, Any]:
        """Ask each query to Gemini with Google Search grounding, extract cited URLs.

        Parameters
        ----------
        queries : list of str
            The queries to send to Gemini (should be discovery queries only,
            i.e. informational + comparative, no navigational).
        delay : float
            Seconds to wait between API calls (rate limiting).
            Default 2s for Gemini free tier (15 RPM).

        Returns
        -------
        dict with keys: discovery_date, engines_used, n_queries, per_query,
        aggregated_domains, top_competitors.
        """
        per_query: Dict[str, Dict[str, Any]] = {}

        for i, query in enumerate(queries):
            print(f"[{i+1}/{len(queries)}] {query[:60]}…", flush=True)

            result = self._query_gemini(query)
            text_urls = self._extract_urls(result["text"])

            # Citation URLs from grounding metadata (resolved from proxies)
            citation_urls = []
            for u in result.get("citation_urls", []):
                cleaned = self._clean_url(u)
                if cleaned:
                    citation_urls.append(cleaned)

            # Combine: citation URLs first (verified by search), then text URLs
            combined = list(dict.fromkeys(citation_urls + text_urls))

            print(
                f"  → {len(result['text'])} chars, "
                f"{len(citation_urls)} citations, "
                f"{len(text_urls)} text URLs, "
                f"{len(combined)} total unique",
                flush=True,
            )
            print(f"  Respuesta: {result['text'][:300]}…", flush=True)
            if combined:
                print(f"  URLs: {', '.join(combined[:5])}", flush=True)

            per_query[query] = {
                "gemini": {
                    "response": result["text"],
                    "urls_cited": combined,
                    "search_urls": result.get("search_urls", []),
                    "citation_urls": citation_urls,
                }
            }

            if i < len(queries) - 1:
                time.sleep(delay)

        # Aggregate by domain with weighted scoring
        aggregated = self._aggregate_by_domain(per_query)

        return {
            "discovery_date": datetime.now().isoformat(),
            "engines_used": ["gemini"],
            "n_queries": len(queries),
            "per_query": per_query,
            "aggregated_domains": aggregated,
            "top_competitors": [d["domain"] for d in aggregated[:15]],
        }

    def save_results(self, results: Dict[str, Any], output_path: str) -> None:
        """Save discovery results to a JSON file."""
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        n = len(results.get("top_competitors", []))
        logger.info("Saved %d competitors to %s", n, output_path)

    # ------------------------------------------------------------------
    # LLM query
    # ------------------------------------------------------------------

    def _query_gemini(
        self, query: str, max_retries: int = 5, initial_wait: float = 30.0
    ) -> Dict[str, Any]:
        """Send query to Gemini with Google Search grounding and return structured data.

        Retries with exponential backoff on rate-limit (429 / RESOURCE_EXHAUSTED) errors.
        """
        if self._client is None:
            from google import genai

            self._client = genai.Client()

        from google.genai import types

        wait = initial_wait
        for attempt in range(max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._gemini_model,
                    contents=(
                        "Responde a la siguiente pregunta usando tu herramienta "
                        "de búsqueda. En tu respuesta DEBES incluir las URLs "
                        "completas de cada fuente que utilices, escritas tal cual "
                        "(ejemplo: https://scratch.mit.edu). "
                        "Al final de tu respuesta incluye una sección "
                        "'Fuentes:' con la lista numerada de todas las URLs "
                        "consultadas. Prioriza fuentes en español.\n\n"
                        f"Pregunta: {query}"
                    ),
                    config=types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    ),
                )

                text = response.text or ""
                search_urls = []
                citation_urls = []

                # Extract URLs from grounding metadata
                grounding = getattr(
                    response.candidates[0], "grounding_metadata", None
                )
                if grounding:
                    # search_urls: all sources from grounding chunks
                    chunks = getattr(grounding, "grounding_chunks", None) or []
                    for chunk in chunks:
                        web = getattr(chunk, "web", None)
                        if web and getattr(web, "uri", None):
                            resolved = self._resolve_proxy_url(web.uri)
                            if resolved:
                                search_urls.append(resolved)

                    # citation_urls: only those backing specific claims (weight=2)
                    supports = (
                        getattr(grounding, "grounding_supports", None) or []
                    )
                    cited_indices = set()
                    for support in supports:
                        indices = (
                            getattr(support, "grounding_chunk_indices", None)
                            or []
                        )
                        for idx in indices:
                            cited_indices.add(idx)

                    for idx in sorted(cited_indices):
                        if idx < len(chunks):
                            web = getattr(chunks[idx], "web", None)
                            if web and getattr(web, "uri", None):
                                resolved = self._resolve_proxy_url(web.uri)
                                if resolved:
                                    citation_urls.append(resolved)

                # Deduplicate while preserving order
                citation_urls = list(dict.fromkeys(citation_urls))
                search_urls = list(dict.fromkeys(search_urls))

                logger.info(
                    "Gemini response: %d chars, %d search URLs, %d citation URLs",
                    len(text),
                    len(search_urls),
                    len(citation_urls),
                )

                return {
                    "text": text,
                    "search_urls": search_urls,
                    "citation_urls": citation_urls,
                }

            except Exception as exc:
                exc_str = str(exc)
                is_rate_limit = "429" in exc_str or "RESOURCE_EXHAUSTED" in exc_str

                if is_rate_limit and attempt < max_retries:
                    logger.warning(
                        "Rate limit hit (attempt %d/%d). Waiting %.0fs…",
                        attempt + 1,
                        max_retries,
                        wait,
                    )
                    time.sleep(wait)
                    wait *= 2  # exponential backoff
                elif is_rate_limit:
                    logger.error(
                        "Rate limit exceeded after %d retries: %s",
                        max_retries,
                        exc,
                    )
                    return {"text": "", "search_urls": [], "citation_urls": []}
                else:
                    logger.error("Gemini query failed: %s", exc)
                    return {"text": "", "search_urls": [], "citation_urls": []}

        return {"text": "", "search_urls": [], "citation_urls": []}

    # ------------------------------------------------------------------
    # Proxy URL resolution
    # ------------------------------------------------------------------

    def _resolve_proxy_url(self, url: str) -> Optional[str]:
        """Resolve a vertexaisearch proxy URL to the real destination URL.

        If the URL is not a proxy, returns it as-is.
        Returns None if resolution fails.
        """
        domain = self._get_domain(url)
        if domain not in _GROUNDING_PROXY_DOMAINS:
            return url

        try:
            resp = _requests.head(url, allow_redirects=False, timeout=5)
            location = resp.headers.get("Location")
            if location and location.startswith("http"):
                return location
        except Exception as exc:
            logger.debug("Failed to resolve proxy URL %s: %s", url[:80], exc)

        return None

    # ------------------------------------------------------------------
    # URL extraction & aggregation
    # ------------------------------------------------------------------

    def _get_domain(self, url: str) -> str:
        """Extract clean domain from URL."""
        return urlparse(url).netloc.replace("www.", "")

    def _clean_url(self, url: str) -> Optional[str]:
        """Clean a URL and return None if it should be excluded."""
        url = url.rstrip(".,;:!?)").rstrip("/")
        domain = self._get_domain(url)
        if (
            not domain
            or domain in _EXCLUDED_DOMAINS
            or domain in _GROUNDING_PROXY_DOMAINS
            or domain == self._target_domain
        ):
            return None
        return url

    def _extract_urls(self, text: str) -> List[str]:
        """Find all URLs in text, clean and deduplicate them."""
        if not text:
            return []

        raw_urls = _URL_PATTERN.findall(text)
        cleaned = []
        seen = set()

        for url in raw_urls:
            url = self._clean_url(url)
            if url is None or url in seen:
                continue

            seen.add(url)
            cleaned.append(url)

        return cleaned

    def _aggregate_by_domain(
        self, per_query: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Aggregate URLs by domain with weighted scoring.

        Scoring: citation URLs count 2 points, text-only URLs count 1.
        A domain can only score once per query (max weight for that query).
        """
        # domain -> {score, queries, urls}
        domains: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {"score": 0, "queries": [], "urls": set(), "citation_count": 0}
        )

        for query, data in per_query.items():
            gemini_data = data.get("gemini", {})
            citation_urls = set(gemini_data.get("citation_urls", []))
            all_urls = gemini_data.get("urls_cited", [])

            # Track best weight per domain for this query (avoid double counting)
            domain_best_weight: Dict[str, int] = {}

            for url in all_urls:
                domain = self._get_domain(url)
                if not domain:
                    continue

                weight = _CITATION_WEIGHT if url in citation_urls else _TEXT_WEIGHT
                domain_best_weight[domain] = max(
                    domain_best_weight.get(domain, 0), weight
                )
                domains[domain]["urls"].add(url)

                if url in citation_urls:
                    domains[domain]["citation_count"] += 1

            # Apply scores per domain (one score per query)
            for domain, weight in domain_best_weight.items():
                domains[domain]["score"] += weight
                if query not in domains[domain]["queries"]:
                    domains[domain]["queries"].append(query)

        # Sort by score descending, then by query count
        aggregated = []
        for domain, info in sorted(
            domains.items(), key=lambda x: (x[1]["score"], len(x[1]["queries"])), reverse=True
        ):
            aggregated.append(
                {
                    "domain": domain,
                    "score": info["score"],
                    "n_queries": len(info["queries"]),
                    "citation_count": info["citation_count"],
                    "urls": sorted(info["urls"]),
                    "queries_appeared_in": info["queries"],
                }
            )

        return aggregated
