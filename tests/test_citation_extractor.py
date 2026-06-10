"""Tests unitarios del CitationExtractor: el núcleo de cálculo de métricas GEO.

Materializa los casos verificables descritos en el capítulo de pruebas de la
memoria: visibilidad, Share of Model, ranking, PAWC, Citation Rate, coincidencia
de URLs y menciones de marca.
"""
from __future__ import annotations

import pytest

from src.rag.citation_extractor import CitationExtractor


@pytest.fixture()
def extractor() -> CitationExtractor:
    return CitationExtractor("https://programamos.es", "Programamos")


def _citation(url: str, index: int, quote: str = "") -> dict:
    return {"url": url, "index": index, "quote": quote}


# ── Visibilidad ────────────────────────────────────────────────────────────────

def test_visible_with_one_target_citation(extractor):
    out = {"citations": [_citation("https://programamos.es/talleres", 1)]}
    assert extractor.extract_metrics(out)["is_visible"] is True


def test_not_visible_without_target_citations(extractor):
    out = {"citations": [_citation("https://code.org", 1)]}
    metrics = extractor.extract_metrics(out)
    assert metrics["is_visible"] is False
    assert metrics["target_citations"] == 0


def test_no_citations_at_all(extractor):
    metrics = extractor.extract_metrics({"citations": [], "answer": ""})
    assert metrics["is_visible"] is False
    assert metrics["total_citations"] == 0


# ── Share of Model ─────────────────────────────────────────────────────────────

def test_som_two_of_five(extractor):
    cits = [
        _citation("https://programamos.es/a", 1),
        _citation("https://code.org", 2),
        _citation("https://programamos.es/b", 3),
        _citation("https://scratch.mit.edu", 4),
        _citation("https://codelearn.com", 5),
    ]
    assert extractor.extract_metrics({"citations": cits})["som"] == 40.0


def test_som_zero_citations_no_division_error(extractor):
    assert extractor.extract_metrics({"citations": []})["som"] == 0.0


# ── Ranking ────────────────────────────────────────────────────────────────────

def test_first_citation_rank_uses_index_order(extractor):
    cits = [
        _citation("https://programamos.es", 3),
        _citation("https://code.org", 1),
        _citation("https://scratch.mit.edu", 2),
    ]
    assert extractor.extract_metrics({"citations": cits})["first_citation_rank"] == 3


def test_rank_none_when_target_absent(extractor):
    cits = [_citation("https://code.org", 1)]
    assert extractor.extract_metrics({"citations": cits})["first_citation_rank"] is None


# ── PAWC ───────────────────────────────────────────────────────────────────────

def test_pawc_manual_formula(extractor):
    """Dos citas del objetivo: 8 palabras en posición 2 y 6 en posición 4.

    PAWC = 8/log2(3) + 6/log2(5) = 5.05 + 2.58 = 7.63
    """
    cits = [
        _citation("https://code.org", 1),
        _citation("https://programamos.es/a", 2, "uno dos tres cuatro cinco seis siete ocho"),
        _citation("https://scratch.mit.edu", 3),
        _citation("https://programamos.es/b", 4, "uno dos tres cuatro cinco seis"),
    ]
    assert extractor.extract_metrics({"citations": cits})["pawc"] == 7.63


def test_pawc_zero_without_target(extractor):
    cits = [_citation("https://code.org", 1, "texto del competidor")]
    assert extractor.extract_metrics({"citations": cits})["pawc"] == 0.0


# ── Coincidencia de URLs (sufijo seguro) ───────────────────────────────────────

@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://programamos.es/talleres", True),
        ("https://www.programamos.es/", True),
        ("http://programamos.es", True),
        ("https://programamos.es?ref=gemini", True),
        ("https://programamos.es.evil.com", False),
        ("https://noprogramamos.es", False),
    ],
)
def test_url_matches_target(extractor, url, expected):
    assert extractor._url_matches_target(url) is expected


# ── Citation Rate ──────────────────────────────────────────────────────────────

def test_citation_rate_none_when_not_retrieved(extractor):
    out = {
        "citations": [],
        "sources_used": ["https://code.org"],
        "sources_available_but_unused": ["https://scratch.mit.edu"],
    }
    assert extractor.extract_metrics(out)["citation_rate"] is None


def test_citation_rate_retrieved_but_not_cited(extractor):
    out = {
        "citations": [_citation("https://code.org", 1)],
        "sources_used": [],
        "sources_available_but_unused": ["https://programamos.es/a"],
    }
    assert extractor.extract_metrics(out)["citation_rate"] == 0.0


def test_citation_rate_one_cited_of_two_retrieved(extractor):
    out = {
        "citations": [_citation("https://programamos.es/a", 1)],
        "sources_used": ["https://programamos.es/a"],
        "sources_available_but_unused": ["https://programamos.es/b"],
    }
    assert extractor.extract_metrics(out)["citation_rate"] == 50.0


# ── Menciones de marca ─────────────────────────────────────────────────────────

def test_brand_mentions_in_answer_case_insensitive(extractor):
    out = {
        "citations": [],
        "answer": "Según PROGRAMAMOS, aprender Scratch es accesible. programamos ofrece recursos.",
    }
    mentions = extractor.extract_metrics(out)["brand_mentions"]
    assert len(mentions) == 2
    assert all(m["source"] == "answer" for m in mentions)


def test_brand_mentions_in_citation_quotes(extractor):
    out = {
        "citations": [_citation("https://code.org", 2, "comparativa con Programamos y otros")],
        "answer": "",
    }
    mentions = extractor.extract_metrics(out)["brand_mentions"]
    assert len(mentions) == 1
    assert mentions[0]["source"] == "citation_2"


def test_brand_mention_context_window(extractor):
    answer = "x" * 100 + " Programamos " + "y" * 100
    out = {"citations": [], "answer": answer}
    mentions = extractor.extract_metrics(out)["brand_mentions"]
    assert len(mentions) == 1
    # ±50 caracteres alrededor de la mención
    assert len(mentions[0]["context"]) <= len("Programamos") + 100 + 2
    assert "Programamos" in mentions[0]["context"]
