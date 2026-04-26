from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.deps import verify_api_key
from app.services import live_loader

router = APIRouter()


@router.get("", dependencies=[Depends(verify_api_key)])
def list_live_runs():
    summaries = live_loader.list_live_summaries()
    return {"items": summaries, "total": len(summaries)}


# IMPORTANTE: /latest y /compare ANTES de /{run_id}
@router.get("/latest", dependencies=[Depends(verify_api_key)])
def get_latest_live():
    data = live_loader.load_latest_live()
    if not data:
        raise HTTPException(status_code=404, detail="No hay runs Live disponibles")
    return data


@router.get("/compare", dependencies=[Depends(verify_api_key)])
def compare_live(
    a: str = Query(...),
    b: str = Query(...),
):
    data_a = live_loader.load_live_run(a)
    data_b = live_loader.load_live_run(b)
    if not data_a:
        raise HTTPException(status_code=404, detail=f"Run Live '{a}' no encontrado")
    if not data_b:
        raise HTTPException(status_code=404, detail=f"Run Live '{b}' no encontrado")

    # Diff a nivel de summary por motor
    deltas = {}
    for engine in set(list(data_a.get("summary", {}).keys()) + list(data_b.get("summary", {}).keys())):
        sa = data_a.get("summary", {}).get(engine, {})
        sb = data_b.get("summary", {}).get(engine, {})
        deltas[engine] = {
            "visibility_rate": _delta(sa.get("visibility_rate"), sb.get("visibility_rate")),
            "avg_som": _delta(sa.get("avg_som"), sb.get("avg_som")),
        }

    return {
        "run_a": a,
        "run_b": b,
        "delta_engine_coverage_avg": _delta(
            data_a.get("engine_coverage_avg"), data_b.get("engine_coverage_avg")
        ),
        "deltas_by_engine": deltas,
    }


@router.get("/{run_id}", dependencies=[Depends(verify_api_key)])
def get_live_run(run_id: str):
    data = live_loader.load_live_run(run_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Run Live '{run_id}' no encontrado")
    return data


@router.get("/{run_id}/queries/{query_id}", dependencies=[Depends(verify_api_key)])
def get_live_run_query(run_id: str, query_id: str):
    data = live_loader.load_live_run(run_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Run Live '{run_id}' no encontrado")

    for result in data.get("results", []):
        if result.get("query_id") == query_id:
            return result

    raise HTTPException(status_code=404, detail=f"Query '{query_id}' no encontrada en '{run_id}'")


def _delta(a, b):
    if a is not None and b is not None:
        return round(b - a, 2)
    return None
