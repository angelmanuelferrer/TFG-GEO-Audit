# Base de Evidencia Académica

> **Versión**: 1.0 | **Última actualización**: Marzo 2026
> Este documento recopila la evidencia académica que fundamenta el diseño de GEO-Audit: métricas, arquitecturas y estrategias de optimización.

---

## 1. Fundamentación GEO

### 1.1. Aggarwal et al. (2023) — *GEO: Generative Engine Optimization*

**Contribución**: Paper fundacional que define el campo GEO. Introduce el framework GEO-Bench para evaluar la visibilidad de sitios web en motores generativos.

**Hallazgos clave**:
- La optimización de contenido puede mejorar la visibilidad en motores generativos hasta un **+115%**.
- Las técnicas más efectivas son: inclusión de estadísticas (+55-85%), citas a fuentes autoritativas (+30-40%), y fluency optimization (+15-25%).
- Las métricas propuestas (Visibilidad, PAWC, Subjective Impression) capturan diferentes dimensiones de la presencia en respuestas generativas.

**Cómo lo usamos**: Framework de métricas base. Nuestras métricas de Visibilidad, Share of Model y PAWC derivan directamente de este paper. La metodología de GEO-Bench (simulador RAG controlado) inspira nuestro modo experimental.

**Métricas/Técnicas adoptadas**: Visibilidad, PAWC, Subjective Impression (→ SoM), Citation Readiness como vector de optimización.

### 1.2. Makrydakis (2025) — *Generative Engine Optimization: A Survey*

**Contribución**: Revisión sistemática del campo GEO. Sintetiza métricas, técnicas y frameworks de múltiples papers en una taxonomía unificada.

**Hallazgos clave**:
- Clasifica las optimizaciones GEO en: content-level (estadísticas, citas, perplexity), structural (HTML semántico, Schema.org) y authority-level (backlinks, referencias externas).
- Identifica que Share of Voice / Share of Model es la métrica más adoptada en la literatura.
- Recomienda evaluación multi-motor para resultados representativos.

**Cómo lo usamos**: Taxonomía de referencia para organizar las métricas y técnicas de optimización. Confirma que nuestra selección de 8 métricas cubre las dimensiones principales identificadas en la literatura.

---

## 2. Cómo funcionan los motores generativos

### 2.1. Wu et al. (2025) — *SAGEO Arena: A Benchmark for Generative Engine Optimization*

**Contribución**: Benchmark controlado que evalúa cómo diferentes configuraciones de RAG afectan a la visibilidad. Introduce Citation Rate como métrica que aísla la etapa de generación.

**Hallazgos clave**:
- **Separación retrieval vs generation**: Las dos etapas de un motor generativo son independientes. Mejorar el contenido para la etapa de generación tiene efecto independiente de la calidad del retrieval.
- **Citation Rate**: Proporción de veces que un documento es citado cuando es recuperado. Más informativa que Visibilidad porque controla por retrieval.
- **Chunking 256/64**: Configuración de referencia utilizada en el benchmark.
- **Validación empírica**: Demuestra correlación entre rendimiento en simuladores RAG y motores generativos reales.

**Cómo lo usamos**: Alineación directa:
- Chunking 256/64 (ADR-011)
- Citation Rate como métrica
- Argumento teórico de que mejoras en RAG simulado predicen mejoras en motores reales
- Separación de discovery (una vez) y experimental (N veces)

**Métricas/Técnicas adoptadas**: Citation Rate, configuración de chunking, framework de evaluación controlada.

### 2.2. Tan et al. (2024) — *HtmlRAG: HTML is Better Than Plain Text for RAG*

**Contribución**: Demuestra que preservar la estructura HTML en el procesamiento RAG mejora significativamente la calidad de las respuestas frente a convertir a texto plano.

**Hallazgos clave**:
- La estructura HTML (headings, listas, tablas) proporciona señales semánticas que el texto plano pierde.
- Los LLMs aprovechan los tags HTML para entender la jerarquía y relevancia del contenido.
- La limpieza selectiva de HTML (eliminar scripts, estilos, pero preservar estructura) es óptima frente a la conversión total a texto.

**Cómo lo usamos**: Justifica nuestro procesamiento HTML-aware (ADR-007). Antes de chunking, eliminamos elementos no-contenido pero preservamos la estructura semántica. También informa la estrategia de Machine Scannability en la [optimización GEO](04_ESTRATEGIA_MEJORA.md).

