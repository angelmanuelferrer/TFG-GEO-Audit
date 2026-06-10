"""Tests del TokenAwareChunker: chunking 256/64 medido en tokens cl100k_base."""
from __future__ import annotations

import pytest

pytest.importorskip("tiktoken")
pytest.importorskip("langchain_text_splitters")

from langchain_core.documents import Document  # noqa: E402

from src.processing.chunker import TokenAwareChunker  # noqa: E402

_CONFIG = {
    "chunking": {
        "default_chunk_size_tokens": 256,
        "default_overlap_tokens": 64,
    }
}


@pytest.fixture(scope="module")
def chunker() -> TokenAwareChunker:
    return TokenAwareChunker(config=_CONFIG)


def _long_doc() -> Document:
    paragraph = (
        "El pensamiento computacional permite resolver problemas de forma "
        "estructurada y es una competencia clave en la educación actual. "
    )
    return Document(page_content="\n\n".join([paragraph * 6] * 12), metadata={"source": "https://ejemplo.es/p"})


def test_chunks_respect_token_budget(chunker):
    chunks = chunker.chunk_documents([_long_doc()])
    assert len(chunks) > 1
    assert all(c.metadata["chunk_tokens"] <= 256 for c in chunks)


def test_chunks_preserve_and_extend_metadata(chunker):
    chunks = chunker.chunk_documents([_long_doc()])
    for idx, chunk in enumerate(chunks):
        assert chunk.metadata["source"] == "https://ejemplo.es/p"
        assert chunk.metadata["chunk_index"] == idx
        assert chunk.metadata["content_type"] == "default"


def test_short_document_single_chunk(chunker):
    doc = Document(page_content="Texto breve.", metadata={})
    chunks = chunker.chunk_documents([doc])
    assert len(chunks) == 1
    assert chunks[0].page_content == "Texto breve."


def test_unknown_profile_raises(chunker):
    with pytest.raises(ValueError):
        chunker.chunk_documents([Document(page_content="x", metadata={})], content_type="inexistente")
