"""Embedding factory: Google gemini-embedding-001 via google-genai SDK.

Uses the new google-genai>=1 SDK directly (not langchain-google-genai, which
uses the v1beta API where gemini-embedding-001 is unavailable).

See ADR-017 in docs/DECISIONS.md (supersedes ADR-016).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx
from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

_BATCH_SIZE = 50
_BATCH_DELAY = 1.5  # seconds between batches — stays under 3000 req/min quota
_MAX_RETRIES = 5
_RETRY_BASE_DELAY = 5.0  # seconds, doubles each attempt


class GoogleGenAIEmbeddings(Embeddings):
    """LangChain-compatible embeddings via google-genai SDK (gemini-embedding-001)."""

    def __init__(self, model: str = "models/gemini-embedding-001") -> None:
        self.model = model
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    def _embed_batch_with_retry(self, batch: List[str]) -> List[List[float]]:
        """Embed a single batch with exponential backoff on network errors."""
        for attempt in range(_MAX_RETRIES):
            try:
                response = self._client.models.embed_content(
                    model=self.model,
                    contents=batch,
                    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
                )
                return [e.values for e in response.embeddings]
            except (httpx.RemoteProtocolError, httpx.ReadError, httpx.ConnectError) as e:
                if attempt == _MAX_RETRIES - 1:
                    raise
                delay = _RETRY_BASE_DELAY * (2**attempt)
                logger.warning(
                    "Network error on batch (attempt %d/%d): %s — retrying in %.0fs",
                    attempt + 1,
                    _MAX_RETRIES,
                    e,
                    delay,
                )
                time.sleep(delay)
        return []  # unreachable

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            all_embeddings.extend(self._embed_batch_with_retry(batch))
            done = min(i + _BATCH_SIZE, len(texts))
            logger.debug("Embedded %d/%d texts", done, len(texts))
            if done < len(texts):
                time.sleep(_BATCH_DELAY)
        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        response = self._client.models.embed_content(
            model=self.model,
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
        )
        return response.embeddings[0].values


def create_embeddings(
    config: Optional[Dict[str, Any]] = None,
) -> GoogleGenAIEmbeddings:
    """Create embeddings via Google gemini-embedding-001 API."""
    return GoogleGenAIEmbeddings()
