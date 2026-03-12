# Arquitectura Live

> **Versión**: 1.0 | **Última actualización**: Marzo 2026
> Este documento describe el sistema de evaluación Live: cómo validamos las métricas del simulador experimental con motores generativos reales y búsqueda web nativa.

---

## 1. Propósito

El [modo experimental](02_EXPERIMENTAL.md) aísla el efecto del contenido sobre la citación controlando por retrieval. Pero un sitio web vive en un ecosistema real donde el retrieval **sí** importa: si Google no indexa tu página, ningún motor generativo la encontrará, por muy bueno que sea tu contenido.

El modo Live valida que las mejoras medidas en el simulador se traducen en mejoras en el mundo real. Mide el pipeline **completo**:

```
Query del usuario
      │
      ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  BÚSQUEDA    │ ──► │  RETRIEVAL   │ ──► │  GENERACIÓN  │
│  WEB REAL    │     │  (indexación,│     │  (citación,  │
│              │     │   authority, │     │   resumen)   │
│  Google,     │     │   freshness) │     │              │
│  Bing, etc.  │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
        SEO influye aquí ───────┘               │
        GEO influye aquí ──────────────────────┘
```

**SEO como primera etapa de filtrado**: Si los crawlers de IA (GPTBot, ClaudeBot, PerplexityBot) no pueden acceder a la página, o si los motores de búsqueda no la indexan bien, no importa lo optimizado que esté el contenido para GEO.

---

## 2. Evaluación multi-motor

### 2.1. Cuatro motores, cuatro proveedores

| Motor | Modelo | Proveedor de búsqueda | Coste búsqueda | Coste tokens (~7K in + 1K out) | Total/query | 100 queries |
|-------|--------|-----------------------|----------------|-------------------------------|-------------|-------------|
| **Gemini** | 2.5 Flash | Google Search | GRATIS (1500/día) | ~$0.005 | ~$0.005 | ~$0.50 |
| **DeepSeek** | V3.2 | Propio | Por confirmar | ~$0.002 | ~$0.003 | ~$0.30 |
| **GPT-4o-mini** | GPT-4o-mini | Bing | $0.01/búsqueda | ~$0.002 | ~$0.012 | ~$1.20 |
| **Claude** | Haiku 4.5 | Propio | $0.01/búsqueda | ~$0.012 | ~$0.022 | ~$2.20 |

### 2.2. Motores descartados

| Motor | Modelo | Coste/query | Razón de exclusión |
|-------|--------|-------------|-------------------|
| Claude Sonnet | Sonnet 4.5 | ~$0.046 | Presupuesto insuficiente para 9 semanas |
| GPT-4o | GPT-4o | ~$0.06 | Mismo proveedor e índice (Bing) que GPT-4o-mini → redundante |

**Decisión de diversidad sobre potencia**: Es más valioso tener 4 proveedores distintos (Google, DeepSeek, OpenAI, Anthropic) que 2 modelos del mismo proveedor. Cada proveedor tiene:
- Su propio índice web
- Su propio pipeline de búsqueda y ranking
- Sus propios sesgos de citación

GPT-4o y GPT-4o-mini comparten el índice de Bing → los resultados de búsqueda serían prácticamente idénticos. Solo cambiaría la calidad de la generación, que no es lo que queremos medir aquí.

### 2.3. Por qué multi-motor

Un sitio puede ser visible en Gemini pero invisible en ChatGPT. Las razones son múltiples:

- **Índice diferente**: Google indexa distinto que Bing, que indexa distinto que los crawlers de DeepSeek.
- **Pipeline de búsqueda**: Cada proveedor pondera diferente PageRank, freshness, authority.
- **Sesgo de citación**: Cada LLM tiene preferencias diferentes sobre qué tipo de fuentes citar.
- **Acceso a robots.txt**: Algunos sitios bloquean GPTBot pero no GoogleBot.

