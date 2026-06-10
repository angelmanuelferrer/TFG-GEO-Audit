# GEO-Audit — Backend (FastAPI)

API REST que sirve al dashboard los resultados generados por el pipeline de investigación: scorecards experimentales, evaluaciones live, métricas SEO y recomendaciones del optimizador. No usa base de datos externa para los datos de investigación: todo se lee como JSON desde `../data/`. La única base SQLite (`jobs.db`) almacena el estado de los jobs asíncronos.

## Requisitos

- Python 3.11+
- Los datos en `../data/` (incluidos en el repositorio)

## Instalación y arranque

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

La documentación interactiva queda en `http://localhost:8000/docs`.

## Tests

```bash
pytest tests/                  # toda la suite
pytest tests/test_overview.py  # un único archivo
pytest --cov=app --cov-report=xml  # con cobertura (genera coverage.xml)
```

## Endpoints

| Router | Prefijo | Qué sirve |
|--------|---------|-----------|
| `catalog` | `/api` | Lista de runs disponibles y definiciones de métricas |
| `experimental` | `/api/runs/experimental` | Scorecards y resultados crudos de `data/geo/experimental/run_*/` |
| `live` | `/api/runs/live` | Resultados de evaluación live de `data/geo/live/` |
| `seo` | `/api/seo` | Métricas PageSpeed de `data/seo/` |
| `metrics` | `/api/metrics` | Métricas GEO agregadas entre runs |
| `overview` | `/api/dashboard/overview` | Snapshot combinado (último experimental + live + SEO) |
| `optimizer` | `/api/optimizer` | Priorización de consultas y recomendaciones GEO (`src/optimizer/`) |
| `jobs` | `/api/jobs` | Cola de jobs asíncronos (lanzar y consultar ejecuciones del pipeline) |

## Servicios clave

- `app/services/run_loader.py` — normaliza scorecards v1/v2 al leerlos.
- `app/services/metrics_aggregator.py` — agrega métricas entre runs.
- `app/services/job_runner.py` — ejecuta pasos del pipeline como jobs en segundo plano.

## Autenticación

Opcional: si se define la variable de entorno `DASHBOARD_API_KEY`, todos los endpoints exigen la cabecera `X-API-Key` con ese valor. Sin la variable, la API queda abierta (modo desarrollo).
