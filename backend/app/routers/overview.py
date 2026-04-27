from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import verify_api_key
from app.services import live_loader, run_loader, seo_loader

router = APIRouter()


@router.get("", dependencies=[Depends(verify_api_key)])
def dashboard_overview():
    # Target
    try:
        import sys, pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).parents[4]))
        from src.config import get_target_url, get_target_brand
        target = {"url": get_target_url(), "brand": get_target_brand()}
    except Exception:
        target = {"url": None, "brand": None}

    # Experimental: último run + delta vs anterior
    summaries = run_loader.list_runs_summary()
    exp_data = None
    if summaries:
        latest = summaries[0]
        exp_data = {**latest}
        if len(summaries) >= 2:
            prev = summaries[1]
            exp_data["delta_vs_previous"] = {
                "visibility_rate": _delta(prev.get("visibility_rate"), latest.get("visibility_rate")),
                "avg_som": _delta(prev.get("avg_som"), latest.get("avg_som")),
                "avg_citations": _delta(prev.get("avg_citations"), latest.get("avg_citations")),
            }
        else:
            exp_data["delta_vs_previous"] = None

    # Live: último run
    live_raw = live_loader.load_latest_live()
    live_data = None
    if live_raw:
        live_data = {
            "latest_run_id": live_raw.get("run_id"),
            "timestamp": live_raw.get("timestamp"),
            "engine_coverage_avg": live_raw.get("engine_coverage_avg"),
            "by_engine": live_raw.get("summary", {}),
        }

    # SEO: última medición
    seo_raw = seo_loader.load_latest_seo()
    seo_data = None
    if seo_raw:
        mobile = seo_raw.get("mobile", {})
        desktop = seo_raw.get("desktop", {})
        seo_data = {
            "fecha": seo_raw.get("fecha"),
            "mobile": {
                "performance": mobile.get("performance"),
                "seo": mobile.get("seo"),
                "accessibility": mobile.get("accessibility"),
                "lcp": mobile.get("lcp"),
            },
            "desktop": {
                "performance": desktop.get("performance"),
                "seo": desktop.get("seo"),
                "accessibility": desktop.get("accessibility"),
            },
        }

    return {
        "target": target,
        "experimental": exp_data,
        "live": live_data,
        "seo": seo_data,
        "alerts": [],
    }


def _delta(a, b):
    if a is not None and b is not None:
        return round(b - a, 2)
    return None
