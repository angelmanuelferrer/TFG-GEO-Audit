"""Remote embeddings client for Kaggle GPU server.

Sends texts to a Flask server running on Kaggle (via localtunnel) that hosts
multilingual-e5-large on GPU. Implements the LangChain Embeddings interface
so it can be used as a drop-in replacement for HuggingFaceEmbeddings.

See ADR-014 in docs/DECISIONS.md.
"""

from __future__ import annotations

import logging
import time
from typing import List

import requests
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)

_DEFAULT_BATCH_SIZE = 64
_MAX_RETRIES = 3
_INITIAL_BACKOFF = 2.0


class RemoteEmbeddings(Embeddings):
    """LangChain-compatible embeddings via a remote HTTP server (Kaggle GPU)."""

    def __init__(
        self,
        server_url: str,
        api_token: str,
        batch_size: int = _DEFAULT_BATCH_SIZE,
    ) -> None:
        self.server_url = server_url.rstrip("/")
        self.api_token = api_token
        self.batch_size = batch_size

        self._health_check()

    def _health_check(self) -> None:
        """Verify the server is reachable. Fail fast if not."""
        url = f"{self.server_url}/health"
        try:
            resp = requests.get(
                url,
                headers=self._headers(),
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "Remote embeddings server OK: model=%s, device=%s",
                data.get("model", "unknown"),
                data.get("device", "unknown"),
            )
        except Exception as exc:
            raise ConnectionError(
                f"No se pudo conectar al servidor de embeddings en {url}: {exc}\n"
                "Asegurate de que kaggle_gpu_server.ipynb esta ejecutandose "
                "y que EMBEDDING_SERVER_URL es correcto."
            ) from exc

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    def _post_with_retry(self, texts: List[str]) -> List[List[float]]:
        """POST texts to /embed with exponential backoff retry."""
        url = f"{self.server_url}/embed"
        payload = {"texts": texts}
        backoff = _INITIAL_BACKOFF

        for attempt in range(_MAX_RETRIES):
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers=self._headers(),
                    timeout=120,
                )
                resp.raise_for_status()
                return resp.json()["embeddings"]
            except Exception as exc:
                if attempt < _MAX_RETRIES - 1:
                    logger.warning(
                        "Embed request failed (attempt %d/%d): %s. Retrying in %.0fs...",
                        attempt + 1,
                        _MAX_RETRIES,
                        exc,
                        backoff,
                    )
                    time.sleep(backoff)
                    backoff *= 2
                else:
                    raise RuntimeError(
                        f"Embed request failed after {_MAX_RETRIES} attempts: {exc}"
                    ) from exc

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of documents, batching client-side."""
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            logger.debug(
                "Embedding batch %d-%d / %d",
                i + 1,
                min(i + self.batch_size, len(texts)),
                len(texts),
            )
            embeddings = self._post_with_retry(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Embed a single query text."""
        result = self._post_with_retry([text])
        return result[0]
