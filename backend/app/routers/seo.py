from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import verify_api_key
from app.services import seo_loader

router = APIRouter()


@router.get("/latest", dependencies=[Depends(verify_api_key)])
def get_latest_seo():
    data = seo_loader.load_latest_seo()
    if not data:
        raise HTTPException(status_code=404, detail="No hay métricas SEO disponibles")
    return data


@router.get("/history", dependencies=[Depends(verify_api_key)])
def get_seo_history(
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
    device: str = Query("both"),
):
    snapshots = seo_loader.load_seo_history(from_date, to_date)

    if device == "mobile":
        snapshots = [{"fecha": s["fecha"], "mobile": s.get("mobile", {})} for s in snapshots]
    elif device == "desktop":
        snapshots = [{"fecha": s["fecha"], "desktop": s.get("desktop", {})} for s in snapshots]

    return snapshots


@router.get("/correlation", dependencies=[Depends(verify_api_key)])
def seo_correlation():
    raise HTTPException(status_code=501, detail="No implementado en Fase 1")
