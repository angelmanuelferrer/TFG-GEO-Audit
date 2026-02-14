# Fase 3: Experimentacion Controlada

**Duracion estimada**: 4 semanas (Semanas 5-8)
**Dependencias**: Fase 2 completada
**Coste**: ~$3.15 (15 runs experimentales)

---

## Objetivo

Ejecutar el experimento longitudinal completo: medir el impacto de optimizaciones progresivas SEO+GEO en el contenido de programamos.es sobre su visibilidad en motores generativos. Esta fase produce los **datos centrales del TFG**.

---

## Protocolo Experimental

### Variables

| Variable | Tipo | Control |
|----------|------|---------|
| Queries | Controlada | 15 queries fijas de `config/queries.json` |
| Pipeline RAG | Controlada | Codigo congelado (tag Git por run) |
| Modelo Judge | Controlada | GPT-4o, temp=0, seed=42 |
| Embeddings | Controlada | text-embedding-3-small |
| Chunk size/overlap | Controlada | 1024/128 tokens |
| Competidores | Controlada | Lista fija en config |
| **Contenido web target** | **Independiente** | Cambia entre fases |
| **Metricas GEO** | **Dependiente** | Se mide cada run |
| Metricas SEO | Covariable | Se registra, no se manipula |

### Protocolo por run

1. Verificar config hash (debe coincidir con runs anteriores)
2. Scrape contenido actual (target + competidores) → guardar snapshot en `data/content/`
3. Ejecutar pipeline completo
4. Extraer metricas → scorecard
5. Guardar con timestamp + config_hash en `data/geo/experimental/`
6. Repetir 3 veces para medir varianza
7. Comparar con runs anteriores

---

## Tareas

### 3.1 Congelar pipeline (pre-baseline)

- [ ] Tag Git: `v1.0-experimental-freeze`
- [ ] `pip freeze > requirements-frozen.txt` con versiones exactas
- [ ] Verificar que `config/experiment_config.json` tiene hash SHA256
- [ ] Documentar version exacta de la API de OpenAI

---

### 3.2 Run Baseline (Semana 5)

**3 repeticiones del pipeline sin ningun cambio en programamos.es**

Entregables:
- [ ] `data/geo/experimental/baseline_001/` con scorecard
- [ ] `data/geo/experimental/baseline_002/` con scorecard
- [ ] `data/geo/experimental/baseline_003/` con scorecard
- [ ] `data/content/baseline/` con snapshots HTML
- [ ] Calcular media y desviacion estandar de cada metrica
- [ ] Verificar reproducibilidad: CV (coeficiente de variacion) < 0.15

**Metricas baseline a registrar**:
- Visibilidad total
- SoM promedio
- Rank promedio
- PAWC total
- Coverage por categoria
- GEO Content Score del target
- GEO Content Score de competidores

---

### 3.3 Intervencion 1: Estructura HTML (Semanas 5-6)

**Cambios en programamos.es**:
- Anadir Schema.org JSON-LD (Organization, WebSite, FAQPage)
- Corregir jerarquia de headings (h1 unico, h2-h6 secuenciales)
- Anadir datos estructurados a paginas clave
- Mejorar meta tags (title, description, og:*)

**Runs post-cambio**: 3 repeticiones → `data/geo/experimental/intervention_1_NNN/`

---

### 3.4 Intervencion 2: Contenido (Semanas 6-7)

**Cambios en programamos.es**:
- Anadir estadisticas explicitas (numeros, porcentajes, fechas)
- Incluir citas y referencias a fuentes externas
- Mejorar claridad semantica (topic sentences, parrafos concisos)
- Anadir listas y tablas donde sea apropiado

**Runs post-cambio**: 3 repeticiones → `data/geo/experimental/intervention_2_NNN/`

---

### 3.5 Intervencion 3: Optimizacion GEO Avanzada (Semanas 7-8)

**Cambios en programamos.es**:
- Reducir perplejidad del contenido (frases claras sujeto-verbo-objeto)
- Machine scannability: estructura parseable para LLMs
- Citation readiness: datos verificables destacados
- Authority signals: credenciales, testimonios, partnerships

**Runs post-cambio**: 3 repeticiones → `data/geo/experimental/intervention_3_NNN/`

---

### 3.6 Intervencion 4: Paginas Generadas por IA (Semana 8)

**Dependencia**: Fase 4 completada

**Cambios en programamos.es**:
- Desplegar 2-3 paginas generadas por el Page Generator (Fase 4)
- Re-evaluar con el pipeline completo

**Runs post-cambio**: 3 repeticiones → `data/geo/experimental/intervention_4_NNN/`

---

### 3.7 Recoleccion Live continua

Durante toda la Fase 3:
- GitHub Actions ejecutando `collect_geo_live.py` diariamente
- Datos acumulandose en `data/geo/live/`
- Estos datos son complementarios (no reproducibles, pero miden impacto real)

---

## Estructura de Datos Resultante

```
data/geo/experimental/
├── baseline_001/
│   ├── config.json          # Config congelada + hash
│   ├── queries.json         # Queries usadas
│   ├── raw_responses.json   # Respuestas completas del judge
│   ├── citations.json       # Citaciones extraidas
│   ├── metrics.json         # Metricas por query
│   └── scorecard.json       # Scorecard agregado
├── baseline_002/
├── baseline_003/
├── intervention_1_001/
├── intervention_1_002/
├── intervention_1_003/
├── intervention_2_001/
│   ...
├── intervention_3_003/
├── intervention_4_001/
├── intervention_4_002/
└── intervention_4_003/
```

---

## Criterios de Aceptacion

- [ ] Baseline completado con 3 repeticiones y CV < 0.15
- [ ] Al menos 3 intervenciones ejecutadas con 3 runs cada una
- [ ] Snapshots HTML guardados para cada fase
- [ ] Scorecards JSON validos y comparables entre runs
- [ ] Datos live acumulados durante todo el periodo
- [ ] Tag Git por cada run experimental
- [ ] Tabla resumen de metricas por intervencion (CSV o JSON)

---

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Programamos.es no acepta los cambios sugeridos | Negociar con el profesor; documentar cambios propuestos vs implementados |
| CV > 0.15 en baseline | Aumentar repeticiones a 5; investigar fuente de varianza |
| OpenAI actualiza GPT-4o durante el experimento | Registrar `model_version` en cada run; documentar cambio si ocurre |
| Competidores cambian su contenido | Los snapshots guardan el estado; el efecto se documenta como limitacion |
