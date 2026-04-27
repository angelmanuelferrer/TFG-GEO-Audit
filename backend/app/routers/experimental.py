from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import verify_api_key
from app.services import metrics_aggregator, run_loader

router = APIRouter()


@router.get("", dependencies=[Depends(verify_api_key)])
def list_experimental_runs():
    summaries = run_loader.list_runs_summary()
    return {"items": summaries, "total": len(summaries)}


# IMPORTANTE: /compare debe declararse ANTES de /{run_id}
@router.get("/compare", dependencies=[Depends(verify_api_key)])
def compare_runs(
    a: str = Query(...),
    b: str = Query(...),
):
    try:
        result = metrics_aggregator.compare_experimental(a, b)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@router.get("/{run_id}", dependencies=[Depends(verify_api_key)])
def get_experimental_run(run_id: str):
    sc = run_loader.load_scorecard(run_id)
    if not sc:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' no encontrado")
    sc["_derived"] = run_loader.compute_derived(sc)
    return sc


@router.get("/{run_id}/raw", dependencies=[Depends(verify_api_key)])
def get_raw_results(
    run_id: str,
    limit: int = Query(10, ge=1, le=200),
    offset: int = Query(0, ge=0),
    with_errors: bool = Query(True),
):
    raw = run_loader.load_raw_results(run_id)
    if raw is None:
        raise HTTPException(status_code=404, detail=f"raw_results para '{run_id}' no encontrado")

    if not with_errors:
        raw = [r for r in raw if not r.get("error")]

    total = len(raw)
    page = raw[offset : offset + limit]
    return {"items": page, "total": total, "limit": limit, "offset": offset}


@router.get("/{run_id}/queries/{query_id}", dependencies=[Depends(verify_api_key)])
def get_run_query(run_id: str, query_id: str):
    sc = run_loader.load_scorecard(run_id)
    if not sc:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' no encontrado")

    # Buscar en per_query_metrics por query_id o texto
    query_meta = None
    for pq in sc.get("per_query_metrics", []):
        if pq.get("query_id") == query_id:
            query_meta = pq
            break

    if not query_meta:
        raise HTTPException(status_code=404, detail=f"Query '{query_id}' no encontrada en run '{run_id}'")

    # Buscar en raw_results
    raw_all = run_loader.load_raw_results(run_id)
    raw_entry: dict = {}
    if raw_all:
        for r in raw_all:
            if r.get("query_id") == query_id or r.get("query") == query_meta.get("query"):
                raw_entry = r
                break

    return {
        "query_id": query_id,
        "metrics": query_meta,
        "raw": {
            "answer": raw_entry.get("answer"),
            "citations": raw_entry.get("citations", []),
            "sources_used": raw_entry.get("sources_used", []),
            "sources_available_but_unused": raw_entry.get("sources_available_but_unused", []),
        },
    }
