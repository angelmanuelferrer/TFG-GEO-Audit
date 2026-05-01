from __future__ import annotations

import sys
import pathlib

PROJECT_ROOT = pathlib.Path(__file__).parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.deps import verify_api_key
from app.settings import settings
from src.optimizer.query_prioritizer import prioritize

router = APIRouter()


class AnalyzeRequest(BaseModel):
    query_ids: List[str]
    mode: Optional[Literal["experimental", "live"]] = "experimental"


@router.get("/prioritize", dependencies=[Depends(verify_api_key)])
def get_prioritize(
    mode: Literal["experimental", "live"] = Query("experimental"),
    top_k: int = Query(15, ge=1, le=50),
):
    result = prioritize(mode=mode, data_dir=settings.data_dir, top_k=top_k)
    if result["run_id"] is None:
        raise HTTPException(status_code=404, detail=f"No hay runs de tipo '{mode}' disponibles.")
    return result


@router.post("/analyze", dependencies=[Depends(verify_api_key)])
async def post_analyze(body: AnalyzeRequest):
    """Lanza el GEOOptimizer para las queries seleccionadas."""
    from src.optimizer.geo_optimizer import GEOOptimizer

    prioritized = prioritize(mode=body.mode, data_dir=settings.data_dir, top_k=50)
    selected = [q for q in prioritized["queries"] if q["query_id"] in body.query_ids]

    if not selected:
        raise HTTPException(status_code=404, detail="Ninguna de las query_ids enviadas aparece en el run más reciente.")

    try:
        optimizer = GEOOptimizer()
        result = await optimizer.analyze(queries=selected, run_id=prioritized["run_id"])
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        err = str(e)
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            raise HTTPException(status_code=429, detail="Cuota de la API Gemini agotada temporalmente. Espera 1 minuto e inténtalo de nuevo.")
        if "503" in err or "UNAVAILABLE" in err:
            raise HTTPException(status_code=503, detail="Gemini no disponible por alta demanda. Inténtalo en unos segundos.")
        raise HTTPException(status_code=500, detail=err)

    return result
