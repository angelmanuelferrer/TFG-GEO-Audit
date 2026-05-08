"""Unit tests para servicios internos del backend.

Cubre funciones puras (sin IO) y funciones que leen archivos usando tmp_path
de pytest para crear fixtures mínimas en disco. No hay llamadas a LLMs ni APIs.
"""
from __future__ import annotations

import json
import pathlib

import pytest


# ── run_loader: funciones puras ───────────────────────────────────────────────


class TestComputeByCategory:
    """Tests de run_loader._compute_by_category."""

    def _call(self, per_query):
        from app.services.run_loader import _compute_by_category
        return _compute_by_category(per_query)

    def test_empty_list_returns_empty_dict(self):
        assert self._call([]) == {}

    def test_single_visible_query(self):
        queries = [
            {"category": "informacional", "is_visible": True, "som": 75.0, "avg_citations": 2.0}
        ]
        result = self._call(queries)
        assert "informacional" in result
        cat = result["informacional"]
        assert cat["n"] == 1
        assert cat["n_successful"] == 1
        assert cat["visibility_rate"] == 100.0
        assert cat["avg_som"] == 75.0
        assert cat["avg_citations"] == 2.0

    def test_mix_visible_not_visible(self):
        queries = [
            {"category": "comparativa", "is_visible": True, "som": 60.0, "avg_citations": 1.0},
            {"category": "comparativa", "is_visible": False, "som": 0.0, "avg_citations": 0.0},
        ]
        result = self._call(queries)
        cat = result["comparativa"]
        assert cat["n"] == 2
        assert cat["visibility_rate"] == 50.0

    def test_errored_queries_excluded_from_metrics(self):
        queries = [
            {"category": "informacional", "is_visible": True, "som": 80.0, "avg_citations": 3.0},
            {"category": "informacional", "_error": True, "is_visible": False, "som": 0.0},
        ]
        result = self._call(queries)
        cat = result["informacional"]
        assert cat["n"] == 2
        assert cat["n_errors"] == 1
        assert cat["n_successful"] == 1
        assert cat["visibility_rate"] == 100.0

    def test_queries_without_category_go_to_unknown(self):
        queries = [{"is_visible": False, "som": 0.0, "avg_citations": 0.0}]
        result = self._call(queries)
        assert "unknown" in result

    def test_multiple_categories_separated(self):
        queries = [
            {"category": "informacional", "is_visible": True, "som": 50.0, "avg_citations": 1.0},
            {"category": "navegacional", "is_visible": False, "som": 0.0, "avg_citations": 0.0},
        ]
        result = self._call(queries)
        assert "informacional" in result
        assert "navegacional" in result
        assert result["informacional"]["n"] == 1
        assert result["navegacional"]["n"] == 1

    def test_total_citations_field_fallback(self):
        """Acepta total_citations cuando avg_citations no está presente (formato v1)."""
        queries = [
            {"category": "comparativa", "is_visible": True, "som": 40.0, "total_citations": 5}
        ]
        result = self._call(queries)
        assert result["comparativa"]["avg_citations"] == 5.0


class TestComputeDerived:
    """Tests de run_loader.compute_derived."""

    def _call(self, scorecard):
        from app.services.run_loader import compute_derived
        return compute_derived(scorecard)

    def test_empty_scorecard_returns_empty_dicts(self):
        result = self._call({"per_query_metrics": []})
        assert result["avg_first_rank_by_category"] == {}
        assert result["avg_pawc_by_category"] == {}

    def test_averages_computed_per_category(self):
        scorecard = {
            "per_query_metrics": [
                {"category": "informacional", "first_citation_rank": 2, "pawc": 0.8},
                {"category": "informacional", "first_citation_rank": 4, "pawc": 0.6},
                {"category": "comparativa", "first_citation_rank": 1, "pawc": 1.0},
            ]
        }
        result = self._call(scorecard)
        assert result["avg_first_rank_by_category"]["informacional"] == 3.0
        assert result["avg_pawc_by_category"]["informacional"] == 0.7
        assert result["avg_first_rank_by_category"]["comparativa"] == 1.0

    def test_queries_without_rank_or_pawc_ignored(self):
        scorecard = {
            "per_query_metrics": [
                {"category": "informacional"},
                {"category": "informacional", "first_citation_rank": 3},
            ]
        }
        result = self._call(scorecard)
        assert result["avg_first_rank_by_category"]["informacional"] == 3.0
        assert "informacional" not in result["avg_pawc_by_category"]

    def test_missing_per_query_metrics_key(self):
        result = self._call({})
        assert result["avg_first_rank_by_category"] == {}


