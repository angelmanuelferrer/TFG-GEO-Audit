# GEO-Audit: Midiendo y Mejorando la Visibilidad en Motores de IA

> **Informe técnico — Marzo 2026**
> Trabajo Fin de Grado | Caso de estudio: Programamos.es

---

## El problema

Imaginad que un profesor busca en ChatGPT: *"¿Qué proyectos existen para enseñar programación a niños en España?"*. La respuesta menciona Code.org, Scratch, la Hora del Código... pero Programamos no aparece. No es un problema de Google — en una búsqueda tradicional, Programamos sí aparece. Es un problema de visibilidad en motores de IA.

Los motores generativos (ChatGPT, Gemini, Perplexity, Claude) no funcionan como Google. No devuelven una lista de enlaces — generan una respuesta completa, citando selectivamente las fuentes que consideran más relevantes. Si tu contenido no es citado, no existes en la respuesta.

En nuestras primeras pruebas, identificamos un patrón revelador: Gemini SÍ menciona a Programamos cuando le preguntas específicamente por proyectos educativos en Andalucía (Q034), pero NO lo menciona en la pregunta general sobre España. El contenido existe y es accesible — el problema está en cómo está escrito y estructurado para ser "citable" por un LLM.

El **SEO** (Search Engine Optimization) mide la visibilidad en buscadores tradicionales. El **GEO** (Generative Engine Optimization) mide la visibilidad en respuestas de IA. Este TFG construye un sistema para medir, diagnosticar y mejorar la visibilidad GEO de Programamos.

---

## Qué medimos

Hemos definido 8 métricas que capturan diferentes dimensiones de la visibilidad en motores de IA:

| Métrica | Qué mide | Rango | Ejemplo |
|---------|----------|-------|---------|
| **Visibilidad** | ¿Aparecemos citados? | 0 o 1 | Programamos aparece en la respuesta → 1 |
| **Share of Model** | ¿Cuánto protagonismo? | 0–100% | 2 de 5 citas son nuestras → 40% |
| **Ranking** | ¿En qué posición? | 1–N | Primera fuente citada → 1 |
| **PAWC** | ¿Cuánto contenido + prominencia? | 0–∞ | 100 palabras en posición 1 → alto PAWC |
| **Coverage** | ¿Para qué tipos de queries? | 0–100% | Visibles en 8 de 10 queries informacionales → 80% |
| **Citation Rate** | ¿Nos citan cuando nos encuentran? | 0–100% | Recuperado 10 veces, citado 7 → 70% |
| **Sentiment** | ¿Cómo nos mencionan? | POS/NEU/NEG | "Excelente plataforma" → POSITIVO |
| **Engine Coverage** | ¿En cuántos motores? | 0–100% | Visibles en 3 de 4 motores → 75% |

Cada métrica está respaldada por literatura académica y tiene una implementación verificable en código.

> Detalle completo: [Catálogo de Métricas GEO](01_METRICAS_GEO.md)

---

## Cómo lo medimos

Usamos dos arquitecturas complementarias que operan en paralelo:

```
┌──────────────────────────┐     ┌──────────────────────────┐
│     EXPERIMENTAL         │     │         LIVE             │
│                          │     │                          │
│  RAG Simulator           │     │  4 motores reales        │
│  Gemini 2.5 Flash        │     │  con búsqueda web        │
│                          │     │                          │
│  Vectorstore FAISS       │     │  Gemini    (Google)      │
│  congelado               │     │  DeepSeek  (propio)      │
│                          │     │  GPT-4o-mini (Bing)      │
│  Solo cambia el          │     │  Haiku 4.5 (Anthropic)   │
│  contenido del target    │     │                          │
│                          │     │  Todo cambia:            │
│  ~$0.002/query           │     │  contenido, índice,      │
│                          │     │  competidores            │
│  Mide: CAUSALIDAD        │     │                          │
│  "¿El contenido nuevo    │     │  ~$21.60 total           │
│   es mejor?"             │     │  (9 semanas)             │
│                          │     │                          │
└──────────────────────────┘     │  Mide: REALIDAD          │
                                 │  "¿Los motores reales    │
                                 │   nos ven más?"          │
                                 │                          │
                                 └──────────────────────────┘
```

### Experimental: aislando el contenido

El simulador experimental es un RAG (Retrieval-Augmented Generation) controlado. Funciona así:

1. **Discovery** (una vez): Gemini 2.5 Flash con Google Search descubre los ~15 competidores reales de Programamos.
2. **Vectorstore congelado**: Los competidores se procesan y almacenan en FAISS. No se tocan más.
3. **Cada run**: Se descarga la web actual de Programamos, se trocea (256 tokens/64 overlap), se inserta en el vectorstore y se ejecutan 40 queries. Un agente Gemini 2.5 Flash simula ser un motor generativo y genera respuestas citando fuentes.

Lo que mide: si cambiamos el contenido y la visibilidad mejora, sabemos que fue por el contenido — todo lo demás está controlado.

**Coste**: ~$0.002/query (prácticamente gratis con créditos de Google Cloud).

> Detalle completo: [Arquitectura Experimental](02_EXPERIMENTAL.md)

### Live: validando con la realidad

Cuatro motores de IA reales con búsqueda web nativa evalúan las mismas queries semanalmente. Cada motor tiene su propio índice web y pipeline de búsqueda:

