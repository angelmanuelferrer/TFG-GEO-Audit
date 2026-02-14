"""Embedding factory: local HuggingFace with OpenAI fallback.

Tries intfloat/multilingual-e5-large on GPU first (Kaggle),
falls back to OpenAI text-embedding-3-small if unavailable.
See ADR-003 in docs/DECISIONS.md.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def create_embeddings(config: Optional[Dict[str, Any]] = None):
    """Create a LangChain-compatible embeddings object.

    Tries local sentence-transformers with GPU, falls back to OpenAI.
    Returns an Embeddings instance ready for FAISS or other vectorstores.
    """
    if config is None:
        from src.config import load_experiment_config

        config = load_experiment_config()

    emb_config = config.get("embeddings", {})

    # Try local embeddings first
    if emb_config.get("provider") == "local":
        try:
            import torch
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                from langchain_community.embeddings import HuggingFaceEmbeddings

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_name = emb_config["model"]

            logger.info("Loading local embeddings: %s (device=%s)", model_name, device)
            embeddings = HuggingFaceEmbeddings(
                model_name=model_name,
                model_kwargs={"device": device},
                encode_kwargs={"normalize_embeddings": True},
            )
            logger.info("Local embeddings loaded successfully on %s", device)
            return embeddings

        except (ImportError, RuntimeError, OSError) as exc:
            logger.warning("Local embeddings failed: %s. Falling back to OpenAI.", exc)

    # Fallback to OpenAI
    fallback = emb_config.get("fallback", {})
    model = fallback.get("model", "text-embedding-3-small")
    local_dim = emb_config.get("dimensions", 1024)
    fallback_dim = fallback.get("dimensions", 1536)
    logger.warning(
        "Using OpenAI embeddings: %s (%dd). "
        "ATENCIÓN: Las dimensiones (%d) difieren de las locales (%d). "
        "NO mezclar vectorstores generados con distintos modelos de embeddings.",
        model,
        fallback_dim,
        fallback_dim,
        local_dim,
    )

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(model=model)