**Técnica adoptada**: HTML-aware chunking con preservación de estructura semántica.

---

## 3. Factores de citación

### 3.1. Chen et al. (2025) — *SEO vs. GEO: A Multi-Engine Study*

**Contribución**: Estudio comparativo extenso entre SEO tradicional y GEO. Analiza qué factores influyen en la citación por parte de motores generativos con búsqueda web.

**Hallazgos clave**:
- **Machine Scannability**: HTML5 semántico, headers jerárquicos (H1-H6), Schema.org JSON-LD son los factores estructurales más influyentes.
- **Authority signals**: Los LLMs prefieren citar fuentes con backlinks de dominios autoritativos (Wikipedia, papers académicos, sitios .edu/.gov).
- **Coverage por categoría**: La visibilidad varía enormemente entre queries informacionales (más fácil) y comparativas (más difícil).
- **Engine Coverage**: La visibilidad varía significativamente entre motores — evaluar en al menos 3 para resultados representativos.

**Cómo lo usamos**: Define dos de nuestros vectores de optimización (Machine Scannability, Authority Signals) y dos métricas (Coverage, Engine Coverage). Justifica la evaluación multi-motor en el Live.

**Métricas/Técnicas adoptadas**: Coverage, Engine Coverage, Machine Scannability, Authority Signals.

### 3.2. Lijia et al. (2025) — *Low Perplexity and GEO*

**Contribución**: Estudia el impacto de la perplejidad del texto (predictibilidad lingüística) en la probabilidad de citación por LLMs.

**Hallazgos clave**:
- Los textos con **baja perplejidad** (escritura clara, predecible, con estructura SVO) tienen mayor probabilidad de ser citados.
- Definiciones explícitas al inicio de párrafos ("topic sentences") aumentan la citabilidad.
- El lenguaje técnico excesivo o las estructuras sintácticas complejas reducen la probabilidad de citación.

**Cómo lo usamos**: Define el vector de optimización "Low Perplexity" en nuestra estrategia de mejora. Informa cómo reescribir contenido para máxima citabilidad.

**Técnica adoptada**: Low Perplexity como vector de optimización (escritura clara SVO, definiciones explícitas).

### 3.3. Chen & Wu (2025) — *Authority and Citation in Generative Engines*

**Contribución**: Analiza cómo las señales de autoridad influyen en las decisiones de citación de los LLMs.

**Hallazgos clave**:
- Los LLMs muestran **sesgo de autoridad**: prefieren citar fuentes reconocidas (Wikipedia, instituciones académicas) sobre fuentes desconocidas.
- Los backlinks de dominios autoritativos actúan como señal indirecta — los LLMs no ven los backlinks directamente, pero el retrieval (búsqueda web) los pondera.
- Las referencias a fuentes terceras en el propio contenido ("según un estudio de la Universidad X...") aumentan la percepción de autoridad.

**Cómo lo usamos**: Informa la estrategia de Authority Signals. Programamos puede incluir referencias a estudios educativos, colaboraciones con universidades, y datos del INTEF para aumentar su percepción de autoridad.

---

## 4. Métricas y marcos de evaluación

### 4.1. Lüttgenau et al. (2025) — *Generative Search Engine Optimization*

**Contribución**: Framework práctico para optimizar sitios web para motores de búsqueda generativos. Introduce métricas posicionales.

**Hallazgos clave**:
- La **posición de la primera cita** tiene impacto significativo en la percepción del usuario — las primeras citas reciben más atención.
- PAWC (Position-Adjusted Word Count) es más informativa que el simple recuento de citas porque penaliza citas tardías.
- Los sitios con buena estructura (headers claros, párrafos cortos) tienden a ser citados antes.

**Cómo lo usamos**: Adoptamos Ranking (primera posición de cita) y PAWC como métricas core. Su análisis de posición refuerza la importancia de estructura clara.

**Métricas adoptadas**: Ranking, PAWC.

### 4.2. Krugmann & Hartmann (2024) — *Sentiment Bias in AI Responses*

**Contribución**: Estudia cómo los LLMs introducen sesgos de sentimiento en sus respuestas sobre marcas y productos.

