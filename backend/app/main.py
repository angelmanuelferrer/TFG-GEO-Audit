from __future__ import annotations

import sys
import pathlib

# Añadir el raíz del repo al path para poder importar src/
PROJECT_ROOT = pathlib.Path(__file__).parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import settings
from app.routers import catalog, experimental, live, metrics, overview, seo, optimizer, jobs
from app.services.job_runner import init_db


app = FastAPI(
    title="GEO-Audit Dashboard API",
    version="1.0.0",
    description="API REST para el dashboard de visibilidad GEO de programamos.es",
)

# Inicializa la tabla de jobs en SQLite al arrancar
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(catalog.router, prefix="/api", tags=["catalog"])
app.include_router(experimental.router, prefix="/api/runs/experimental", tags=["experimental"])
app.include_router(live.router, prefix="/api/runs/live", tags=["live"])
app.include_router(seo.router, prefix="/api/seo", tags=["seo"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(overview.router, prefix="/api/dashboard/overview", tags=["overview"])
app.include_router(optimizer.router, prefix="/api/optimizer", tags=["optimizer"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
