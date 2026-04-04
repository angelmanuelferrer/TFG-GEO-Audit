"""Embedding factory: Google text-embedding-004 via google-genai SDK.

Uses the new google-genai>=1 SDK directly (not langchain-google-genai, which
uses v1beta API where text-embedding-004 is unavailable).

See ADR-016 in docs/DECISIONS.md.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

_BATCH_SIZE = 100


class GoogleGenAIEmbeddings(Embeddings):
    """LangChain-compatible embeddings via google-genai SDK (text-embedding-004)."""

    def __init__(self, model: str = "models/gemini-embedding-001") -> None:
        self.model = model
        self._client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), _BATCH_SIZE):
            batch = texts[i : i + _BATCH_SIZE]
            response = self._client.models.embed_content(
                model=self.model,
                contents=batch,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            all_embeddings.extend([e.values for e in response.embeddings])
            logger.debug("Embedded %d/%d texts", min(i + _BATCH_SIZE, len(texts)), len(texts))
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
    """Create embeddings via Google text-embedding-004 API."""
    return GoogleGenAIEmbeddings()
