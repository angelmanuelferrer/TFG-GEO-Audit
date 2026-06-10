# GEO-Audit — Frontend (React + Vite)

Dashboard web del sistema GEO-Audit: visualiza los resultados experimentales, la evaluación live multi-motor, las métricas SEO y las recomendaciones del optimizador que expone el backend FastAPI.

Stack: React 18, TypeScript, Vite, shadcn/ui (Radix + Tailwind), Zustand para estado y TanStack Query + axios para datos.

## Requisitos

- Node 20+
- Backend en marcha en `http://localhost:8000` (ver `../backend/README.md`), o usar los mocks (abajo)

## Instalación y scripts

```bash
cd frontend
npm install

npm run dev      # servidor de desarrollo en http://localhost:5173
npm run build    # build de producción en dist/
npm test         # tests unitarios (vitest)
npm run lint     # eslint
```

`npm install` también activa el hook pre-commit de Husky (ESLint --fix sobre los archivos staged).

## Variables de entorno (`.env`)

| Variable | Descripción | Por defecto |
|----------|-------------|-------------|
| `VITE_API_BASE_URL` | URL del backend | `http://localhost:8000` |
| `VITE_API_KEY` | Opcional; se envía como cabecera `X-API-Key` | — |

## Páginas

| Página | Ruta | Contenido |
|--------|------|-----------|
| `Index` | `/` | Visión general: último run experimental, live y SEO |
| `Experimental` | `/experimental` | Scorecards de los runs experimentales |
| `RunDetail` | `/experimental/:runId` | Detalle por consulta de un run |
| `Compare` | `/compare` | Comparación entre runs |
| `Live` | `/live` | Evaluación live multi-motor (Gemini, Claude, OpenAI) |
| `Seo` | `/seo` | Serie temporal de métricas PageSpeed |
| `Optimizer` | `/optimizer` | Priorización de consultas y recomendaciones GEO |
| `Jobs` | `/jobs` | Lanzar y monitorizar ejecuciones del pipeline |
