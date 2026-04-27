from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class MobileMetrics(BaseModel):
    performance: Optional[float] = None
    seo: Optional[float] = None
    accessibility: Optional[float] = None
    lcp: Optional[str] = None
    tbt: Optional[str] = None


class DesktopMetrics(BaseModel):
    performance: Optional[float] = None
    seo: Optional[float] = None
    accessibility: Optional[float] = None


class SeoSnapshot(BaseModel):
    fecha: str
    url: Optional[str] = None
    mobile: MobileMetrics
    desktop: DesktopMetrics


class SeoHistoryResponse(BaseModel):
    items: List[SeoSnapshot]
    total: int