# ── query_prioritizer: funciones puras ───────────────────────────────────────


class TestIsTarget:
    def _call(self, url):
        from src.optimizer.query_prioritizer import _is_target
        return _is_target(url)

    def test_target_domain_detected(self):
        assert self._call("https://programamos.es/cursos") is True

    def test_subdomain_of_target_detected(self):
        assert self._call("https://blog.programamos.es/post") is True

    def test_competitor_url_is_not_target(self):
        assert self._call("https://openwebinars.net/cursos") is False

    def test_empty_url_is_not_target(self):
        assert self._call("") is False


class TestPrioritizeExperimental:
    """Tests de query_prioritizer.prioritize_experimental usando tmp_path."""

    def _make_fixture(self, tmp_path: pathlib.Path):
        run_dir = tmp_path / "geo" / "experimental" / "run_test"
        run_dir.mkdir(parents=True)

        scorecard = {
            "run_id": "run_test",
            "timestamp": "2026-05-06T10:00:00",
            "per_query_metrics": [
                {
                    "query_id": "Q001",
                    "query": "cursos de programación",
                    "category": "informacional",
                    "is_visible": False,
                    "target_citations": 0,
                    "total_citations": 3,
                    "som": 0.0,
                },
                {
                    "query_id": "Q002",
                    "query": "aprender python",
                    "category": "comparativa",
                    "is_visible": True,
                    "target_citations": 1,
                    "total_citations": 4,
                    "som": 25.0,
                },
                {
                    "query_id": "Q003",
                    "query": "programamos es web",
                    "category": "navegacional",
                    "is_visible": True,
                    "target_citations": 5,
                    "total_citations": 5,
                    "som": 100.0,
                },
            ],
        }
        raw_results = [
            {
                "query_id": "Q001",
                "answer": {
                    "citations": [
                        {"url": "https://competidor.es/cursos", "quote": "Aprende a programar"},
                        {"url": "https://otro.es/python", "quote": "Python desde cero"},
                        {"url": "https://tercero.es/java", "quote": "Java básico"},
                    ],
                    "sources_available_but_unused": [],
                },
            },
            {
                "query_id": "Q002",
                "answer": {
                    "citations": [
                        {"url": "https://competidor.es/python", "quote": "Python para todos"},
                        {"url": "https://programamos.es/python", "quote": "Nuestro curso"},
                    ],
                    "sources_available_but_unused": [],
                },
            },
        ]

        (run_dir / "scorecard.json").write_text(json.dumps(scorecard), encoding="utf-8")
        (run_dir / "raw_results.json").write_text(json.dumps(raw_results), encoding="utf-8")
        return tmp_path

    def test_returns_prioritized_queries(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_experimental

        data_dir = self._make_fixture(tmp_path)
        result = prioritize_experimental(data_dir, top_k=10)

        assert result["run_id"] == "run_test"
        assert result["mode"] == "experimental"
        assert len(result["queries"]) >= 1

    def test_not_visible_query_has_higher_score(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_experimental

        data_dir = self._make_fixture(tmp_path)
        result = prioritize_experimental(data_dir, top_k=10)

        query_ids = [q["query_id"] for q in result["queries"]]
        # Q001 (no visible, 3 citas de competidores) debe preceder a Q002
        assert query_ids[0] == "Q001"

    def test_high_som_query_excluded(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_experimental

        data_dir = self._make_fixture(tmp_path)
        result = prioritize_experimental(data_dir, top_k=10)

        query_ids = [q["query_id"] for q in result["queries"]]
        # Q003: visible con SoM=100% → debe excluirse
        assert "Q003" not in query_ids

    def test_no_data_dir_returns_empty(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_experimental

        empty_dir = tmp_path / "vacio"
        empty_dir.mkdir()
        result = prioritize_experimental(empty_dir, top_k=10)

        assert result["run_id"] is None
        assert result["queries"] == []

    def test_top_k_limits_results(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_experimental

        data_dir = self._make_fixture(tmp_path)
        result = prioritize_experimental(data_dir, top_k=1)

        assert len(result["queries"]) <= 1


class TestPrioritizeLive:
    """Tests de query_prioritizer.prioritize_live usando tmp_path."""

    def _make_fixture(self, tmp_path: pathlib.Path):
        live_dir = tmp_path / "geo" / "live"
        live_dir.mkdir(parents=True)

        live_data = {
            "run_id": "LIVE-2026-W18",
            "timestamp": "2026-05-04T09:00:00",
            "engines": ["gemini", "claude", "openai"],
            "results": [
                {
                    "query_id": "Q010",
                    "query_text": "mejores cursos online",
                    "query_category": "informacional",
                    "engine_coverage": 33.3,
                    "engines": {
                        "gemini": {"is_visible": True, "sentiment": "positive"},
                        "claude": {"is_visible": False, "sentiment": None},
                        "openai": {"is_visible": False, "sentiment": None},
                    },
                },
                {
                    "query_id": "Q011",
                    "query_text": "programamos.es review",
                    "query_category": "navegacional",
                    "engine_coverage": 100.0,
                    "engines": {
                        "gemini": {"is_visible": True, "sentiment": "positive"},
                        "claude": {"is_visible": True, "sentiment": "positive"},
                        "openai": {"is_visible": True, "sentiment": "positive"},
                    },
                },
            ],
        }

        (live_dir / "LIVE-2026-W18.json").write_text(json.dumps(live_data), encoding="utf-8")
        return tmp_path

    def test_returns_prioritized_queries(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_live

        data_dir = self._make_fixture(tmp_path)
        result = prioritize_live(data_dir, top_k=10)

        assert result["run_id"] == "LIVE-2026-W18"
        assert result["mode"] == "live"

    def test_full_coverage_query_excluded(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_live

        data_dir = self._make_fixture(tmp_path)
        result = prioritize_live(data_dir, top_k=10)

        query_ids = [q["query_id"] for q in result["queries"]]
        # Q011 con engine_coverage=100% no tiene motores faltantes → se excluye
        assert "Q011" not in query_ids

    def test_partial_coverage_query_included(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_live

        data_dir = self._make_fixture(tmp_path)
        result = prioritize_live(data_dir, top_k=10)

        query_ids = [q["query_id"] for q in result["queries"]]
        assert "Q010" in query_ids

    def test_no_live_data_returns_empty(self, tmp_path):
        from src.optimizer.query_prioritizer import prioritize_live

        empty_dir = tmp_path / "vacio"
        empty_dir.mkdir()
        result = prioritize_live(empty_dir, top_k=10)

        assert result["run_id"] is None
        assert result["queries"] == []


# ── metrics_aggregator: funciones de timeline ─────────────────────────────────
# Usan datos reales del repo (commitados por los workflows automáticos).
# No hay llamadas a APIs externas.


class TestTimelineExperimental:
    """Tests de metrics_aggregator.timeline_experimental."""

    def test_returns_list_of_points(self):
        from app.services.metrics_aggregator import timeline_experimental

        points = timeline_experimental(metric="visibility_rate")
        assert isinstance(points, list)
        # Con datos reales, debe haber al menos un punto
        assert len(points) >= 1

    def test_each_point_has_required_fields(self):
        from app.services.metrics_aggregator import timeline_experimental

        points = timeline_experimental(metric="visibility_rate")
        for p in points:
            assert "run_id" in p
            assert "timestamp" in p
            assert "value" in p

    def test_metric_avg_som(self):
        from app.services.metrics_aggregator import timeline_experimental

        points = timeline_experimental(metric="avg_som")
        assert isinstance(points, list)

    def test_metric_avg_citations(self):
        from app.services.metrics_aggregator import timeline_experimental

        points = timeline_experimental(metric="avg_citations")
        assert isinstance(points, list)

    def test_invalid_metric_raises_value_error(self):
        from app.services.metrics_aggregator import timeline_experimental
        import pytest

        with pytest.raises(ValueError, match="metric debe ser"):
            timeline_experimental(metric="metrica_invalida")

    def test_category_filter(self):
        from app.services.metrics_aggregator import timeline_experimental

        points = timeline_experimental(metric="visibility_rate", category="informacional")
        assert isinstance(points, list)

    def test_date_range_filter(self):
        from app.services.metrics_aggregator import timeline_experimental

        points = timeline_experimental(
            metric="visibility_rate",
            from_date="2026-01-01",
            to_date="2026-12-31",
        )
        assert isinstance(points, list)


class TestTimelineLive:
    """Tests de metrics_aggregator.timeline_live."""

    def test_engine_coverage_avg_no_engine_required(self):
        from app.services.metrics_aggregator import timeline_live

        points = timeline_live(metric="engine_coverage_avg")
        assert isinstance(points, list)
        assert len(points) >= 1

    def test_each_point_has_required_fields(self):
        from app.services.metrics_aggregator import timeline_live

        points = timeline_live(metric="engine_coverage_avg")
        for p in points:
            assert "run_id" in p
            assert "timestamp" in p
            assert "value" in p

    def test_engine_metric_requires_engine(self):
        from app.services.metrics_aggregator import timeline_live
        import pytest

        with pytest.raises(ValueError, match="Se requiere"):
            timeline_live(metric="visibility_rate")

    def test_engine_metric_with_engine(self):
        from app.services.metrics_aggregator import timeline_live

        points = timeline_live(metric="visibility_rate", engine="gemini")
        assert isinstance(points, list)

    def test_invalid_metric_raises_value_error(self):
        from app.services.metrics_aggregator import timeline_live
        import pytest

        with pytest.raises(ValueError):
            timeline_live(metric="metrica_invalida")


class TestTimelineSEO:
    """Tests de metrics_aggregator.timeline_seo."""

    def test_mobile_visibility_rate(self):
        from app.services.metrics_aggregator import timeline_seo

        points = timeline_seo(device="mobile", metric="performance")
        assert isinstance(points, list)
        assert len(points) >= 1

    def test_desktop_device(self):
        from app.services.metrics_aggregator import timeline_seo

        points = timeline_seo(device="desktop", metric="seo")
        assert isinstance(points, list)

    def test_invalid_device_raises_value_error(self):
        from app.services.metrics_aggregator import timeline_seo
        import pytest

        with pytest.raises(ValueError, match="device debe ser"):
            timeline_seo(device="tablet", metric="performance")

    def test_each_point_has_required_fields(self):
        from app.services.metrics_aggregator import timeline_seo

        points = timeline_seo(device="mobile", metric="performance")
        for p in points:
            assert "run_id" in p
            assert "timestamp" in p
            assert "value" in p


# ── live_loader: caminos adicionales ─────────────────────────────────────────


class TestLiveLoader:
    """Tests adicionales del live_loader para cubrir caminos no cubiertos."""

    def test_load_live_run_latest_alias(self):
        """El run_id 'latest' es un alias para load_latest_live()."""
        from app.services.live_loader import load_live_run, load_latest_live

        via_alias = load_live_run("latest")
        via_direct = load_latest_live()
        # Ambos deben devolver el mismo run_id
        if via_alias is not None and via_direct is not None:
            assert via_alias["run_id"] == via_direct["run_id"]

    def test_load_live_run_nonexistent_returns_none(self):
        from app.services.live_loader import load_live_run

        assert load_live_run("LIVE-9999-W99") is None

    def test_enrich_adds_coverage_avg_when_missing(self, tmp_path):
        """_enrich_live calcula engine_coverage_avg si no está en el fichero."""
        from app.services.live_loader import _enrich_live

        data = {
            "run_id": "LIVE-TEST",
            "results": [
                {"engine_coverage": 50.0},
                {"engine_coverage": 100.0},
            ],
        }
        enriched = _enrich_live(data)
        assert enriched["engine_coverage_avg"] == 75.0

    def test_enrich_preserves_existing_coverage_avg(self):
        """_enrich_live no sobreescribe engine_coverage_avg si ya existe."""
        from app.services.live_loader import _enrich_live

        data = {
            "run_id": "LIVE-TEST",
            "engine_coverage_avg": 42.0,
            "results": [{"engine_coverage": 100.0}],
        }
        enriched = _enrich_live(data)
        assert enriched["engine_coverage_avg"] == 42.0

    def test_list_live_files_empty_dir_returns_empty(self, tmp_path):
        from app.services import live_loader
        from app.settings import settings
        from unittest.mock import patch

        with patch.object(settings, "data_dir", tmp_path):
            files = live_loader.list_live_files()
        assert files == []
