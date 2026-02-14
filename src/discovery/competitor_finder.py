"""Discover real competitors by querying live LLMs and extracting cited sources.

Asks the 15 fixed queries to ChatGPT and Gemini, extracts the URLs they cite,
and ranks them by frequency. The result is saved as frozen_competitors.json
and used as the fixed competitor set for all experimental runs.
See ADR-004 in docs/DECISIONS.md.
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
    """Queries live LLMs to discover which sources they cite for the target queries."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is None:
            from src.config import load_experiment_config

            config = load_experiment_config()

        self.config = config
        live = config.get("live_evaluation", {})
        self._chatgpt_model = live.get("chatgpt_model", "gpt-4o")
        self._gemini_model = live.get("gemini_model", "gemini-2.0-flash")

        # Initialize LLM clients once (not per query)
        self._chatgpt = None
        self._gemini = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover_competitors(
        self, queries: List[str], delay: float = 2.0
    ) -> Dict[str, Any]:
        """Ask each query to ChatGPT and Gemini, extract cited URLs.

        Parameters
        ----------
        queries : list of str
            The queries to send to each engine.
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
            entry: Dict[str, Any] = {}

            # ChatGPT
            chatgpt_resp = self._query_chatgpt(query)
            chatgpt_urls = self._extract_urls(chatgpt_resp)
            entry["chatgpt"] = {
                "response": chatgpt_resp,
                "urls_cited": chatgpt_urls,
            }
            all_urls.extend(chatgpt_urls)

            time.sleep(delay)

            # Gemini
            gemini_resp = self._query_gemini(query)
            gemini_urls = self._extract_urls(gemini_resp)
            entry["gemini"] = {
                "response": gemini_resp,
                "urls_cited": gemini_urls,
            }
            all_urls.extend(gemini_urls)

            per_query[query] = entry

            if i < len(queries) - 1:
                time.sleep(delay)

        # Aggregate
        aggregated = self._aggregate_urls(all_urls, per_query)

        return {
            "discovery_date": datetime.now().isoformat(),
            "engines_used": ["chatgpt", "gemini"],
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
    # LLM queries
    # ------------------------------------------------------------------

    def _query_chatgpt(self, query: str) -> str:
        """Send query to ChatGPT and return the response text."""
        try:
            if self._chatgpt is None:
                from langchain_openai import ChatOpenAI

                self._chatgpt = ChatOpenAI(model=self._chatgpt_model, temperature=0.0)
            llm = self._chatgpt
            system = (
                "Eres un asistente que responde preguntas citando fuentes web. "
                "Incluye las URLs completas de las fuentes que uses en tu respuesta."
            )
            response = llm.invoke(
                [("system", system), ("human", query)]
            )
            return response.content
        except Exception as exc:
            logger.error("ChatGPT query failed: %s", exc)
            return ""

    def _query_gemini(self, query: str) -> str:
        """Send query to Gemini and return the response text."""
        try:
            if self._gemini is None:
                from langchain_google_genai import ChatGoogleGenerativeAI

                self._gemini = ChatGoogleGenerativeAI(
                    model=self._gemini_model, temperature=0.0
                )
            llm = self._gemini
            system = (
                "Eres un asistente que responde preguntas citando fuentes web. "
                "Incluye las URLs completas de las fuentes que uses en tu respuesta."
            )
            response = llm.invoke(
                [("system", system), ("human", query)]
            )
            return response.content
        except Exception as exc:
            logger.error("Gemini query failed: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # URL extraction
    # ------------------------------------------------------------------

    def _extract_urls(self, text: str) -> List[str]:
        """Find all URLs in text, clean and deduplicate them."""
        if not text:
            return []

        raw_urls = _URL_PATTERN.findall(text)
        cleaned = []
        seen = set()

        for url in raw_urls:
            url = _TRAILING_PUNCT.sub("", url).rstrip("/")
            domain = urlparse(url).netloc.replace("www.", "")

            if domain in _EXCLUDED_DOMAINS:
                continue
            if url in seen:
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
            for engine in ("chatgpt", "gemini"):
                for url in data.get(engine, {}).get("urls_cited", []):
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