| Motor | Tier | Queries/semana | Coste 9 semanas |
|-------|------|---------------|-----------------|
| Gemini 2.5 Flash | FULL | 100 | ~$4.50 (créditos gratuitos) |
| DeepSeek V3.2 | FULL | 100 | ~$2.70 |
| GPT-4o-mini | MEDIUM | 60 | ~$6.48 |
| Haiku 4.5 | LIGHT | 40 | ~$7.92 |

**Total Live**: ~$21.60 para 9 semanas de evaluación continua.

Lo que mide: ¿las mejoras del simulador se traducen en mejoras reales? Si la correlación es alta, el simulador queda validado.

> Detalle completo: [Arquitectura Live](03_LIVE.md)

---

## Por qué funciona

Todos los motores generativos — ChatGPT, Gemini, Perplexity, Claude — usan RAG internamente. Cuando un usuario hace una pregunta:

1. **Retrieval**: El motor busca en la web y recupera documentos relevantes.
2. **Generation**: El LLM lee los documentos recuperados y decide qué citar.

Nuestro simulador experimental controla la etapa 1 (retrieval constante) y mide la etapa 2 (¿nos cita?). Si mejoramos el contenido y el LLM nos cita más en condiciones controladas, esa misma mejora debería trasladarse a motores reales — porque la etapa de generación funciona igual en ambos casos.

Esta no es solo una suposición teórica. SAGEO Arena (Wu et al. 2025) demuestra empíricamente que el rendimiento en simuladores RAG correlaciona con el rendimiento en motores reales. Y nuestro diseño dual (experimental + Live) permite verificar esta correlación específicamente para Programamos.

**Evidencia**: GEO-Bench (Aggarwal et al. 2023) demostró que la optimización de contenido puede mejorar la visibilidad en motores generativos hasta un +115%. Las técnicas más efectivas — inclusión de estadísticas (+55-85%), citas a fuentes autoritativas (+30-40%), escritura clara (+20-35%) — son las que implementamos en nuestra estrategia de mejora.

> Detalle completo: [Base de Evidencia](05_EVIDENCIA.md)

---

## Cómo mejorar

La estrategia de mejora opera en dos frentes secuenciales:

### Fase 1 — SEO con MARTE

MARTE (herramienta del director del TFG) reconstruye la web de Programamos con HTML optimizado, responsive y con buen rendimiento. Esto establece los cimientos técnicos: sin buena estructura HTML y buen rendimiento, las optimizaciones de contenido GEO tienen menor impacto.

### Fase 2 — GEO puro

Cinco vectores de optimización respaldados por la literatura:

| Vector | Concepto | Paper | Mejora esperada |
|--------|----------|-------|-----------------|
| **Machine Scannability** | HTML semántico, Schema.org, headers claros | Chen 2025 | Significativa |
| **Citation Readiness** | Estadísticas, párrafos auto-contenidos, datos | Aggarwal 2023 | +55-85% |
| **Low Perplexity** | Escritura clara SVO, definiciones explícitas | Lijia 2025 | +20-35% |
| **Authority Signals** | Referencias a instituciones, datos oficiales | Chen & Wu 2025 | +30-40% |
| **Bot Accessibility** | robots.txt, sitemap, tiempos de respuesta | Chen 2025 | Prerequisito |

El protocolo es secuencial: baseline → MARTE → Machine Scannability → Citation Readiness → Low Perplexity + Authority. Cada fase incluye 3 runs experimentales y 1 semana de Live para medir el impacto incremental.

> Detalle completo: [Estrategia de Mejora](04_ESTRATEGIA_MEJORA.md)

---

## Visión

GEO-Audit está diseñado como un sistema modular que puede evolucionar de herramienta de investigación a plataforma operativa:

**Ahora** (TFG): Sistema de medición + diagnóstico para un caso de estudio (Programamos). Pipeline experimental controlado + validación Live multi-motor. Intervenciones manuales guiadas por métricas.

**Futuro** (extensión): Plataforma unificada que mide, diagnostica y genera mejoras automáticamente. La arquitectura modular (`src/`) ya está diseñada para esto:
- `src/processing/` → procesamiento de cualquier web
- `src/rag/` → simulación RAG generalizable
- `src/metrics/` → framework de métricas extensible
- `src/generation/` → generador de páginas optimizadas (Mode A + Mode B)

El caso Programamos demuestra la viabilidad. La arquitectura permite escalar a cualquier sitio web que quiera medir y mejorar su visibilidad en la nueva era de búsqueda generativa.

---

## Navegación del informe

| Documento | Contenido | Lectura |
|-----------|-----------|---------|
| [01 — Métricas GEO](01_METRICAS_GEO.md) | Catálogo completo de las 8 métricas con fórmulas y papers | ~10 min |
| [02 — Experimental](02_EXPERIMENTAL.md) | Arquitectura del simulador RAG controlado | ~12 min |
| [03 — Live](03_LIVE.md) | Evaluación multi-motor con búsqueda web real | ~12 min |
| [04 — Estrategia](04_ESTRATEGIA_MEJORA.md) | SEO (MARTE) + 5 vectores de optimización GEO | ~10 min |
| [05 — Evidencia](05_EVIDENCIA.md) | Base de 10+ papers con tabla resumen | ~12 min |
