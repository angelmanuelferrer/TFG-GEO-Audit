"""Token-aware text chunking using tiktoken and LangChain splitters.

Replaces prototype character-based chunking (1000 chars) with proper
token-based chunking (256 tokens default, aligned with SAGEO Arena benchmark).
See ADR-001 and ADR-011 in docs/DECISIONS.md.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

_DEFAULT_SEPARATORS = ["\n## ", "\n### ", "\n\n", "\n", ". ", " "]

_DEFAULT_PROFILES = {
    "default": {"chunk_size": 256, "overlap": 64},
    "faq": {"chunk_size": 256, "overlap": 64},
}


class TokenAwareChunker:
    """Chunks documents using tiktoken token counts instead of character counts."""

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        self._encoding = tiktoken.get_encoding("cl100k_base")

        if config is None:
            from src.config import load_experiment_config

            config = load_experiment_config()

        chunking = config.get("chunking", {})
        separators = chunking.get("separators", _DEFAULT_SEPARATORS)

        self._profiles: Dict[str, RecursiveCharacterTextSplitter] = {}
        for profile, defaults in _DEFAULT_PROFILES.items():
            size_key = f"{profile}_chunk_size_tokens"
            overlap_key = f"{profile}_overlap_tokens"
            chunk_size = chunking.get(size_key, defaults["chunk_size"])
            overlap = chunking.get(overlap_key, defaults["overlap"])

            self._profiles[profile] = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=overlap,
                length_function=self._token_length,
                separators=separators,
            )
            logger.info(
                "Profile '%s': %d tokens, %d overlap", profile, chunk_size, overlap
            )

    def _token_length(self, text: str) -> int:
        """Return the number of cl100k_base tokens in *text*."""
        return len(self._encoding.encode(text))

    def chunk_documents(
        self, docs: List[Document], content_type: str = "default"
    ) -> List[Document]:
        """Split *docs* into token-sized chunks, preserving metadata."""
        if content_type not in self._profiles:
            raise ValueError(
                f"Unknown content_type '{content_type}'. "
                f"Available: {list(self._profiles.keys())}"
            )

        splitter = self._profiles[content_type]
        chunks = splitter.split_documents(docs)

        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["content_type"] = content_type
            chunk.metadata["chunk_tokens"] = self._token_length(chunk.page_content)

        logger.info(
            "Chunked %d document(s) into %d chunks (profile=%s)",
            len(docs),
            len(chunks),
            content_type,
        )
        return chunks
