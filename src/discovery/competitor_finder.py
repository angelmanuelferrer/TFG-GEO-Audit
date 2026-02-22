"""Discover real competitors by querying Claude with web search.

Asks the 15 fixed queries to Claude (with web search enabled), extracts the URLs
it cites, and ranks them by frequency. The result is saved as frozen_competitors.json
and used as the fixed competitor set for all experimental runs.
See ADR-004 and ADR-009 in docs/DECISIONS.md.
"""

from __future__ import annotations

import json
import logging
import re
import time
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_URL_PATTERN = re.compile(r"https?://[^\s\)\]\"\' <>]+")
_TRAILING_PUNCT = re.compile(r"[.,;:!?\)]+$")

# Domains to exclude (not real competitors)
_EXCLUDED_DOMAINS = {
    "google.com",
    "youtube.com",
    "wikipedia.org",
    "facebook.com",
    "twitter.com",
    "instagram.com",
    "linkedin.com",
    "amazon.com",
    "github.com",
}


class CompetitorFinder:
    """Queries Claude with web search to discover which sources it cites."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is None:
            from src.config import load_experiment_config

            config = load_experiment_config()

        self.config = config
        live = config.get("live_evaluation", {})
        self._claude_model = live.get("claude_model", "claude-sonnet-4-5-20250929")
        self._client = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover_competitors(
        self, queries: List[str], delay: float = 2.0
    ) -> Dict[str, Any]:
        """Ask each query to Claude with web search, extract cited URLs.

        Parameters
        ----------
        queries : list of str
            The queries to send to Claude.
        delay : float
            Seconds to wait between API calls (rate limiting).

        Returns
        -------
        dict with keys: discovery_date, engines_used, per_query, aggregated_urls,
        top_competitors.
        """
        per_query: Dict[str, Dict[str, Any]] = {}
        all_urls: List[str] = []

        for i, query in enumerate(queries):
            logger.info("Query %d/%d: %s", i + 1, len(queries), query[:60])

            result = self._query_claude(query)
            text_urls = self._extract_urls(result["text"])

            # Citation URLs come from web search citations (higher quality)
            citation_urls = []
            for u in result.get("citation_urls", []):
                cleaned = self._clean_url(u)
                if cleaned:
                    citation_urls.append(cleaned)

            # Combine: citation URLs first (verified by search), then text URLs
            combined = list(dict.fromkeys(citation_urls + text_urls))

            per_query[query] = {
                "claude": {
                    "response": result["text"],
                    "urls_cited": combined,
                    "search_urls": result.get("search_urls", []),
                    "citation_urls": citation_urls,
                }
            }
            all_urls.extend(combined)

            if i < len(queries) - 1:
                time.sleep(delay)

        # Aggregate
        aggregated = self._aggregate_urls(all_urls, per_query)

        return {
            "discovery_date": datetime.now().isoformat(),
            "engines_used": ["claude"],
            "per_query": per_query,
            "aggregated_urls": aggregated,
            "top_competitors": [u["url"] for u in aggregated[:15]],
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

    def _query_claude(self, query: str) -> Dict[str, Any]:
        """Send query to Claude with web search and return structured data."""
        try:
            if self._client is None:
                import anthropic

                self._client = anthropic.Anthropic()

            response = self._client.messages.create(
                model=self._claude_model,
                max_tokens=2000,
                tools=[
                    {
                        "type": "web_search_20250305",
                        "name": "web_search",
                        "max_uses": 5,
                        "user_location": {
                            "type": "approximate",
                            "country": "ES",
                            "timezone": "Europe/Madrid",
                        },
                    }
                ],
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Responde a la siguiente pregunta citando fuentes web "
                            "reales con sus URLs completas. Prioriza fuentes en "
                            "español.\n\n"
                            f"Pregunta: {query}"
                        ),
                    }
                ],
            )

            text = ""
            search_urls = []
            citation_urls = []

            for block in response.content:
                if block.type == "text":
                    text += block.text
                    if hasattr(block, "citations") and block.citations:
                        for citation in block.citations:
                            if hasattr(citation, "url") and citation.url:
                                citation_urls.append(citation.url)
                elif block.type == "web_search_tool_result":
                    if isinstance(block.content, list):
                        for result in block.content:
                            if hasattr(result, "url"):
                                search_urls.append(result.url)

            logger.info(
                "Claude response: %d chars, %d search URLs, %d citation URLs",
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
            logger.error("Claude query failed: %s", exc)
            return {"text": "", "search_urls": [], "citation_urls": []}

    # ------------------------------------------------------------------
    # URL extraction
    # ------------------------------------------------------------------

    def _clean_url(self, url: str) -> Optional[str]:
        """Clean a URL and return None if it should be excluded."""
        url = _TRAILING_PUNCT.sub("", url).rstrip("/")
        domain = urlparse(url).netloc.replace("www.", "")
        if domain in _EXCLUDED_DOMAINS or not domain:
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

    def _aggregate_urls(
        self,
        all_urls: List[str],
        per_query: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Rank URLs by frequency and annotate with query appearances."""
        freq = Counter(all_urls)
        # Map URL -> list of queries where it appeared
        url_queries: Dict[str, List[str]] = {}
        for query, data in per_query.items():
            for url in data.get("claude", {}).get("urls_cited", []):
                url_queries.setdefault(url, [])
                if query not in url_queries[url]:
                    url_queries[url].append(query)

        aggregated = []
        for url, count in freq.most_common():
            domain = urlparse(url).netloc.replace("www.", "")
            aggregated.append(
                {
                    "url": url,
                    "domain": domain,
                    "frequency": count,
                    "queries_appeared_in": url_queries.get(url, []),
                }
            )

        return aggregated