**Hallazgos clave**:
- Los LLMs pueden introducir sentimiento positivo o negativo que no está presente en las fuentes originales.
- El sentimiento en las respuestas de IA influye significativamente en la percepción de las marcas por parte de los usuarios.
- Recomienda monitorizar el tono como parte del framework de visibilidad.

**Cómo lo usamos**: Justifica incluir Sentiment como métrica. Un sitio puede tener alta Visibilidad pero sentimiento negativo, lo cual es contraproducente. Nuestro análisis de sentimiento (Ollama local) clasifica cada mención del target.

**Métrica adoptada**: Sentiment (POSITIVO / NEUTRO / NEGATIVO).

---

## 5. Diseño experimental

### 5.1. SAGEO Arena — Alignment de parámetros

Nuestro diseño experimental se alinea con SAGEO Arena (Wu et al. 2025) en múltiples dimensiones:

| Parámetro | SAGEO Arena | GEO-Audit | Alineado |
|-----------|-------------|-----------|----------|
| Chunking tokens | 256 | 256 | Si |
| Overlap tokens | 64 | 64 | Si |
| Retrieval | Coseno + vectorstore | Coseno + FAISS | Si |
| Judge mode | Agent con search tool | Agent con FAISS tool | Si |
| Métricas | Citation Rate, Visibility | Citation Rate, Visibilidad, +6 más | Superset |
| Control de variables | Retrieval congelado | Vectorstore congelado | Si |

Esta alineación permite comparar nuestros resultados con los del benchmark SAGEO Arena, aumentando la validez externa del estudio.

### 5.2. Validez de simuladores RAG

Múltiples papers soportan la validez de usar simuladores RAG para evaluar GEO:

- **Aggarwal et al. (2023)**: GEO-Bench usa un simulador RAG y demuestra que las optimizaciones mejoran la visibilidad real.
- **Wu et al. (2025)**: SAGEO Arena valida correlación entre rendimiento en simulador y motores reales.
- **Argumento teórico**: Todos los motores generativos usan RAG internamente (retrieval + generation). Si el contenido funciona bien en la etapa de generación (medida por simulador), funcionará en motores reales donde esa misma etapa ocurre.

Nuestro TFG contribuye validación empírica adicional mediante la correlación experimental-Live.

---

## 6. Optimización de contenido

### 6.1. Técnicas con evidencia empírica

| Técnica | Paper | Mejora reportada | Adoptada en GEO-Audit |
|---------|-------|------------------|-----------------------|
| Inclusión de estadísticas | Aggarwal 2023 | +55-85% visibilidad | Si (Citation Readiness) |
| Citas a fuentes autoritativas | Aggarwal 2023 | +30-40% visibilidad | Si (Authority Signals) |
| HTML5 semántico + Schema.org | Chen 2025 | Significativa (no cuantificada) | Si (Machine Scannability) |
| Headers jerárquicos H1-H6 | Chen 2025, Tan 2024 | Significativa | Si (Machine Scannability) |
| Baja perplejidad lingüística | Lijia 2025 | +20-35% citabilidad | Si (Low Perplexity) |
| Topic sentences explícitas | Lijia 2025 | +15-25% citabilidad | Si (Low Perplexity) |
| Párrafos auto-contenidos | Aggarwal 2023 | +25% citabilidad | Si (Citation Readiness) |
| robots.txt limpio para bots IA | Chen 2025 | Prerequisito | Si (Bot Accessibility) |

### 6.2. Técnicas sin evidencia suficiente (descartadas o pendientes)

| Técnica | Razón de exclusión |
|---------|-------------------|
| Keyword stuffing | Contraproducente en GEO (aumenta perplejidad) |
| Link building masivo | SEO clásico, no directamente GEO |
| Contenido generado por IA sin revisión | Puede reducir authority signals |
| Social media signals | No hay evidencia de impacto en citación por LLMs |

---

## 7. Tabla resumen de evidencia

