"""Site crawler with sitemap parsing, robots.txt compliance, and BFS fallback.

Crawls entire websites to build representative vectorstores instead of
scraping single URLs. Uses StructuredWebLoader for each page.
"""

from __future__ import annotations

import logging
import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document

from src.processing.html_processor import StructuredWebLoader

logger = logging.getLogger(__name__)

# XML namespaces used in sitemaps
_SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}


@dataclass
class URLInfo:
    """Metadata for a URL discovered from a sitemap."""

    loc: str
    lastmod: Optional[str] = None
    priority: Optional[float] = None
    changefreq: Optional[str] = None
    source: str = "sitemap"  # "sitemap", "bfs", "discovered"


class SitemapParser:
    """Parses sitemap.xml files (including sitemap index files)."""

    def __init__(self, user_agent: str, timeout: int = 10) -> None:
        self.user_agent = user_agent
        self.timeout = timeout

    def parse(self, sitemap_url: str) -> List[URLInfo]:
        """Parse a sitemap URL, handling both index and regular sitemaps."""
        if not sitemap_url.endswith(".xml"):
            logger.debug("Skipping non-XML sitemap: %s", sitemap_url)
            return []

        xml_text = self._fetch(sitemap_url)
        if not xml_text:
            return []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            logger.warning("Failed to parse sitemap XML at %s: %s", sitemap_url, e)
            return []

        tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

        if tag == "sitemapindex":
            return self._parse_index(root)
        elif tag == "urlset":
            return self._parse_urlset(root)
        else:
            logger.warning("Unknown sitemap root tag: %s", root.tag)
            return []

    def _parse_index(self, root: ET.Element) -> List[URLInfo]:
        """Parse a sitemap index and recursively fetch child sitemaps."""
        urls: List[URLInfo] = []
        for sitemap_el in root.findall("sm:sitemap", _SITEMAP_NS):
            loc_el = sitemap_el.find("sm:loc", _SITEMAP_NS)
            if loc_el is not None and loc_el.text:
                child_urls = self.parse(loc_el.text.strip())
                urls.extend(child_urls)
        # Fallback: try without namespace
        if not urls:
            for sitemap_el in root.findall("sitemap"):
                loc_el = sitemap_el.find("loc")
                if loc_el is not None and loc_el.text:
                    child_urls = self.parse(loc_el.text.strip())
                    urls.extend(child_urls)
        return urls

    def _parse_urlset(self, root: ET.Element) -> List[URLInfo]:
        """Parse a regular sitemap's <url> entries."""
        urls: List[URLInfo] = []
        for url_el in root.findall("sm:url", _SITEMAP_NS):
            info = self._parse_url_element(url_el, _SITEMAP_NS)
            if info:
                urls.append(info)
        # Fallback: try without namespace
        if not urls:
            for url_el in root.findall("url"):
                info = self._parse_url_element(url_el, {})
                if info:
                    urls.append(info)
        return urls

    def _parse_url_element(
        self, url_el: ET.Element, ns: Dict[str, str]
    ) -> Optional[URLInfo]:
        """Extract URLInfo from a single <url> element."""
        prefix = "sm:" if ns else ""

        loc_el = url_el.find(f"{prefix}loc", ns) if ns else url_el.find("loc")
        if loc_el is None or not loc_el.text:
            return None

        lastmod_el = (
            url_el.find(f"{prefix}lastmod", ns) if ns else url_el.find("lastmod")
        )
        priority_el = (
            url_el.find(f"{prefix}priority", ns) if ns else url_el.find("priority")
        )
        changefreq_el = (
            url_el.find(f"{prefix}changefreq", ns)
            if ns
            else url_el.find("changefreq")
        )

        priority = None
        if priority_el is not None and priority_el.text:
            try:
                priority = float(priority_el.text.strip())
            except ValueError:
                pass

        return URLInfo(
            loc=loc_el.text.strip(),
            lastmod=lastmod_el.text.strip() if lastmod_el is not None and lastmod_el.text else None,
            priority=priority,
            changefreq=changefreq_el.text.strip() if changefreq_el is not None and changefreq_el.text else None,
        )

    def _fetch(self, url: str) -> Optional[str]:
        """Download sitemap XML content."""
        headers = {"User-Agent": self.user_agent}
        try:
            resp = requests.get(url, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as e:
            logger.warning("Failed to fetch sitemap %s: %s", url, e)
            return None


class RobotsTxtChecker:
    """Reads robots.txt and checks URL access permissions."""

    def __init__(self, base_url: str, user_agent: str, timeout: int = 10) -> None:
        self.base_url = base_url
        self.user_agent = user_agent
        self._parser = RobotFileParser()
        self._sitemap_urls: List[str] = []
        self._loaded = False
        self._timeout = timeout

    def load(self) -> bool:
        """Fetch and parse robots.txt. Returns True if successful."""
        parsed = urlparse(self.base_url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        try:
            resp = requests.get(
                robots_url,
                headers={"User-Agent": self.user_agent},
                timeout=self._timeout,
            )
            if resp.status_code == 200:
                self._parser.parse(resp.text.splitlines())
                # Extract Sitemap directives manually (RobotFileParser doesn't expose them reliably)
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith("sitemap:"):
                        sitemap_url = line.split(":", 1)[1].strip()
                        if sitemap_url:
                            self._sitemap_urls.append(sitemap_url)
                self._loaded = True
                logger.info(
                    "Loaded robots.txt from %s (%d sitemap directives)",
                    robots_url,
                    len(self._sitemap_urls),
                )
                return True
            else:
                logger.info(
                    "No robots.txt at %s (status %d), allowing all",
                    robots_url,
                    resp.status_code,
                )
                self._loaded = True
                return True
        except requests.RequestException as e:
            logger.warning("Failed to fetch robots.txt from %s: %s", robots_url, e)
            self._loaded = True  # Assume allowed if can't fetch
            return False

    def can_fetch(self, url: str) -> bool:
        """Check if the URL is allowed by robots.txt."""
        if not self._loaded:
            self.load()
        return self._parser.can_fetch(self.user_agent, url)

    def get_sitemap_urls(self) -> List[str]:
        """Return sitemap URLs declared in robots.txt."""
        if not self._loaded:
            self.load()
        return self._sitemap_urls


class SiteCrawler:
    """Orchestrates full site crawling: robots.txt → sitemaps → scrape."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is None:
            from src.config import load_experiment_config

            config = load_experiment_config()

        crawler_cfg = config.get("crawler", {})
        self.request_delay = crawler_cfg.get("request_delay", 1.0)
        self.timeout = crawler_cfg.get("timeout", 10)
        self.max_retries = crawler_cfg.get("max_retries", 3)
        self.respect_robots = crawler_cfg.get("respect_robots_txt", True)

        self.target_cfg = crawler_cfg.get("target", {})
        self.competitor_cfg = crawler_cfg.get("competitor", {})
        self.fallback_cfg = crawler_cfg.get("fallback", {})

        self.user_agent = os.getenv("USER_AGENT", "GeoAuditBot/1.0 (TFG Research)")

    def crawl_site(
        self,
        url: str,
        is_target: bool = False,
        discovered_urls: Optional[List[str]] = None,
    ) -> List[Document]:
        """Crawl a site and return Documents compatible with TokenAwareChunker.

        Parameters
        ----------
        url : str
            Base URL of the site to crawl.
        is_target : bool
            If True, use target config (no max_pages limit by default).
        discovered_urls : list[str] or None
            URLs already discovered (e.g., from Gemini grounding) to prioritize.

        Returns
        -------
        List[Document] — one Document per successfully scraped page.
        """
        cfg = self.target_cfg if is_target else self.competitor_cfg
        if not cfg.get("enabled", True):
            logger.info("Crawling disabled for %s (is_target=%s)", url, is_target)
            return []

        parsed = urlparse(url)
        base_domain = parsed.netloc
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # 1. robots.txt
        robots = RobotsTxtChecker(base_url, self.user_agent, self.timeout)
        robots.load()

        # 2. Discover URLs from sitemaps
        sitemap_urls = self._get_sitemap_urls(robots, base_url)
        url_infos = self._parse_sitemaps(sitemap_urls)
        logger.info("Found %d URLs from sitemaps for %s", len(url_infos), base_url)

        # 3. Add discovered URLs (from Gemini grounding, etc.)
        seen_locs = {info.loc for info in url_infos}
        if discovered_urls:
            for disc_url in discovered_urls:
                if disc_url not in seen_locs:
                    url_infos.append(URLInfo(loc=disc_url, source="discovered"))
                    seen_locs.add(disc_url)
            logger.info(
                "Added %d discovered URLs (total: %d)",
                len(discovered_urls),
                len(url_infos),
            )

        # 4. BFS fallback if no sitemap URLs found
        if not url_infos and self.fallback_cfg.get("bfs_enabled", True):
            logger.info("No sitemap found for %s, using BFS fallback", base_url)
            url_infos = self._bfs_crawl(url, base_domain)

        # If still nothing, at least scrape the provided URL
        if not url_infos:
            url_infos = [URLInfo(loc=url, source="direct")]

        # 5. Filter
        exclude_patterns = cfg.get("exclude_patterns", [])
        url_infos = self._filter_urls(
            url_infos, base_domain, exclude_patterns, robots if self.respect_robots else None
        )

        # 6. Prioritize
        priority_mode = cfg.get("priority", "pages_first")
        url_infos = self._prioritize(url_infos, priority_mode)

        # 7. Apply max_pages limit
        max_pages = cfg.get("max_pages", None)
        if max_pages is not None and len(url_infos) > max_pages:
            logger.info(
                "Limiting from %d to %d URLs (max_pages)", len(url_infos), max_pages
            )
            url_infos = url_infos[:max_pages]

        # 8. Scrape each URL
        role = "target" if is_target else "competitor"
        logger.info(
            "Crawling %d URLs for %s [%s]", len(url_infos), base_url, role
        )
        docs = self._scrape_urls(url_infos, is_target)

        logger.info(
            "Crawl complete for %s: %d/%d pages scraped successfully",
            base_url,
            len(docs),
            len(url_infos),
        )
        return docs

    # ------------------------------------------------------------------
    # Sitemap discovery
    # ------------------------------------------------------------------

    def _get_sitemap_urls(
        self, robots: RobotsTxtChecker, base_url: str
    ) -> List[str]:
        """Get sitemap URLs from robots.txt, falling back to common locations."""
        sitemap_urls = robots.get_sitemap_urls()
        if not sitemap_urls:
            # Try common sitemap locations
            candidates = [
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
                f"{base_url}/wp-sitemap.xml",
            ]
            for candidate in candidates:
                try:
                    resp = requests.head(
                        candidate,
                        headers={"User-Agent": self.user_agent},
                        timeout=self.timeout,
                        allow_redirects=True,
                    )
                    if resp.status_code == 200:
                        sitemap_urls.append(candidate)
                        break
                except requests.RequestException:
                    continue
        return sitemap_urls

    def _parse_sitemaps(self, sitemap_urls: List[str]) -> List[URLInfo]:
        """Parse all sitemap URLs and return deduplicated URLInfo list."""
        parser = SitemapParser(self.user_agent, self.timeout)
        all_urls: List[URLInfo] = []
        seen: Set[str] = set()

        for sitemap_url in sitemap_urls:
            urls = parser.parse(sitemap_url)
            for info in urls:
                if info.loc not in seen:
                    all_urls.append(info)
                    seen.add(info.loc)

        return all_urls

    # ------------------------------------------------------------------
    # BFS fallback
    # ------------------------------------------------------------------

    def _bfs_crawl(self, start_url: str, base_domain: str) -> List[URLInfo]:
        """BFS crawl following internal <a> links up to max_depth."""
        max_depth = self.fallback_cfg.get("max_depth", 2)
        same_domain = self.fallback_cfg.get("same_domain_only", True)

        visited: Set[str] = set()
        result: List[URLInfo] = []
        queue: List[tuple] = [(start_url, 0)]  # (url, depth)

        while queue:
            current_url, depth = queue.pop(0)

            normalized = self._normalize_url(current_url)
            if normalized in visited:
                continue
            visited.add(normalized)

            result.append(URLInfo(loc=current_url, source="bfs"))

            if depth >= max_depth:
                continue

            # Fetch page and extract links
            try:
                resp = requests.get(
                    current_url,
                    headers={"User-Agent": self.user_agent},
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                soup = BeautifulSoup(resp.text, "html.parser")

                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    full_url = urljoin(current_url, href)
                    full_url = self._normalize_url(full_url)

                    if full_url in visited:
                        continue

                    parsed = urlparse(full_url)
                    if parsed.scheme not in ("http", "https"):
                        continue

                    if same_domain and parsed.netloc != base_domain:
                        continue

                    queue.append((full_url, depth + 1))

                time.sleep(self.request_delay)
            except requests.RequestException as e:
                logger.debug("BFS failed to fetch %s: %s", current_url, e)

        logger.info("BFS crawl found %d URLs from %s", len(result), start_url)
        return result

    # ------------------------------------------------------------------
    # Filtering and prioritization
    # ------------------------------------------------------------------

    def _filter_urls(
        self,
        url_infos: List[URLInfo],
        base_domain: str,
        exclude_patterns: List[str],
        robots: Optional[RobotsTxtChecker],
    ) -> List[URLInfo]:
        """Filter URLs by domain, exclude patterns, and robots.txt."""
        filtered = []
        for info in url_infos:
            parsed = urlparse(info.loc)

            # Same domain check (allow subdomains like www.)
            if not parsed.netloc.endswith(base_domain.replace("www.", "")):
                # Allow the exact domain match too
                base_clean = base_domain.replace("www.", "")
                url_clean = parsed.netloc.replace("www.", "")
                if url_clean != base_clean:
                    continue

            # Exclude patterns
            path = parsed.path
            if any(pattern in path for pattern in exclude_patterns):
                continue

            # robots.txt
            if robots and not robots.can_fetch(info.loc):
                logger.debug("Blocked by robots.txt: %s", info.loc)
                continue

            # Skip non-HTML resources
            if re.search(r"\.(pdf|jpg|jpeg|png|gif|svg|css|js|zip|xml|json)$", path, re.I):
                continue

            filtered.append(info)

        logger.info(
            "Filtered from %d to %d URLs", len(url_infos), len(filtered)
        )
        return filtered

    def _prioritize(
        self, url_infos: List[URLInfo], mode: str
    ) -> List[URLInfo]:
        """Sort URLs by priority mode."""
        if mode == "pages_first":
            # Static pages (no /20xx/ date pattern, shorter paths) before blog posts
            def sort_key(info: URLInfo) -> tuple:
                path = urlparse(info.loc).path
                is_post = bool(re.search(r"/\d{4}/", path))
                depth = path.count("/")
                priority = info.priority or 0.5
                return (is_post, depth, -priority)

            url_infos.sort(key=sort_key)

        elif mode == "discovered_urls_first":
            # Discovered URLs first, then sitemap, then BFS
            source_order = {"discovered": 0, "direct": 1, "sitemap": 2, "bfs": 3}

            def sort_key(info: URLInfo) -> tuple:
                return (source_order.get(info.source, 9), -(info.priority or 0.5))

            url_infos.sort(key=sort_key)

        return url_infos

    # ------------------------------------------------------------------
    # Scraping
    # ------------------------------------------------------------------

    def _scrape_urls(
        self, url_infos: List[URLInfo], is_target: bool
    ) -> List[Document]:
        """Scrape each URL using StructuredWebLoader with delay between requests."""
        docs: List[Document] = []
        total = len(url_infos)

        for i, info in enumerate(url_infos):
            logger.info("[%d/%d] Scraping: %s", i + 1, total, info.loc)

            loader = StructuredWebLoader(
                url=info.loc,
                timeout=self.timeout,
                max_retries=self.max_retries,
            )
            page_docs = loader.load()

            if page_docs:
                for doc in page_docs:
                    doc.metadata["is_target"] = is_target
                    doc.metadata["crawl_source"] = info.source
                    if info.lastmod:
                        doc.metadata["lastmod"] = info.lastmod
                docs.extend(page_docs)
                logger.info("  -> OK (%d chars)", len(page_docs[0].page_content))
            else:
                logger.warning("  -> FAILED: %s", info.loc)

            # Delay between requests (skip after last)
            if i < total - 1:
                time.sleep(self.request_delay)

        return docs

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL by removing fragment and trailing slash."""
        parsed = urlparse(url)
        path = parsed.path.rstrip("/") or "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}"
