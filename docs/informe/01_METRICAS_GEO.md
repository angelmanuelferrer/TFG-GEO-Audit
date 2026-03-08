# Catálogo de Métricas GEO

> **Versión**: 1.0 | **Última actualización**: Marzo 2026
> Este documento define las 8 métricas que utiliza GEO-Audit para medir la visibilidad de un sitio web en respuestas generadas por IA.

---

## Tabla resumen

| # | Métrica | Tipo | Rango | Paper principal |
|---|---------|------|-------|-----------------|
| 1 | [Visibilidad](#1-visibilidad) | Binaria | {0, 1} | Aggarwal et al. 2023 |
| 2 | [Share of Model (SoM)](#2-share-of-model-som) | Proporción | 0–100% | Aggarwal 2023, Chen 2025 |
| 3 | [Ranking](#3-ranking) | Ordinal | 1–N (menor = mejor) | Lüttgenau 2025, Chen 2025 |
| 4 | [PAWC](#4-pawc-position-adjusted-word-count) | Ponderada | 0–∞ (mayor = mejor) | Aggarwal 2023, Lüttgenau 2025 |
| 5 | [Coverage](#5-coverage) | Proporción | 0–100% | Chen et al. 2025 |
| 6 | [Citation Rate](#6-citation-rate) | Proporción | 0–100% | Wu et al. 2025 |
| 7 | [Sentiment](#7-sentiment) | Categórica | POS / NEU / NEG | Krugmann & Hartmann 2024 |
| 8 | [Engine Coverage](#8-engine-coverage) | Proporción | 0–100% | Chen et al. 2025 |

---

## 1. Visibilidad

### Definición

Indica si el sitio objetivo aparece citado (con URL o mención de marca) en la respuesta generada por el motor de IA para una query determinada. Es la métrica más básica: ¿estamos o no estamos?

### Fórmula

$$V(q) = \begin{cases} 1 & \text{si el sitio aparece citado en la respuesta a } q \\ 0 & \text{en caso contrario} \end{cases}$$

### Rango e interpretación

- **1**: El sitio es visible para esa query. El motor de IA consideró el contenido relevante y lo citó.
- **0**: El sitio no aparece. Puede significar que no fue recuperado (problema de retrieval/SEO) o que fue recuperado pero no citado (problema de calidad de contenido/GEO).

### Papers de referencia

- **Aggarwal et al. (2023)** — *GEO: Generative Engine Optimization*: Define "source-level visibility" como la base del framework GEO. Un sitio es visible si aparece en las citas del motor generativo.
- **Chen et al. (2025)** — *SEO vs. GEO*: Usa visibilidad binaria como métrica primaria en su estudio comparativo.
- **Makrydakis (2025)** — *GEO Survey*: Recoge la visibilidad como métrica fundacional en su taxonomía.

### Implementación

```python
# src/rag/citation_extractor.py — CitationExtractor.extract_metrics()
target_citations = self._count_target_citations(citations)
is_visible = target_citations > 0
```

La detección de si una cita pertenece al sitio objetivo usa normalización de URLs (elimina esquema, `www.`, barra final) y validación de sufijos para prevenir falsos positivos como `programamos.es.evil.com`.

---

## 2. Share of Model (SoM)

### Definición

Proporción de citas que corresponden al sitio objetivo sobre el total de citas en la respuesta. Es el análogo GEO del "Share of Voice" en marketing digital. Mide no solo si aparecemos, sino cuánto protagonismo tenemos frente a competidores.

### Fórmula

$$\text{SoM}(q) = \frac{\text{citas del objetivo}}{\text{total de citas}} \times 100$$

Donde cada cita es una referencia numerada `[1]`, `[2]`, etc., con URL de origen en la respuesta del motor generativo.

### Rango e interpretación

- **0%**: No citado (equivale a Visibilidad = 0).
- **1–25%**: Presencia marginal. Aparecemos pero otros dominan.
- **25–50%**: Presencia significativa. Somos una fuente relevante.
- **50–100%**: Dominamos la respuesta. El motor nos considera la fuente principal.

### Papers de referencia

- **Aggarwal et al. (2023)**: Introduce "Subjective Impression" como proporción de contenido atribuible a una fuente, de donde deriva SoM.
- **Chen et al. (2025)**: Usa "Brand Visibility Score" como porcentaje de menciones, esencialmente la misma métrica.
- **Makrydakis (2025)**: Recoge SoM como métrica clave en su revisión sistemática.

### Implementación

```python
# src/rag/citation_extractor.py — CitationExtractor.extract_metrics()
total = len(citations)
target = self._count_target_citations(citations)
som = (target / total * 100) if total > 0 else 0.0
```

---

## 3. Ranking

### Definición

Posición de la primera cita del sitio objetivo en la lista ordenada de citas de la respuesta. Mide la prominencia: no es lo mismo ser la primera fuente citada (posición 1) que aparecer como la quinta (posición 5). Las citas tempranas tienen más impacto en la percepción del usuario.

### Fórmula

$$\text{Ranking}(q) = \min\{i : \text{cita}_i \in \text{objetivo}\}$$

Donde $i$ es la posición 1-indexed de la cita en la respuesta. Si el objetivo no aparece, Ranking = `null` (no aplicable).

### Rango e interpretación

- **1**: Primera fuente citada. Máxima prominencia.
- **2–3**: Presencia temprana, buena visibilidad.
- **4+**: Aparece pero en posición secundaria.
- **null**: No citado.

### Papers de referencia

- **Lüttgenau et al. (2025)** — *Generative Search Engine Optimization*: Analiza el impacto de la posición de citación en la percepción del usuario, demostrando que citas tempranas reciben más atención.
- **Chen et al. (2025)**: Usa "First Mention Position" como métrica de prominencia.

### Implementación

```python
# src/rag/citation_extractor.py — CitationExtractor._find_first_citation_rank()
for i, citation in enumerate(citations, 1):
    url = citation.get("url", "")
    if self._url_matches_target(url):
        return i
return None
```

---

## 4. PAWC (Position-Adjusted Word Count)

### Definición

Recuento de palabras atribuidas al sitio objetivo, ponderado por la posición de cada cita usando un factor de descuento logarítmico. Las palabras asociadas a citas tempranas valen más que las asociadas a citas tardías. Combina cantidad de contenido citado con prominencia posicional.

### Fórmula

$$\text{PAWC}(q) = \sum_{i \in \text{citas del objetivo}} \frac{w_i}{\log_2(i + 1)}$$

Donde:
- $w_i$ = número de palabras en el texto asociado a la cita $i$
- $i$ = posición de la cita (1-indexed)
- $\log_2(i + 1)$ = factor de descuento (cita 1 → divisor 1.0, cita 2 → 1.58, cita 3 → 2.0, cita 4 → 2.32...)

### Rango e interpretación

- **0**: No citado.
- **1–50**: Presencia breve (una mención corta).
- **50–200**: Presencia moderada.
- **200+**: Presencia sustancial con contenido extenso en posiciones prominentes.

PAWC penaliza aparecer solo al final con poco texto y recompensa aparecer pronto con contenido extenso.

### Papers de referencia

- **Aggarwal et al. (2023)**: Propone PAWC como métrica principal en GEO-Bench, argumentando que captura tanto la cantidad como la posición de las citas.
- **Lüttgenau et al. (2025)**: Adopta PAWC como una de las métricas core en su framework de evaluación.

### Implementación

PAWC se calcula a nivel de pipeline (no en `CitationExtractor` directamente) combinando los datos de `first_citation_rank` con el recuento de palabras de las citas del objetivo. El cálculo utiliza los campos `quote` de cada cita que matchea el target.

---

## 5. Coverage

### Definición

Porcentaje de queries en una categoría para las que el sitio objetivo es visible. Mide la amplitud de presencia: ¿aparecemos solo para queries informacionales o también para comparativas y navegacionales?

### Fórmula

$$\text{Coverage}(c) = \frac{|\{q \in c : V(q) = 1\}|}{|c|} \times 100$$

Donde $c$ es una categoría de queries (informacional, comparativa, navegacional).

### Rango e interpretación

- **0%**: No aparecemos para ninguna query de esa categoría.
- **1–33%**: Cobertura baja. Solo somos visibles para casos muy específicos.
- **34–66%**: Cobertura media. Presencia parcial.
- **67–100%**: Cobertura alta. Somos referencia habitual para esa categoría.

### Distribución de queries en GEO-Audit

| Categoría | Queries totales | Core | Rotativas |
|-----------|----------------|------|-----------|
| Informacional | 35 | 7 | 28 |
| Comparativa | 35 | 7 | 28 |
| Navegacional | 30 | 6 | 24 |
| **Total** | **100** | **20** | **80** |

### Papers de referencia

- **Chen et al. (2025)**: Analiza Coverage por tipo de query, demostrando que la visibilidad varía enormemente entre categorías. Los sitios suelen tener mejor cobertura en queries informacionales que comparativas.

### Implementación

Coverage se calcula agregando las métricas de Visibilidad por categoría, usando los metadatos de `config/queries.json` que etiquetan cada query con su categoría (`informacional`, `comparativa`, `navegacional`).

---

## 6. Citation Rate

### Definición

Proporción de veces que el sitio objetivo es citado respecto a las veces que fue recuperado (incluido en los chunks que el LLM recibe). Mide la calidad de conversión: de todas las veces que el motor tuvo acceso a nuestro contenido, ¿cuántas veces lo consideró digno de citar?

### Fórmula

$$\text{CR}(q) = \frac{\text{veces citado}}{\text{veces recuperado}} \times 100$$

En modo agent del RAG Simulator, "recuperado" significa que el agente buscó y obtuvo chunks del sitio objetivo entre sus resultados.

### Rango e interpretación

- **0%**: Recuperado pero nunca citado. El contenido está accesible pero no es lo suficientemente relevante/claro para que el LLM lo cite.
- **1–50%**: Citado a veces. Hay potencial de mejora en calidad de contenido.
- **50–100%**: Citado frecuentemente. El contenido es atractivo para el LLM.

### Papers de referencia

- **Wu et al. (2025)** — *SAGEO Arena*: Introduce Citation Rate como métrica que aísla la etapa de generación. Argumenta que es más informativa que Visibilidad porque controla por retrieval: si un sitio no es citado, Citation Rate distingue entre "no fue encontrado" y "fue encontrado pero descartado".

### Implementación

Citation Rate requiere datos de retrieval (qué chunks fueron recuperados) además de citación. En modo agent, el RAG Judge reporta `sources_available_but_unused` en su JSON de salida, lo que permite calcular:
- Recuperado = `sources_used` + `sources_available_but_unused`
- Citado = entradas en `citations` que matchean el target

---

## 7. Sentiment

### Definición

Tono con el que el motor de IA menciona o describe al sitio objetivo en su respuesta. Un sitio puede ser visible pero mencionado negativamente ("tiene limitaciones" o "su interfaz es confusa"), lo cual es contraproducente.

### Fórmula

$$\text{Sentiment}(q) \in \{\text{POSITIVO}, \text{NEUTRO}, \text{NEGATIVO}\}$$

Clasificación categórica del fragmento de respuesta que menciona al objetivo. Se aplica un modelo de análisis de sentimiento sobre el contexto textual de cada mención.

### Rango e interpretación

- **POSITIVO**: El motor recomienda o habla favorablemente del sitio ("una excelente plataforma", "destaca por su comunidad").
- **NEUTRO**: Mención factual sin valoración ("Programamos es una organización sin ánimo de lucro que...").
- **NEGATIVO**: Mención con crítica o limitación ("sin embargo, su interfaz podría mejorar").

### Papers de referencia

- **Krugmann & Hartmann (2024)** — *Sentiment Bias in AI*: Demuestran que los LLMs pueden introducir sesgos de sentimiento en sus respuestas, afectando la percepción de las marcas. Recomiendan monitorizar el tono como parte del framework de visibilidad.

### Implementación

Configurado en `src/prompts/registry.py` (prompt `sentiment_analyzer`, v0.1.0). Modelo: Ollama local (clasificación simple que no requiere modelos de pago). Clasificación ternaria: POSITIVO / NEUTRO / NEGATIVO.

---

## 8. Engine Coverage

### Definición

Proporción de motores generativos (proveedores) que citan al sitio objetivo para una query dada. Mide la consistencia de visibilidad a través de diferentes motores. Un sitio puede ser visible en Gemini pero invisible en ChatGPT porque cada proveedor tiene su propio índice web y pipeline de búsqueda.

### Fórmula

$$\text{EC}(q) = \frac{|\{e : V_e(q) = 1\}|}{|E|} \times 100$$

Donde $E$ es el conjunto de motores evaluados y $V_e(q)$ es la visibilidad en el motor $e$ para la query $q$.

### Rango e interpretación (con 4 motores)

- **0%** (0/4): Invisible en todos los motores.
- **25%** (1/4): Solo un motor nos cita. Dependencia de un proveedor.
- **50%** (2/4): Presencia parcial.
- **75%** (3/4): Buena cobertura multi-motor.
- **100%** (4/4): Visibilidad universal.

### Motores evaluados en GEO-Audit (Live)

| Motor | Proveedor | Búsqueda web |
|-------|-----------|-------------|
| Gemini 2.5 Flash | Google | Google Search |
| DeepSeek V3.2 | DeepSeek | Propio |
| GPT-4o-mini | OpenAI | Bing |
| Claude Haiku 4.5 | Anthropic | Propio |

La diversidad de proveedores maximiza la representatividad: 4 índices web distintos, 4 pipelines de búsqueda, 4 sesgos de citación diferentes.

### Papers de referencia

- **Chen et al. (2025)**: Introduce "Engine Coverage" como métrica cross-engine, demostrando que la visibilidad varía significativamente entre motores. Recomienda evaluar en al menos 3 motores para obtener resultados representativos.

### Implementación

Engine Coverage se calcula en la evaluación Live (`collect_metrics/collect_geo_live.py`), agregando los resultados de Visibilidad por motor para cada query.

---

## Tabla comparativa de nomenclatura entre papers

Cada paper usa nombres diferentes para métricas equivalentes. Esta tabla mapea la terminología:

| Métrica GEO-Audit | Aggarwal 2023 | Chen 2025 | Wu 2025 (SAGEO) | Lüttgenau 2025 | Makrydakis 2025 |
|-------------------|---------------|-----------|------------------|-----------------|-----------------|
| Visibilidad | Source-level Visibility | Brand Presence | Visibility | Source Visibility | Visibility |
| Share of Model | Subjective Impression | Brand Visibility Score | Source Share | Citation Share | Share of Voice |
| Ranking | — | First Mention Position | — | Citation Position | — |
| PAWC | Position-Adj. Word Count | — | — | PAWC | Weighted Impression |
| Coverage | — | Category Coverage | — | — | Topic Coverage |
| Citation Rate | — | — | Citation Rate | — | — |
| Sentiment | — | — | — | — | Sentiment Score |
| Engine Coverage | — | Engine Coverage | — | — | Cross-Engine Visibility |

**Nota**: Un guion (—) indica que el paper no define explícitamente esa métrica, aunque pueda mencionarla indirectamente.

---

## Relación entre métricas

Las métricas forman una jerarquía:

```
Visibilidad (¿estamos?)
  └── Ranking (¿dónde estamos?)
  └── Share of Model (¿cuánto protagonismo?)
       └── PAWC (¿cuánto contenido, ponderado por posición?)
  └── Sentiment (¿cómo nos mencionan?)

Coverage = agregación de Visibilidad por categoría
Engine Coverage = agregación de Visibilidad por motor
Citation Rate = Visibilidad / oportunidades de retrieval
```

- **Visibilidad** es el prerequisito: sin ella, las demás métricas no aplican.
- **SoM y Ranking** son complementarias: SoM mide cuánto, Ranking mide dónde.
- **PAWC** combina ambas con volumen de contenido.
- **Coverage y Engine Coverage** son métricas de robustez: miden consistencia a través de dimensiones.
- **Citation Rate** es diagnóstica: diferencia problemas de retrieval vs. generación.
- **Sentiment** es cualitativa: un SoM alto con sentimiento negativo es peor que un SoM medio con sentimiento positivo.

---

*Siguiente: [Arquitectura Experimental](02_EXPERIMENTAL.md) — Cómo medimos estas métricas en entorno controlado.*
