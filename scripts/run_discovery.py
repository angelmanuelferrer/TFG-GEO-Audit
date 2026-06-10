#!/usr/bin/env python3
"""Discovery pipeline: find competitors and freeze vectorstore.

Equivalent to notebooks/00_discover_competitors.ipynb but runs from terminal.
Requires GOOGLE_API_KEY in .env (Gemini discovery + embeddings via Google API).

Usage:
    python scripts/run_discovery.py [--top N]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from langchain_community.vectorstores import FAISS

from src.config import (
    get_discovery_queries,
    load_experiment_config,
)
from src.discovery.competitor_finder import CompetitorFinder
from src.processing.chunker import TokenAwareChunker
from src.processing.embeddings import create_embeddings
from src.processing.site_crawler import SiteCrawler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run competitor discovery pipeline")
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of top competitors to select (default: 10)",
    )
    parser.add_argument(
        "--skip-discovery",
        action="store_true",
        help="Skip Gemini discovery and reuse existing data/frozen_competitors.json",
    )
    args = parser.parse_args()

    config = load_experiment_config()
    target_url = config["target_url"]

    data_dir = PROJECT_ROOT / "data"
    data_dir.mkdir(exist_ok=True)
    discovery_path = data_dir / "frozen_competitors.json"

    # --- 1. Discovery ---
    if args.skip_discovery:
        if not discovery_path.exists():
            print(f"ERROR: --skip-discovery requires {discovery_path} to exist.")
            sys.exit(1)
        import json
        with open(discovery_path, encoding="utf-8") as f:
            results = json.load(f)
        print(f"\n=== 1/6 Skipping discovery — loaded {discovery_path} ===")
    else:
        print("\n=== 1/6 Discovering competitors ===")
        queries = get_discovery_queries()
        print(f"Using {len(queries)} discovery queries (informational + comparative)")

        finder = CompetitorFinder(config)
        results = finder.discover_competitors(queries)

        finder.save_results(results, str(discovery_path))
        print(f"Discovery results saved to {discovery_path}")

    # --- 2. Select top competitors ---
    print(f"\n=== 2/6 Selecting top {args.top} competitors ===")
    aggregated = results["aggregated_domains"]
    top_competitors = aggregated[: args.top]

    for i, comp in enumerate(top_competitors, 1):
        print(f"  {i:2d}. {comp['domain']} (score={comp['score']}, queries={comp['n_queries']})")

    # --- 3. Crawl target + competitors ---
    print("\n=== 3/6 Crawling sites ===")
    crawler = SiteCrawler(config)

    print(f"\nCrawling target: {target_url}")
    target_docs = crawler.crawl_site(target_url, is_target=True)
    print(f"  Target: {len(target_docs)} pages")

    competitor_docs = []
    for comp in top_competitors:
        domain = comp["domain"]
        discovered_urls = comp.get("urls", [])
        base_url = f"https://{domain}"
        print(f"\nCrawling competitor: {domain}")
        docs = crawler.crawl_site(
            base_url, is_target=False, discovered_urls=discovered_urls
        )
        competitor_docs.extend(docs)
        print(f"  {domain}: {len(docs)} pages")

    print(f"\nTotal: {len(target_docs)} target + {len(competitor_docs)} competitor pages")

    # --- 4. Chunk ---
    print("\n=== 4/6 Chunking documents ===")
    chunker = TokenAwareChunker(config)
    competitor_chunks = chunker.chunk_documents(competitor_docs)
    print(f"Competitor chunks: {len(competitor_chunks)}")

    # --- 5. Embed + build frozen vectorstore (competitors only) ---
    print("\n=== 5/6 Building frozen vectorstore (competitors only) ===")
    embeddings = create_embeddings(config)
    frozen_vs = FAISS.from_documents(competitor_chunks, embeddings)

    vs_dir = PROJECT_ROOT / "data" / "frozen_vectorstore"
    vs_dir.mkdir(parents=True, exist_ok=True)
    frozen_vs.save_local(str(vs_dir))
    print(f"Frozen vectorstore saved to {vs_dir}")

    # --- 6. Summary ---
    print("\n=== 6/6 Summary ===")
    print(f"  Competitors: {len(top_competitors)}")
    print(f"  Competitor pages: {len(competitor_docs)}")
    print(f"  Competitor chunks: {len(competitor_chunks)}")
    print(f"  Vectorstore: {vs_dir}")
    print(f"  Discovery data: {discovery_path}")
    print("\nDiscovery complete. Run scripts/run_experimental.py for experimental runs.")


if __name__ == "__main__":
    main()
