from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import verify_api_key
from app.services import metrics_aggregator

router = APIRouter()


@router.get("/timeline/experimental", dependencies=[Depends(verify_api_key)])
def timeline_experimental(
    metric: str = Query(...),
    category: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    try:
        points = metrics_aggregator.timeline_experimental(metric, category, from_date, to_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"metric": metric, "category": category, "points": points}


@router.get("/timeline/live", dependencies=[Depends(verify_api_key)])
def timeline_live(
    metric: str = Query(...),
    engine: Optional[str] = Query(None),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    try:
        points = metrics_aggregator.timeline_live(metric, engine, from_date, to_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"metric": metric, "engine": engine, "points": points}


@router.get("/timeline/seo", dependencies=[Depends(verify_api_key)])
def timeline_seo(
    device: str = Query(...),
    metric: str = Query(...),
    from_date: Optional[str] = Query(None, alias="from"),
    to_date: Optional[str] = Query(None, alias="to"),
):
    try:
        points = metrics_aggregator.timeline_seo(device, metric, from_date, to_date)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"metric": metric, "device": device, "points": points}


@router.get("/coverage-matrix", dependencies=[Depends(verify_api_key)])
def coverage_matrix(run_id: str = Query(...)):
    matrix = metrics_aggregator.coverage_matrix(run_id)
    if not matrix:
        raise HTTPException(status_code=404, detail=f"Run Live '{run_id}' no encontrado o sin datos")
    categories = list(matrix.keys())
    engines: list = []
    for eng_dict in matrix.values():
        for e in eng_dict:
            if e not in engines:
                engines.append(e)
    return {"run_id": run_id, "categories": categories, "engines": engines, "matrix": matrix}


@router.get("/sentiment-distribution", dependencies=[Depends(verify_api_key)])
def sentiment_distribution(
    run_id: str = Query(...),
    engine: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
):
    dist = metrics_aggregator.sentiment_distribution(run_id, engine, category)
    # Transformar {engine: {sentiment: count}} → SentimentDistribution[]
    result = []
    for eng, counts in dist.items():
        result.append({
            "engine": eng,
            "POSITIVO": counts.get("POSITIVO", 0),
            "NEUTRO": counts.get("NEUTRO", 0),
            "NEGATIVO": counts.get("NEGATIVO", 0),
            "null": counts.get("null", 0),
        })
    return result


@router.get("/brand-mentions", dependencies=[Depends(verify_api_key)])
def brand_mentions(
    run_id: str = Query(...),
    query_id: Optional[str] = Query(None),
    engine: Optional[str] = Query(None),
):
    mentions = metrics_aggregator.brand_mentions(run_id, query_id, engine)
    return {"items": mentions, "total": len(mentions)}