La métrica [Engine Coverage](01_METRICAS_GEO.md#8-engine-coverage) (Chen et al. 2025) mide exactamente esta consistencia: ¿en cuántos motores somos visibles?

---

## 3. Sistema de tiers por presupuesto

### 3.1. Diseño de tiers

Con un presupuesto limitado (~$7/modelo para 9 semanas de evaluación), no todos los motores pueden ejecutar las 100 queries cada semana. El sistema de tiers asigna queries según el coste por motor:

| Tier | Modelos | Queries/semana | Composición | Total (9 sem) | Coste total |
|------|---------|---------------|-------------|---------------|-------------|
| **FULL** | Gemini, DeepSeek | 100 | CORE + R1 + R2 + R3 + R4 | 900 | ~$4.50 / ~$2.70 |
| **MEDIUM** | GPT-4o-mini | 60 | CORE + 2 bloques rotativos | ~540 | ~$6.48 |
| **LIGHT** | Haiku 4.5 | 40 | CORE + 1 bloque rotativo | ~360 | ~$7.92 |

### 3.2. Cobertura resultante

| Motor | Queries core (20) | Queries rotativas (80) | Frecuencia rotativas | Cobertura total |
|-------|-------------------|----------------------|---------------------|-----------------|
| Gemini | 9 evaluaciones/query | 9 evaluaciones/query | Todas cada semana | 100% semanal |
| DeepSeek | 9 evaluaciones/query | 9 evaluaciones/query | Todas cada semana | 100% semanal |
| GPT-4o-mini | 9 evaluaciones/query | ~4-5 evaluaciones/query | 2 bloques/semana | 60% semanal |
| Haiku 4.5 | 9 evaluaciones/query | ~2 evaluaciones/query | 1 bloque/semana | 40% semanal |

### 3.3. Coste total estimado

| Motor | Coste 9 semanas | Notas |
|-------|----------------|-------|
| Gemini | ~$4.50 | Cubierto por créditos gratuitos ($300 Google Cloud) |
| DeepSeek | ~$2.70 | Coste de API directo |
| GPT-4o-mini | ~$6.48 | Incluye $0.01/búsqueda |
| Haiku 4.5 | ~$7.92 | Incluye $0.01/búsqueda |
| **Total** | **~$21.60** | Sin contar Gemini (créditos gratuitos) |

---

## 4. Recolección SEO diaria

### 4.1. Pipeline actual

La recolección de métricas SEO funciona desde el 4 de febrero de 2026 mediante GitHub Actions:

- **Hora**: 08:00 UTC (todos los días)
- **Script**: `collect_metrics/collect_seo.py`
- **API**: Google PageSpeed Insights
- **Target**: `https://programamos.es/`
- **Output**: `data/seo/metrics_{timestamp}.json`

### 4.2. Métricas actuales

| Métrica | Fuente | Estrategia |
|---------|--------|-----------|
| Performance score | Lighthouse | Mobile + Desktop |
| SEO score | Lighthouse | Mobile + Desktop |
| Accessibility score | Lighthouse | Mobile + Desktop |
| LCP (Largest Contentful Paint) | Lighthouse | Mobile |
| TBT (Total Blocking Time) | Lighthouse | Mobile |

### 4.3. Métricas SEO adicionales propuestas

Para un análisis más completo de la relación SEO-GEO, se propone ampliar la recolección:

| Métrica | Herramienta | Estado | Relevancia GEO |
|---------|-------------|--------|----------------|
| Lighthouse scores | PageSpeed API | Implementado | Accesibilidad del contenido |
| Core Web Vitals (CLS, INP) | CrUX API | Propuesto | User experience que afecta indexación |
| Schema.org validación | Schema.org validator | Propuesto | Machine scannability directa |
| robots.txt / sitemap | Análisis propio | Propuesto | Acceso de crawlers de IA |
| Backlink profile | Ahrefs/Moz free tier | Propuesto | Authority signals |
| Indexación | Google Search Console | Propuesto | Si acceso disponible |
| Tráfico de bots IA | Logs servidor | Pendiente investigar | GPTBot, ClaudeBot, PerplexityBot |

**Schema.org y robots.txt** son especialmente relevantes para GEO: los datos estructurados facilitan que los motores de IA extraigan información, y la configuración de robots.txt determina qué crawlers pueden acceder al contenido.

---

## 5. Evaluación GEO Live semanal

### 5.1. Pipeline propuesto

- **Frecuencia**: Semanal (GitHub Actions)
- **Script**: `collect_metrics/collect_geo_live.py` (pendiente de implementar)
- **Motores**: 4 (Gemini, DeepSeek, GPT-4o-mini, Haiku)
- **Queries**: Según tier (40-100 por motor)

### 5.2. Schema de datos

Cada evaluación Live genera un registro con la siguiente estructura:

```json
{
  "run_id": "LIVE-2026-W12",
  "timestamp": "2026-03-15T09:00:00Z",
  "programamos_version": {
    "date": "2026-03-15",
    "content_hash": "sha256:abc123..."
  },
  "results": [
    {
      "query_id": "Q001",
      "query_text": "¿Qué proyectos existen para enseñar programación a niños en España?",
      "query_category": "informacional",
      "engines": {
        "gemini": {
          "is_visible": true,
          "som": 25.0,
          "first_citation_rank": 2,
          "brand_mentions": ["Programamos es una organización sin ánimo de lucro..."],
          "total_citations": 4,
          "target_citations": 1
        },
        "deepseek": {
          "is_visible": false,
          "som": 0.0,
          "first_citation_rank": null,
          "brand_mentions": [],
          "total_citations": 3,
          "target_citations": 0
        }
      }
    }
  ]
}
```

### 5.3. Diferencias con el experimental

| Aspecto | Experimental | Live |
|---------|-------------|------|
| **Retrieval** | FAISS local (coseno) | Búsqueda web real por motor |
| **Competidores** | Congelados | Los que el motor encuentre (cambian) |
| **Judge** | 1 modelo (Gemini 2.5 Flash) | 4 motores diferentes |
| **Control** | Total (variable aislada) | Parcial (entorno real) |
| **Propósito** | Medir efecto del contenido | Validar que mejoras son reales |
| **Frecuencia** | Por intervención | Semanal |
| **Coste/run** | ~$0.08 (40 queries × $0.002) | Variable por tier |

---

## 6. Validación cruzada

### 6.1. La pregunta clave

> Si optimizamos el contenido y el SoM mejora en el simulador experimental, ¿mejora también la visibilidad en los motores reales?

Esta es una **contribución clave del TFG**. La mayoría de papers de GEO usan solo un tipo de evaluación (simulada o real, pero no ambas). Nuestro diseño dual permite validar empíricamente que los resultados del simulador son representativos.

### 6.2. Método de validación

1. **Antes de una intervención**: Registrar métricas experimentales + Live como baseline.
2. **Después de la intervención**: Re-evaluar con ambos sistemas.
3. **Correlación**: Calcular correlación de Spearman entre:
   - $\Delta\text{SoM}_{\text{experimental}}$ (cambio en SoM simulado)
   - $\Delta\text{Visibilidad}_{\text{live}}$ (cambio en visibilidad real, promediado por motor)

### 6.3. Interpretación

| Resultado | Interpretación |
|-----------|---------------|
| Correlación alta ($\rho > 0.7$) | El simulador predice bien la realidad → validado |
| Correlación media ($0.3 < \rho < 0.7$) | El simulador captura tendencias pero no magnitudes |
| Correlación baja ($\rho < 0.3$) | El simulador no es representativo → revisar diseño |

Incluso una correlación media es un resultado publicable: demuestra que la optimización de contenido tiene efecto real, aunque la magnitud difiera del simulador.

---

## 7. SEO como covariable

### 7.1. No es variable independiente

En nuestro diseño, el SEO no es algo que manipulamos directamente (excepto en la Fase 1 con MARTE). Es una **covariable** que debemos monitorizar para detectar confounding.

### 7.2. Escenario de confounding

Supongamos que en la semana 5:
- Aplicamos optimización de contenido GEO → esperamos mejora en visibilidad
- Pero Google también re-indexa la página con mejor Lighthouse score
- La visibilidad Live mejora, pero ¿fue por el contenido GEO o por el mejor SEO?

La recolección diaria de métricas SEO permite **controlar por esta covariable**: si Lighthouse score no cambió significativamente, la mejora se atribuye al GEO.

### 7.3. SEO como prerequisito de GEO

```
¿El crawler de IA   ──NO──►  Invisible (problema SEO)
puede acceder?                   │
      │                          │  robots.txt, sitemap,
      SÍ                        │  server response time
      │                          │
      ▼                          │
¿La página está     ──NO──►  Invisible (problema SEO)
bien indexada?                   │
      │                          │  Schema.org, HTML semántico,
      SÍ                        │  Core Web Vitals
      │                          │
      ▼                          │
¿El contenido es    ──NO──►  Recuperado pero no citado
citado por el LLM?               │  (problema GEO)
      │                          │
      SÍ                        │  Estadísticas, citas,
      │                          │  párrafos auto-contenidos,
      ▼                          │  baja perplejidad
  VISIBLE
```

El SEO determina si el contenido **llega** al LLM. El GEO determina si el LLM lo **cita**. Ambos son necesarios; ninguno es suficiente por sí solo.

---

## 8. Cronograma semanal de recolección

```
Lunes a Domingo:
  08:00 UTC ─── collect_seo.py ─── PageSpeed API ─── data/seo/

Domingos (o día configurable):
  09:00 UTC ─── collect_geo_live.py ─── 4 motores ─── data/geo/live/
```

### Datos acumulados en 9 semanas

| Tipo | Frecuencia | Registros totales |
|------|-----------|-------------------|
| SEO (PageSpeed) | Diario | ~63 mediciones |
| GEO Live Gemini | Semanal × 100 queries | 900 evaluaciones |
| GEO Live DeepSeek | Semanal × 100 queries | 900 evaluaciones |
| GEO Live GPT-4o-mini | Semanal × 60 queries | ~540 evaluaciones |
| GEO Live Haiku | Semanal × 40 queries | ~360 evaluaciones |
| GEO Experimental | Por intervención × 40 queries | Variable (~200-400) |

---

*Anterior: [Arquitectura Experimental](02_EXPERIMENTAL.md) | Siguiente: [Estrategia de Mejora](04_ESTRATEGIA_MEJORA.md)*
