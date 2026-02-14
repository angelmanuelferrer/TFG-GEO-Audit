"""HTML-aware web scraping with noise removal and markdown conversion.

Replaces LangChain's basic WebBaseLoader with structured content extraction
that removes navigation, footers, scripts, and ads.
See ADR-007 in docs/DECISIONS.md.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup, Tag
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

_NOISE_TAGS = ["nav", "footer", "script", "style", "aside", "header", "noscript"]
_NOISE_SELECTORS = [
    ".ad",
    ".advertisement",
    ".sidebar",
    ".social-share",
    ".cookie-banner",
    ".popup",
    "#comments",
    ".menu",
    ".breadcrumb",
]


class StructuredWebLoader:
    """Downloads a URL, cleans HTML noise, and returns structured Documents."""

    def __init__(
        self,
        url: str,
        user_agent: Optional[str] = None,
        timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        self.url = url
        self.user_agent = user_agent or os.getenv(
            "USER_AGENT", "GeoAuditBot/1.0 (TFG Research)"
        )
        self.timeout = timeout
        self.max_retries = max_retries

    def load(self) -> List[Document]:
        """Download, clean, and convert the page to a Document list."""
        html = self._download_with_retry()
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        metadata = self._extract_metadata(soup)
        soup = self._clean_html(soup)
        main = self._extract_main_content(soup)
        markdown = self._html_to_markdown(main)

        if not markdown.strip():
            logger.warning("No content extracted from %s", self.url)
            return []

        metadata.update(
            {
                "source_url": self.url,
                "loader": "StructuredWebLoader",
                "timestamp": time.time(),
            }
        )

        return [Document(page_content=markdown, metadata=metadata)]

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def _download_with_retry(self) -> Optional[str]:
        """GET the URL with exponential backoff. Returns HTML string or None."""
        headers = {"User-Agent": self.user_agent}

        for attempt in range(self.max_retries):
            try:
                resp = requests.get(
                    self.url, headers=headers, timeout=self.timeout
                )
                resp.raise_for_status()
                if resp.encoding is None or "charset" not in resp.headers.get(
                    "content-type", ""
                ):
                    resp.encoding = resp.apparent_encoding
                return resp.text
            except requests.RequestException as exc:
                wait = min(2**attempt, 30)
                logger.warning(
                    "Attempt %d/%d failed for %s: %s. Retry in %ds",
                    attempt + 1,
                    self.max_retries,
                    self.url,
                    exc,
                    wait,
                )
                if attempt < self.max_retries - 1:
                    time.sleep(wait)

        logger.error("All %d attempts failed for %s", self.max_retries, self.url)
        return None

    # ------------------------------------------------------------------
    # HTML cleaning
    # ------------------------------------------------------------------

    def _clean_html(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove noise tags and CSS-selected containers."""
        for tag_name in _NOISE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        for selector in _NOISE_SELECTORS:
            for el in soup.select(selector):
                el.decompose()

        return soup

    def _extract_main_content(self, soup: BeautifulSoup) -> Tag:
        """Find the main content area of the page."""
        for semantic in ["main", "article"]:
            found = soup.find(semantic)
            if found:
                return found

        # Fallback: div with the most paragraph text
        divs = soup.find_all("div")
        if divs:
            return max(
                divs,
                key=lambda d: len(d.get_text(strip=True)),
            )

        return soup.body if soup.body else soup

    # ------------------------------------------------------------------
    # Markdown conversion
    # ------------------------------------------------------------------

    def _html_to_markdown(self, element: Tag) -> str:
        """Convert an HTML element tree to markdown, preserving structure."""
        lines: List[str] = []
        self._walk(element, lines)
        text = "\n\n".join(line for line in lines if line)
        # Collapse excessive blank lines
        while "\n\n\n" in text:
            text = text.replace("\n\n\n", "\n\n")
        return text.strip()

    def _walk(self, element: Tag, lines: List[str]) -> None:
        """Recursively walk the element tree and build markdown lines."""
        for child in element.children:
            if isinstance(child, str):
                stripped = child.strip()
                if stripped:
                    lines.append(stripped)
                continue

            if not isinstance(child, Tag):
                continue

            name = child.name

            if name in ("h1", "h2", "h3", "h4"):
                level = int(name[1])
                text = child.get_text(strip=True)
                if text:
                    lines.append("#" * level + " " + text)

            elif name == "p":
                text = child.get_text(strip=True)
                if text:
                    lines.append(text)

            elif name in ("ul", "ol"):
                for li in child.find_all("li", recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        lines.append("- " + text)

            elif name == "a":
                text = child.get_text(strip=True)
                href = child.get("href", "")
                if text and href and href.startswith("http"):
                    lines.append(f"[{text}]({href})")

            elif name == "blockquote":
                text = child.get_text(strip=True)
                if text:
                    lines.append("> " + text)

            elif name in ("pre", "code"):
                text = child.get_text()
                if text.strip():
                    lines.append("```\n" + text.strip() + "\n```")

            elif name in ("strong", "b"):
                text = child.get_text(strip=True)
                if text:
                    lines.append(f"**{text}**")

            elif name in ("em", "i"):
                text = child.get_text(strip=True)
                if text:
                    lines.append(f"*{text}*")

            elif name in ("dl",):
                for dt in child.find_all("dt", recursive=False):
                    text = dt.get_text(strip=True)
                    if text:
                        lines.append(f"**{text}**")
                for dd in child.find_all("dd", recursive=False):
                    text = dd.get_text(strip=True)
                    if text:
                        lines.append(f": {text}")

            elif name in ("div", "section", "span", "figure", "article", "main"):
                self._walk(child, lines)

    # ------------------------------------------------------------------
    # Metadata extraction
    # ------------------------------------------------------------------

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract title, description, and JSON-LD schema from the page."""
        metadata: Dict[str, Any] = {}

        title_tag = soup.find("title")
        if title_tag:
            metadata["title"] = title_tag.get_text(strip=True)

        desc = soup.find("meta", attrs={"name": "description"})
        if desc:
            metadata["description"] = desc.get("content", "")

        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title:
            metadata["og_title"] = og_title.get("content", "")

        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc:
            metadata["og_description"] = og_desc.get("content", "")

        schema_tags = soup.find_all("script", type="application/ld+json")
        if schema_tags:
            try:
                metadata["schema_org"] = json.loads(schema_tags[0].string)
            except (json.JSONDecodeError, TypeError):
                pass

        return metadata