| # | Paper | Año | Contribución principal | Cómo lo usamos | Métrica/Técnica adoptada |
|---|-------|-----|----------------------|----------------|--------------------------|
| 1 | Aggarwal et al. — *GEO: Generative Engine Optimization* | 2023 | Framework fundacional GEO, +115% visibilidad | Métricas base, metodología | Visibilidad, SoM, PAWC, Citation Readiness |
| 2 | Wu et al. — *SAGEO Arena* | 2025 | Benchmark GEO, separación retrieval/generation | Chunking 256/64, Citation Rate, validación | Citation Rate, parámetros de chunking |
| 3 | Chen et al. — *SEO vs. GEO* | 2025 | Estudio multi-motor SEO vs GEO | Factores de citación, métricas cross-engine | Coverage, Engine Coverage, Machine Scannability |
| 4 | Lüttgenau et al. — *Generative Search Engine Optimization* | 2025 | Métricas posicionales de citación | Ranking y PAWC como métricas core | Ranking, PAWC |
| 5 | Makrydakis — *GEO Survey* | 2025 | Taxonomía del campo GEO | Organización de métricas y técnicas | Taxonomía de métricas |
| 6 | Tan et al. — *HtmlRAG* | 2024 | HTML > texto plano para RAG | Procesamiento HTML-aware | HTML-aware chunking |
| 7 | Lijia et al. — *Low Perplexity and GEO* | 2025 | Perplejidad baja → mayor citabilidad | Vector de optimización Low Perplexity | Low Perplexity, topic sentences |
| 8 | Chen & Wu — *Authority and Citation* | 2025 | Señales de autoridad en citación | Vector Authority Signals | Authority Signals |
| 9 | Krugmann & Hartmann — *Sentiment Bias in AI* | 2024 | Sesgo de sentimiento en respuestas LLM | Métrica Sentiment | Sentiment (POS/NEU/NEG) |
| 10 | HtmlRAG — Tan et al. | 2024 | Preservar HTML mejora RAG | Chunking HTML-aware (ADR-007) | Procesamiento HTML-aware |

---

## 8. Mapa de evidencia por componente del sistema

### 8.1. Métricas

| Métrica | Papers que la definen/usan |
|---------|---------------------------|
| Visibilidad | Aggarwal 2023, Chen 2025, Makrydakis 2025 |
| Share of Model | Aggarwal 2023, Chen 2025, Makrydakis 2025 |
| Ranking | Lüttgenau 2025, Chen 2025 |
| PAWC | Aggarwal 2023, Lüttgenau 2025 |
| Coverage | Chen 2025 |
| Citation Rate | Wu 2025 |
| Sentiment | Krugmann & Hartmann 2024 |
| Engine Coverage | Chen 2025 |

### 8.2. Arquitectura

| Decisión de diseño | Evidencia |
|--------------------|-----------|
| Simulador RAG controlado | Aggarwal 2023 (GEO-Bench), Wu 2025 (SAGEO Arena) |
| Chunking 256/64 | Wu 2025 (SAGEO Arena), ADR-011 |
| HTML-aware processing | Tan 2024 (HtmlRAG), ADR-007 |
| Agent mode para judge | Wu 2025 (SAGEO: agent más realista), ADR-012 |
| Multi-motor en Live | Chen 2025 (Engine Coverage), Makrydakis 2025 |
| Embeddings locales | Reproducibilidad (estándar científico), ADR-003 |

### 8.3. Estrategia de optimización

| Vector de optimización | Evidencia |
|-----------------------|-----------|
| Machine Scannability | Chen 2025, Tan 2024 |
| Citation Readiness | Aggarwal 2023 |
| Low Perplexity | Lijia 2025 |
| Authority Signals | Chen & Wu 2025, Aggarwal 2023 |
| Bot Accessibility | Chen 2025 (prerequisito SEO) |

---

## 9. Gaps en la literatura

| Gap identificado | Impacto en GEO-Audit | Oportunidad |
|------------------|----------------------|-------------|
| Pocos estudios en español | Nuestros resultados pueden no alinearse con papers en inglés | Contribución original: GEO en español |
| Validación dual (simulado + real) escasa | Nuestra correlación experimental-Live es novedosa | Contribución metodológica |
| Sector educativo poco estudiado | No hay benchmarks GEO para ONGs educativas | Contribución sectorial |
| Evolución temporal poco medida | Mayoría de papers son cross-sectional | Nuestras 9 semanas de datos longitudinales |

Estos gaps representan oportunidades de contribución original del TFG al campo de GEO.

---

*Este documento se actualiza conforme se incorporan nuevos papers. Última revisión: Marzo 2026.*

*Volver a: [Resumen Ejecutivo](00_RESUMEN.md)*
