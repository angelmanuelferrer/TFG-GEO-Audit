#!/usr/bin/env python3
"""Experimental run: measure GEO visibility of target site.

Equivalent to notebooks/experimental_run.ipynb but runs from terminal.
Loads frozen vectorstore, re-embeds only the target, then runs RAG Judge
for each query and computes GEO metrics.

Requires EMBEDDING_SERVER_URL and EMBEDDING_SERVER_TOKEN in .env (Kaggle GPU server).

Usage:
    python scripts/run_experimental.py [--block R1|R2|R3|R4]
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from langchain_community.vectorstores import FAISS

from src.config import (
    get_queries_for_run,
    load_experiment_config,
)
from src.processing.chunker import TokenAwareChunker
from src.processing.embeddings import create_embeddings
from src.processing.site_crawler import SiteCrawler
from src.rag.citation_extractor import CitationExtractor
from src.rag.judge import RAGJudge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run experimental GEO measurement")
    parser.add_argument(
        "--block",
        type=str,
        default=None,
        choices=["R1", "R2", "R3", "R4"],
        help="Rotation block to include (default: core only)",
    )
    args = parser.parse_args()

    config = load_experiment_config()
    target_url = config["target_url"]
    target_brand = config["target_brand"]

    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    output_dir = PROJECT_ROOT / "data" / "geo" / "experimental" / run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. Setup ---
    print(f"\n=== Experimental Run: {run_id} ===")
    print(f"Target: {target_url}")
    print(f"Block: {args.block or 'core only'}")

    queries = get_queries_for_run(args.block)
    print(f"Queries: {len(queries)}")

    # --- 2. Embeddings ---
    print("\n=== 1/6 Connecting to embedding server ===")
    embeddings = create_embeddings(config)

    # --- 3. Load frozen vectorstore ---
    print("\n=== 2/6 Loading frozen vectorstore ===")
    vs_dir = PROJECT_ROOT / "data" / "frozen_vectorstore"
    if not vs_dir.exists():
        print(f"ERROR: Frozen vectorstore not found at {vs_dir}")
        print("Run scripts/run_discovery.py first.")
        sys.exit(1)

    frozen_vs = FAISS.load_local(
        str(vs_dir), embeddings, allow_dangerous_deserialization=True
    )
    print(f"Frozen vectorstore loaded ({vs_dir})")

    # --- 4. Crawl + chunk + embed target ---
    print(f"\n=== 3/6 Crawling target: {target_url} ===")
    crawler = SiteCrawler(config)
    target_docs = crawler.crawl_site(target_url, is_target=True)
    print(f"Target pages: {len(target_docs)}")

    print("\n=== 4/6 Chunking + embedding target ===")
    chunker = TokenAwareChunker(config)
    target_chunks = chunker.chunk_documents(target_docs)
    print(f"Target chunks: {len(target_chunks)}")

    target_vs = FAISS.from_documents(target_chunks, embeddings)

    # Merge: target + frozen competitors
    frozen_vs.merge_from(target_vs)
    merged_vs = frozen_vs
    print("Merged vectorstore ready")

    # --- 5. RAG Judge + Metrics ---
    print(f"\n=== 5/6 Running RAG Judge on {len(queries)} queries ===")
    judge = RAGJudge(config)
    extractor = CitationExtractor(target_url, target_brand)

    raw_results = []
    metrics_list = []

    for i, query in enumerate(queries, 1):
        print(f"\n[{i}/{len(queries)}] {query[:70]}...")

        try:
            answer = judge.generate_answer_with_agent(query, merged_vs)
            metrics = extractor.extract_metrics(answer)

            raw_results.append({"query": query, "answer": answer})
            metrics_list.append({"query": query, **metrics})

            visible = "VISIBLE" if metrics["is_visible"] else "not visible"
            print(f"  -> {visible} | SoM={metrics['som']}% | Citations={metrics['target_citations']}/{metrics['total_citations']}")

        except Exception as exc:
            logger.error("Query failed: %s — %s", query[:50], exc)
            raw_results.append({"query": query, "error": str(exc)})
            metrics_list.append({"query": query, "error": str(exc)})

    # --- 6. Save results ---
    print(f"\n=== 6/6 Saving results to {output_dir} ===")

    # Raw results
    with open(output_dir / "raw_results.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=2)

    # Scorecard
    successful = [m for m in metrics_list if "error" not in m]
    n_visible = sum(1 for m in successful if m["is_visible"])

    scorecard = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "target_url": target_url,
        "target_brand": target_brand,
        "rotation_block": args.block,
        "n_queries": len(queries),
        "n_successful": len(successful),
        "n_errors": len(queries) - len(successful),
        "visibility_rate": round(n_visible / len(successful) * 100, 2) if successful else 0,
        "avg_som": round(sum(m["som"] for m in successful) / len(successful), 2) if successful else 0,
        "avg_citations": round(sum(m["target_citations"] for m in successful) / len(successful), 2) if successful else 0,
        "per_query_metrics": metrics_list,
    }

    with open(output_dir / "scorecard.json", "w", encoding="utf-8") as f:
        json.dump(scorecard, f, ensure_ascii=False, indent=2)

    # Summary
    print(f"\n=== Results ===")
    print(f"  Visibility rate: {scorecard['visibility_rate']}%")
    print(f"  Average SoM: {scorecard['avg_som']}%")
    print(f"  Avg target citations: {scorecard['avg_citations']}")
    print(f"  Errors: {scorecard['n_errors']}/{scorecard['n_queries']}")
    print(f"\n  Scorecard: {output_dir / 'scorecard.json'}")
    print(f"  Raw results: {output_dir / 'raw_results.json'}")


if __name__ == "__main__":
    main()
