#!/usr/bin/env python3
"""Experimental run: measure GEO visibility of target site.

Equivalent to notebooks/experimental_run.ipynb but runs from terminal.
Loads frozen vectorstore, re-embeds only the target, then runs RAG Judge
for each query and computes GEO metrics.

Requires GOOGLE_API_KEY in .env (RAG Judge + embeddings via Google API).

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
    get_queries_for_run_with_meta,
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
    parser.add_argument(
        "--cache-ttl",
        type=float,
        default=24.0,
        metavar="HOURS",
        help="Reuse cached target vectorstore if younger than N hours (default: 24, 0 = always recrawl)",
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

    query_metas = get_queries_for_run_with_meta(args.block)
    print(f"Queries: {len(query_metas)} (block={args.block or 'core only'})")

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

    # --- 4. Crawl + chunk + embed target (with cache) ---
    target_cache_dir = PROJECT_ROOT / "data" / "target_vectorstore_cache"
    target_cache_meta = target_cache_dir / "meta.json"

    def _load_cached_target_vs() -> "FAISS | None":
        if args.cache_ttl <= 0 or not target_cache_meta.exists():
            return None
        with open(target_cache_meta) as f:
            meta = json.load(f)
        age_h = (time.time() - meta["timestamp"]) / 3600
        if age_h > args.cache_ttl:
            return None
        print(f"\n=== 3/6 Target vectorstore from cache ({age_h:.1f}h old, TTL={args.cache_ttl:.0f}h) ===")
        vs = FAISS.load_local(str(target_cache_dir), embeddings, allow_dangerous_deserialization=True)
        print(f"  pages={meta['n_pages']}  chunks={meta['n_chunks']}")
        return vs

    target_vs = _load_cached_target_vs()

    if target_vs is None:
        print(f"\n=== 3/6 Crawling target: {target_url} ===")
        crawler = SiteCrawler(config)
        target_docs = crawler.crawl_site(target_url, is_target=True)
        print(f"Target pages: {len(target_docs)}")

        print("\n=== 4/6 Chunking + embedding target ===")
        chunker = TokenAwareChunker(config)
        target_chunks = chunker.chunk_documents(target_docs)
        print(f"Target chunks: {len(target_chunks)}")

        target_vs = FAISS.from_documents(target_chunks, embeddings)

        target_cache_dir.mkdir(parents=True, exist_ok=True)
        target_vs.save_local(str(target_cache_dir))
        with open(target_cache_meta, "w") as f:
            json.dump({"timestamp": time.time(), "n_pages": len(target_docs), "n_chunks": len(target_chunks)}, f)
        print(f"  Target vectorstore cached at {target_cache_dir}")

    # Merge: target + frozen competitors
    frozen_vs.merge_from(target_vs)
    merged_vs = frozen_vs
    print("Merged vectorstore ready")

    # --- 5. RAG Judge + Metrics ---
    print(f"\n=== 5/6 Running RAG Judge on {len(query_metas)} queries ===")
    judge = RAGJudge(config)
    extractor = CitationExtractor(target_url, target_brand)

    raw_results = []
    metrics_list = []

    for i, qmeta in enumerate(query_metas, 1):
        query = qmeta["text"]
        print(f"\n[{i}/{len(query_metas)}] [{qmeta['category']}] {query[:65]}...")

        try:
            answer = judge.generate_answer_with_agent(query, merged_vs)
            metrics = extractor.extract_metrics(answer)

            raw_results.append({"query_id": qmeta["id"], "query": query, "answer": answer})
            metrics_list.append({"query_id": qmeta["id"], "query": query, "category": qmeta["category"], **metrics})

            visible = "VISIBLE" if metrics["is_visible"] else "not visible"
            print(f"  -> {visible} | SoM={metrics['som']}% | Citations={metrics['target_citations']}/{metrics['total_citations']}")

        except Exception as exc:
            logger.error("Query failed: %s — %s", query[:50], exc)
            raw_results.append({"query_id": qmeta["id"], "query": query, "error": str(exc)})
            metrics_list.append({"query_id": qmeta["id"], "query": query, "category": qmeta["category"], "error": str(exc)})

    # --- 6. Save results ---
    print(f"\n=== 6/6 Saving results to {output_dir} ===")

    # Raw results
    with open(output_dir / "raw_results.json", "w", encoding="utf-8") as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=2)

    # Scorecard
    successful = [m for m in metrics_list if "error" not in m]
    n_visible = sum(1 for m in successful if m["is_visible"])

    # Per-category breakdown
    categories = sorted(set(m.get("category", "unknown") for m in metrics_list))
    by_category = {}
    for cat in categories:
        cat_all = [m for m in metrics_list if m.get("category") == cat]
        cat_ok = [m for m in cat_all if "error" not in m]
        cat_vis = [m for m in cat_ok if m["is_visible"]]
        by_category[cat] = {
            "n": len(cat_all),
            "n_errors": len(cat_all) - len(cat_ok),
            "n_successful": len(cat_ok),
            "visibility_rate": round(len(cat_vis) / len(cat_ok) * 100, 2) if cat_ok else 0,
            "avg_som": round(sum(m["som"] for m in cat_ok) / len(cat_ok), 2) if cat_ok else 0,
            "avg_citations": round(sum(m["total_citations"] for m in cat_ok) / len(cat_ok), 2) if cat_ok else 0,
        }

    scorecard = {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(),
        "target_url": target_url,
        "target_brand": target_brand,
        "rotation_block": args.block,
        "n_queries": len(metrics_list),
        "n_successful": len(successful),
        "n_errors": len(metrics_list) - len(successful),
        "visibility_rate": round(n_visible / len(successful) * 100, 2) if successful else 0,
        "avg_som": round(sum(m["som"] for m in successful) / len(successful), 2) if successful else 0,
        "avg_citations": round(sum(m["total_citations"] for m in successful) / len(successful), 2) if successful else 0,
        "by_category": by_category,
        "per_query_metrics": metrics_list,
    }

    with open(output_dir / "scorecard.json", "w", encoding="utf-8") as f:
        json.dump(scorecard, f, ensure_ascii=False, indent=2)

    # Summary
    print(f"\n=== Results ===")
    print(f"  Queries:     {len(successful)}/{len(metrics_list)} ok  ({scorecard['n_errors']} errores)")
    print(f"  Visibility:  {scorecard['visibility_rate']}%")
    print(f"  Avg SoM:     {scorecard['avg_som']}%")
    print(f"\n  By category:")
    for cat, stats in by_category.items():
        print(f"    {cat:<15} n={stats['n']} (err={stats['n_errors']})  vis={stats['visibility_rate']:.0f}%  SoM={stats['avg_som']:.1f}%")
    print(f"\n  Scorecard: {output_dir / 'scorecard.json'}")
    print(f"  Raw results: {output_dir / 'raw_results.json'}")


if __name__ == "__main__":
    main()
