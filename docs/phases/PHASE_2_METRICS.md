# Fase 2: Framework de Metricas

**Duracion estimada**: 1 semana
**Dependencias**: Fase 1 completada
**Coste**: ~$0.50 (pruebas)

---

## Objetivo

Implementar el framework completo de metricas GEO, el evaluador live de LLMs reales, el analisis de sentimiento y el scorecard integrado. Al final de esta fase, cada run del pipeline produce un scorecard JSON completo y comparable.

---

## Tareas

### 2.1 Metricas GEO cuantitativas

**Ref. arquitectura**: Seccion 6.1

**Archivo**: `src/metrics/geo_metrics.py`

**Implementar las 6 metricas**:

| Metrica | Formula | Tipo |
|---------|---------|------|
| **Visibilidad** | `1 si target_url in citations, 0 si no` | Binaria → ratio |
| **Share of Model (SoM)** | `target_citations / total_citations * 100` | Porcentaje |
| **Ranking** | Posicion de primera citacion del target (1-indexed) | Ordinal |
| **PAWC** | `sum(words_target_citation_i * 1/log2(pos+1))` | Continua |
| **Coverage** | `queries_con_visibilidad / total_queries` (total + por categoria) | Ratio |
| **Citation Rate** | `citas_correctas_target / veces_target_retrieved` | Ratio |

**Interfaz**:
```python
class GEOMetricsCalculator:
    def calculate_per_query(self, judge_output: dict, target_domain: str) -> dict
    def calculate_aggregated(self, per_query_results: list) -> dict
    def calculate_by_category(self, per_query_results: list, queries_config: dict) -> dict
```

---

### 2.2 Analisis de sentimiento de menciones

**Ref. arquitectura**: Seccion 7.5

**Archivo**: `src/metrics/sentiment.py`

**Implementar**:
- `BrandSentimentAnalyzer`: clasifica menciones como POSITIVO/NEUTRO/NEGATIVO
- Usa `gpt-4o-mini` (bajo coste) con `temperature=0`
- Entrada: lista de menciones con contexto (de CitationExtractor)
- Salida: distribucion de sentimientos + ratio positivo

---

### 2.3 GEO Content Scorer

**Ref. arquitectura**: Secciones 9.3, 21.1, 21.2

**Archivo**: `src/metrics/content_scorer.py`

**Implementar**:
- `GEOContentScorer`: evalua la optimizacion GEO de una pagina HTML
  - Machine scannability (headers, listas, parrafos cortos)
  - Citation readiness (estadisticas, fechas, nombres propios, enlaces)
  - Semantic structure (h1 unico, jerarquia correcta)
  - Schema.org (presencia y completitud)
  - Meta completeness (title, description, og:*)
- `CitationReadinessScorer`: scoring especifico de "citabilidad"
- (Opcional) `ContentPerplexityScorer`: perplejidad con modelo local — solo en Kaggle con GPU

---

### 2.4 Live LLM Evaluator

**Ref. arquitectura**: Seccion 17

**Archivo**: `src/evaluation/live_evaluator.py`

**Implementar**:
- `LiveLLMEvaluator`: consulta ChatGPT, Gemini y Perplexity con prompts fijos
- Analisis de respuesta: mention_count, url_present, first_mention_position, sentiment, recommendation_strength, competitors_mentioned
- Calculo de Engine Coverage (EC): engines_que_citan / total_engines
- Guardado de resultados en `data/geo/live/`

**Archivo**: `collect_metrics/collect_geo_live.py`
- Script standalone para ejecutar desde GitHub Actions
- Lee queries de `config/queries.json` (usa un subset de 5 queries para coste)
- Guarda JSON timestamped

---

### 2.5 GitHub Actions para GEO Live

**Ref. arquitectura**: Seccion 17.4

**Archivo**: `.github/workflows/geo_live_audit.yml`

**Implementar**:
- Cron: 09:00 UTC diario (1h despues de SEO)
- Ejecuta `collect_metrics/collect_geo_live.py`
- Auto-commit resultados a `data/geo/live/`
- Secrets necesarios: `OPENAI_API_KEY`, `GOOGLE_API_KEY`

---

### 2.6 Scorecard integrado

**Ref. arquitectura**: Seccion 6.4

**Implementar** funcion que genera el scorecard completo:

```json
{
  "run_id": "2026-02-15_001",
  "config_hash": "sha256:...",
  "timestamp": "2026-02-15T10:00:00Z",
  "target_url": "https://programamos.es",
  "geo_metrics": {
    "visibilidad_total": 0.73,
    "som_promedio": 28.5,
    "rank_promedio": 2.1,
    "pawc_total": 342.7,
    "coverage": {"total": 0.73, "informacional": 0.60, "comparativa": 0.80, "navegacional": 1.00},
    "citation_rate": 0.85,
    "sentiment": "positivo"
  },
  "seo_metrics": { ... },
  "meta": { "model": "gpt-4o", "temperature": 0, "seed": 42, "n_queries": 15 }
}
```

---

### 2.7 Mejorar reporter de Notion

**Implementar**:
- Enviar el scorecard completo a Notion (no solo las metricas basicas actuales)
- Incluir metricas por categoria (informacional/comparativa/navegacional)
- Incluir sentimiento

---

## Criterios de Aceptacion

- [ ] `GEOMetricsCalculator` calcula las 6 metricas correctamente (verificar con datos de ejemplo)
- [ ] `BrandSentimentAnalyzer` clasifica menciones en 3 categorias
- [ ] `GEOContentScorer` produce scores 0-100 para cada dimension
- [ ] `LiveLLMEvaluator` consulta al menos ChatGPT y Gemini y produce resultados
- [ ] `collect_geo_live.py` funciona como script standalone
- [ ] GitHub Actions workflow creado (se puede testear con `workflow_dispatch`)
- [ ] Scorecard JSON generado con todas las metricas
- [ ] Reporter de Notion actualizado con scorecard completo
- [ ] Un run de prueba end-to-end produce scorecard valido

---

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Perplexity API puede no estar disponible o cambiar | Hacerlo opcional; el sistema funciona con 2 engines |
| Coste de sentiment con muchas menciones | Batch de menciones, maximo 20 por run |
| GPT-4o-mini insuficiente para sentiment en espanol | Test con 10 ejemplos manuales; fallback a GPT-4o si precision < 80% |
