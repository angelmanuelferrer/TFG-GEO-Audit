"""Extract GEO metrics from the RAG Judge's structured JSON output.

Pure Python -- no external dependencies beyond the standard library.
See ADR-002 in docs/DECISIONS.md.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse


class CitationExtractor:
    """Compute GEO visibility metrics for a target URL/brand.

    Parameters
    ----------
    target_url : str
        The canonical URL to track (e.g. ``"https://programamos.es"``).
    target_brand : str
        Brand name to search for in answer text (e.g. ``"Programamos"``).
    """

    def __init__(self, target_url: str, target_brand: str) -> None:
        self.target_url = target_url
        self.target_brand = target_brand
        self._normalized_target = self._normalize_url(target_url)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract_metrics(self, judge_output: dict) -> Dict[str, Any]:
        """Return a dict of GEO metrics extracted from *judge_output*.

        Expected keys in *judge_output*: ``answer``, ``citations``,
        ``sources_used``, ``sources_available_but_unused``.
        """
        citations: List[dict] = judge_output.get("citations", [])
        answer: str = judge_output.get("answer", "")

        total = len(citations)
        target_count = self._count_target_citations(citations)
        first_rank = self._find_first_citation_rank(citations)
        mentions = self._detect_brand_mentions(answer, citations)

        return {
            "total_citations": total,
            "target_citations": target_count,
            "is_visible": target_count > 0,
            "som": round((target_count / total) * 100, 2) if total > 0 else 0.0,
            "first_citation_rank": first_rank,
            "brand_mentions": mentions,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Strip scheme, ``www.`` prefix, and trailing slash for comparison."""
        parsed = urlparse(url)
        host = parsed.netloc or parsed.path
        host = re.sub(r"^www\.", "", host, count=1)
        path = parsed.path.rstrip("/") if parsed.netloc else ""
        return (host + path).lower()

    def _url_matches_target(self, url: str) -> bool:
        """Check whether *url* belongs to the target domain."""
        normalized = self._normalize_url(url)
        # Ensure exact domain match: after the target string there must be
        # either nothing, a '/', or a '?' — prevents "programamos.es.evil.com".
        if not normalized.startswith(self._normalized_target):
            return False
        remainder = normalized[len(self._normalized_target):]
        return remainder == "" or remainder[0] in ("/", "?", "#")

    def _count_target_citations(self, citations: List[dict]) -> int:
        """Count how many citations reference the target URL."""
        return sum(
            1 for c in citations if self._url_matches_target(c.get("url", ""))
        )

    def _find_first_citation_rank(self, citations: List[dict]) -> Optional[int]:
        """Return 1-indexed rank of the first citation matching the target.

        Citations are ordered by their ``index`` field. Returns ``None``
        when the target is not cited at all.
        """
        sorted_citations = sorted(citations, key=lambda c: c.get("index", 0))
        for position, citation in enumerate(sorted_citations, start=1):
            if self._url_matches_target(citation.get("url", "")):
                return position
        return None

    def _detect_brand_mentions(
        self, answer: str, citations: List[dict]
    ) -> List[Dict[str, Any]]:
        """Find all occurrences of the brand name in *answer* and citation quotes.

        Each mention includes +-50 characters of surrounding context.
        """
        mentions: List[Dict[str, Any]] = []
        pattern = re.compile(re.escape(self.target_brand), re.IGNORECASE)

        for match in pattern.finditer(answer):
            start = max(0, match.start() - 50)
            end = min(len(answer), match.end() + 50)
            mentions.append(
                {
                    "source": "answer",
                    "position": match.start(),
                    "context": answer[start:end],
                }
            )

        for citation in citations:
            quote = citation.get("quote", "")
            for match in pattern.finditer(quote):
                start = max(0, match.start() - 50)
                end = min(len(quote), match.end() + 50)
                mentions.append(
                    {
                        "source": f"citation_{citation.get('index', '?')}",
                        "position": match.start(),
                        "context": quote[start:end],
                    }
                )

        return mentions
