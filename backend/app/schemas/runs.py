from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ── Experimental ──────────────────────────────────────────────────────────────

class BrandMention(BaseModel):
    source: str
    position: int
    context: str


class QueryMetrics(BaseModel):
    query_id: Optional[str] = None
    query: str
    category: Optional[str] = None
    total_citations: int
    target_citations: int
    is_visible: bool
    som: float
    first_citation_rank: Optional[int] = None
    brand_mentions: List[BrandMention] = []
    pawc: Optional[float] = None
    citation_rate: Optional[float] = None


class CategoryStats(BaseModel):
    n: int
    n_errors: int
    n_successful: int
    visibility_rate: float
    avg_som: float
    avg_citations: float


class DerivedStats(BaseModel):
    avg_first_rank_by_category: Dict[str, Optional[float]]
    avg_pawc_by_category: Dict[str, Optional[float]]


class ScorecardResponse(BaseModel):
    run_id: str
    timestamp: str
    target_url: str
    target_brand: str
    rotation_block: Optional[str] = None
    n_queries: int
    n_successful: int
    n_errors: int
    visibility_rate: float
    avg_som: float
    avg_citations: float
    by_category: Dict[str, CategoryStats] = {}
    per_query_metrics: List[QueryMetrics] = []
    _derived: Optional[DerivedStats] = None

    model_config = {"populate_by_name": True}


class RunSummary(BaseModel):
    run_id: str
    timestamp: str
    rotation_block: Optional[str] = None
    n_queries: int
    n_successful: int
    n_errors: int
    visibility_rate: float
    avg_som: float
    avg_citations: float


class RunListResponse(BaseModel):
    items: List[RunSummary]
    total: int


class QueryRawDetail(BaseModel):
    answer: Optional[str] = None
    citations: List[Dict[str, Any]] = []
    sources_used: List[str] = []
    sources_available_but_unused: List[str] = []


class QueryDetailResponse(BaseModel):
    query_id: Optional[str] = None
    metrics: QueryMetrics
    raw: QueryRawDetail


class CompareDeltas(BaseModel):
    visibility_rate: Optional[float] = None
    avg_som: Optional[float] = None
    avg_citations: Optional[float] = None


class RankingShift(BaseModel):
    query_id: str
    from_rank: Optional[int] = None
    to_rank: Optional[int] = None


class SomShift(BaseModel):
    query_id: str
    from_som: float
    to_som: float
    delta: float


class CompareResponse(BaseModel):
    run_a: str
    run_b: str
    deltas: CompareDeltas
    queries_gained: List[str]
    queries_lost: List[str]
    queries_stable_visible: List[str]
    ranking_shifts: List[RankingShift]
    som_shifts: List[SomShift]


class PaginatedRaw(BaseModel):
    items: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


# ── Live ──────────────────────────────────────────────────────────────────────

class EngineQueryResult(BaseModel):
    total_citations: int
    target_citations: int
    is_visible: bool
    som: float
    first_citation_rank: Optional[int] = None
    brand_mentions: List[BrandMention] = []
    sentiment: Optional[str] = None


class LiveQueryResult(BaseModel):
    query_id: str
    query_text: str
    query_category: Optional[str] = None
    engine_coverage: float
    engines: Dict[str, EngineQueryResult]


class EngineSummary(BaseModel):
    visibility_rate: float
    avg_som: float
    avg_first_rank: Optional[float] = None
    n_queries: int
    n_visible: int


class LiveRunResponse(BaseModel):
    run_id: str
    timestamp: str
    engines: List[str]
    engine_tiers: Dict[str, str] = {}
    n_queries: int
    results: List[LiveQueryResult] = []
    summary: Dict[str, EngineSummary] = {}
    engine_coverage_avg: float
    delta_vs_prev_week: Optional[Any] = None


class LiveRunSummary(BaseModel):
    run_id: str
    timestamp: str
    engines: List[str]
    n_queries: int
    engine_coverage_avg: float


class LiveListResponse(BaseModel):
    items: List[LiveRunSummary]
    total: int
