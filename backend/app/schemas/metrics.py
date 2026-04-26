from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class TimelinePoint(BaseModel):
    run_id: str
    timestamp: str
    value: Optional[float] = None


class TimelineResponse(BaseModel):
    metric: str
    engine: Optional[str] = None
    category: Optional[str] = None
    points: List[TimelinePoint]


class CoverageMatrixResponse(BaseModel):
    run_id: str
    matrix: Dict[str, Dict[str, float]]


class SentimentDistributionResponse(BaseModel):
    run_id: str
    distribution: Dict[str, Dict[str, int]]


class BrandMentionItem(BaseModel):
    run_id: str
    query_id: Optional[str] = None
    engine: Optional[str] = None
    source: str
    position: int
    context: str


class BrandMentionsResponse(BaseModel):
    items: List[BrandMentionItem]
    total: int
