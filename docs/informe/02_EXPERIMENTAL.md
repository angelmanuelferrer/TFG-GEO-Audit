# Arquitectura Experimental

> **Versión**: 1.0 | **Última actualización**: Marzo 2026
> Este documento describe el diseño experimental del sistema GEO-Audit: cómo aislamos el efecto de la calidad del contenido sobre la visibilidad en motores de IA.

---

## 1. Principio de diseño

El objetivo del modo experimental es responder a la pregunta: **¿mejora la visibilidad de Programamos en motores de IA si optimizamos su contenido web?**

Para responder con rigor, necesitamos aislar el contenido como la única variable que cambia entre mediciones. Todo lo demás — queries, modelo judge, embeddings, competidores, configuración — permanece congelado.

### Tabla de variables

| Tipo | Variable | Valor | Justificación |
|------|----------|-------|---------------|
| **Independiente** | Contenido web de Programamos | Cambia entre runs | Es lo que optimizamos |
| **Dependientes** | Visibilidad, SoM, Ranking, PAWC, Coverage, Citation Rate, Sentiment | Medidas en cada run | Las [8 métricas GEO](01_METRICAS_GEO.md) |
| **Controladas** | Modelo judge | Gemini 2.5 Flash, temp=0 | Consistencia entre runs |
| | Queries | 40/run (20 core + 20 rotativas) | Set fijo, `config/queries.json` v2.0 |
| | Embeddings | multilingual-e5-large, 1024d | Modelo local determinista |
| | Chunking | 256 tokens / 64 overlap | SAGEO Arena alignment (ADR-011) |
| | Competidores | FAISS congelado tras discovery | Solo target se re-embede |
| | Retrieval | top_k=5, similitud coseno | `config/experiment_config.json` |

**Formulación clave**: Nuestro simulador RAG aísla el efecto de la calidad del contenido sobre la decisión de citación del LLM, controlando por retrieval mediante un vectorstore congelado.

---

## 2. Stack de modelos y justificación

### 2.1. Discovery — Gemini 2.5 Flash + Google Search grounding

| Aspecto | Detalle |
|---------|---------|
| **Modelo** | Gemini 2.5 Flash |
| **Herramienta** | Google Search grounding |
| **Coste** | GRATIS (free tier: 1500 búsquedas/día) |

**Por qué Google Search grounding**: Los motores generativos reales (ChatGPT, Gemini, Perplexity) usan el índice web para decidir qué sitios consultar. Google Search grounding nos da URLs reales verificadas por el índice de Google — descubrimos los competidores que los motores reales citan, no URLs inventadas por el LLM.

**Por qué Gemini y no Claude**: Claude con `web_search` tool devuelve URLs menos diversas y tiene coste por búsqueda ($0.01/búsqueda). Gemini 2.5 Flash con Google Search es gratuito y devuelve URLs directamente del índice de Google, además contamos con los 300€ de prueba de Google AI Studio.

**Implementación**: `src/discovery/competitor_finder.py` — envía cada query, extrae URLs de grounding metadata + texto, agrega por dominio con scoring ponderado (cita=2 pts, mención en texto=1 pt), devuelve top 15 competidores. Delay de 2s entre queries (15 RPM free tier).

### 2.2. RAG Judge — Gemini 2.5 Flash (agent mode, JSON)

| Aspecto | Detalle |
|---------|---------|
| **Modelo** | Gemini 2.5 Flash |
| **Temperatura** | 0.0 |
| **Max tokens** | 2000 |
| **Modo** | Agent con FAISS search tool |
| **Formato** | JSON estructurado |
| **Coste** | ~$0.002/query (gratis con créditos $300 de Google Cloud) |

**Argumento central**: El experimental mide **deltas** (web vieja vs web nueva), no valores absolutos. Lo que importa es que el modelo judge sea **consistente** entre runs, no que sea el modelo más potente del mercado. Gemini 2.5 Flash con temp=0 y JSON mode ofrece la consistencia necesaria a una fracción del coste de GPT-4o ($0.002 vs $0.02/query).


### 2.3. Embeddings — multilingual-e5-large (local)

| Aspecto | Detalle |
|---------|---------|
| **Modelo** | `intfloat/multilingual-e5-large` |
| **Dimensiones** | 1024 |
| **Proveedor** | Local (Kaggle GPU T4/P100) |
| **Coste** | GRATIS (ejecución local) |

**Por qué local**: Reproducibilidad total. Los embeddings de APIs pueden cambiar sin aviso (OpenAI ha actualizado sus modelos silenciosamente). Un modelo local produce exactamente los mismos vectores cada vez.

**Por qué e5-large**: Excelente rendimiento en español (entrenado multilingüe), 1024 dimensiones (buen balance entre calidad y eficiencia en FAISS), y es el estándar en benchmarks de retrieval multilingüe.

**Independencia del judge**: Los embeddings son independientes del LLM judge. El judge recibe texto plano en su contexto, nunca ve embeddings. Los embeddings solo determinan qué chunks se recuperan (etapa de retrieval), no cómo el judge los interpreta (etapa de generación).

### 2.4. Chunking — tiktoken cl100k_base

| Aspecto | Detalle |
|---------|---------|
| **Tokenizador** | tiktoken `cl100k_base` |
| **Chunk size** | 256 tokens |
| **Overlap** | 64 tokens |
| **Separadores** | `\n## `, `\n### `, `\n\n`, `\n`, `. `, ` ` |

**Por qué 256/64**: Alineado con el benchmark SAGEO Arena (Wu et al. 2025), que usa esta configuración para evaluar GEO. Usar los mismos parámetros nos permite comparar nuestros resultados con la literatura.

**HTML-aware**: Antes de chunking, el procesador elimina elementos no-contenido (nav, footer, scripts, estilos) y preserva la jerarquía de headers. Esto reduce el ruido y mejora la calidad del retrieval.

### 2.5. Sentiment — Ollama (modelo local)

| Aspecto | Detalle |
|---------|---------|
| **Modelo** | Ollama (modelo local) |
| **Coste** | GRATIS |
| **Tarea** | Clasificación ternaria: POSITIVO / NEUTRO / NEGATIVO |

**Por qué local**: Es una tarea simple de clasificación que no requiere modelos grandes ni razonamiento complejo. Un modelo local en Kaggle o en la máquina de desarrollo es suficiente y evita coste de API.

---

## 3. Pipeline completo

### 3.1. Dos fases diferenciadas

```
┌─────────────────────┐
│  FASE 1: DISCOVERY   │  ← Se ejecuta UNA VEZ
│  (Gemini + Google)   │
│                      │
│  100 queries         │
│     ↓                │
│  Competitor URLs     │
│     ↓                │
│  Scrape + Chunk      │
│     ↓                │
│  FAISS vectorstore   │  ← SE CONGELA
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  FASE 2: EXPERIMENT  │  ← Se ejecuta N VECES
│  (por cada versión   │
│   de la web)         │
│                      │
│  Scrape target nuevo │
│     ↓                │
│  Chunk target        │
│     ↓                │
│  Merge con FAISS     │
│  congelado           │
│     ↓                │
│  RAG Judge (agent)   │
│  × 40 queries        │
│     ↓                │
│  Extracción métricas │
│     ↓                │
│  Scorecard           │
└─────────────────────┘
```

**Separación discovery/experimental**: Discovery es costoso (web scraping de ~15 competidores × 100 queries) y no necesita repetirse. Los competidores se congelan en FAISS y solo el target se re-embede en cada run experimental.

### 3.2. Flujo detallado de un run experimental

1. **Scrape del target**: Descarga HTML de `programamos.es` con procesamiento HTML-aware (`src/processing/`). Se preserva un snapshot del HTML para reproducibilidad.

2. **Chunking del target**: Divide el contenido en chunks de 256 tokens con 64 de overlap. Separadores jerárquicos que respetan la estructura HTML.

3. **Merge en FAISS**: Los chunks del target actualizado se insertan en una copia del vectorstore congelado (los competidores no cambian). El target se re-embede con e5-large.

4. **RAG Judge agent** (×40 queries): Para cada query:
   - El agente recibe la query del usuario
   - Tiene acceso a una herramienta de búsqueda (FAISS)
   - Puede buscar 1-5 veces, reformulando si necesita
   - Genera respuesta JSON con `answer`, `citations`, `sources_used`, `sources_available_but_unused`

5. **Extracción de métricas**: `CitationExtractor` procesa cada respuesta JSON y calcula Visibilidad, SoM, Ranking, menciones de marca.

6. **Agregación**: Coverage por categoría, Citation Rate, Sentiment, scorecard final.

---

## 4. RAG Judge como agente

### 4.1. Agent mode

| Aspecto | Agent |
|---------|-------|
| **Retrieval** | El LLM decide qué buscar |
| **Reformulación** |  Sí (1-5 búsquedas) |
| **Realismo** | Alto (simula el comportamiento de Perplexity/ChatGPT) |

### 4.2. Cómo funciona el agent mode

```
                    ┌──────────────┐
  Query del usuario │  RAG Judge   │
  ─────────────────►│  (Gemini)    │
                    │              │
                    │  "Necesito   │
                    │   buscar..." │
                    │      │       │
                    │      ▼       │
                    │  ┌────────┐  │
                    │  │ FAISS  │  │  ← El agente CREE que busca en la web
                    │  │ search │  │     pero busca en nuestro vectorstore
                    │  │ tool   │  │
                    │  └────────┘  │
                    │      │       │
                    │  [Puede      │
                    │   repetir    │
                    │   1-5 veces] │
                    │      │       │
                    │      ▼       │
                    │  Respuesta   │
                    │  JSON con    │
                    │  citations   │
                    └──────────────┘
```

El agente simula el comportamiento de un motor generativo como Perplexity:
1. Recibe una pregunta del usuario
2. Decide qué buscar (puede reformular la query)
3. Examina los resultados y decide si necesita más información
4. Genera una respuesta citando fuentes específicas con URLs
5. Clasifica las fuentes en "usadas" y "disponibles pero no usadas"

**El agente no sabe que busca en FAISS** — el prompt le indica que tiene una herramienta de búsqueda web. Esto es deliberado: queremos que se comporte como un motor generativo real.

### 4.3. Formato de salida JSON

```json
{
  "answer": "Texto de la respuesta con citas [1], [2]...",
  "citations": [
    {"index": 1, "url": "https://ejemplo.com", "quote": "texto citado"},
    {"index": 2, "url": "https://programamos.es/...", "quote": "texto citado"}
  ],
  "sources_used": ["https://ejemplo.com", "https://programamos.es/..."],
  "sources_available_but_unused": ["https://otro.com"]
}
```

El schema se valida en `src/rag/judge.py` — `_validate_schema()` comprueba que las claves requeridas existen.

---

## 5. Validez del retrieval por coseno

### 5.1. Las dos etapas de un motor generativo

Un motor generativo real tiene dos etapas diferenciadas:

```
Query del usuario
      │
      ▼
┌─────────────────┐
│  1. RETRIEVAL    │  ← ¿Qué documentos ve el LLM?
│                  │
│  Motor real:     │  Motor real usa: PageRank, authority,
│  Google/Bing     │  freshness, backlinks, schema.org...
│  index           │
│                  │  Nuestro FAISS usa: similitud coseno
│  Nuestro FAISS:  │  con embeddings e5-large
│  coseno          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. GENERATION   │  ← ¿Qué cita de lo que ha leído?
│                  │
│  El LLM decide:  │  Factores: calidad, estadísticas,
│  qué citar       │  autoridad, estilo, relevancia,
│                  │  claridad, estructura...
└─────────────────┘
```

### 5.2. Qué aislamos

Nuestro diseño experimental aísla la **etapa 2** (generación/citación):

- El vectorstore está **congelado** → el retrieval es constante
- Las queries son **fijas** → las búsquedas son las mismas
- Solo cambia el **contenido del target** → la decisión de citar depende de la calidad del contenido

Si entre un run y otro la Visibilidad pasa de 0 a 1, sabemos que el cambio se debe al contenido nuevo, no a que "el retrieval cambió" (porque no cambió).

### 5.3. Limitación honesta

El retrieval por coseno **no** es igual al de un motor real. Un motor real podría no recuperar nuestro contenido aunque sea excelente (problema de SEO/indexación). Nuestro simulador asume que el contenido **llega** al LLM — lo que mide es si, una vez que llega, es citado.

Por eso existe la [arquitectura Live](03_LIVE.md) como validación: si las mejoras en el simulador se traducen en mejoras con motores reales (que SÍ usan retrieval real), el diseño experimental queda validado.

---

## 6. Sistema de queries

### 6.1. Composición

100 queries totales organizadas en 3 categorías y 5 bloques:

| Bloque | Queries | Ejecutado en | Propósito |
|--------|---------|-------------|-----------|
| **CORE** | Q001–Q020 | Todos los runs | Serie temporal consistente |
| **R1** | Q021–Q040 | Runs 1, 5, 9... | Amplitud |
| **R2** | Q041–Q060 | Runs 2, 6, 10... | Amplitud |
| **R3** | Q061–Q080 | Runs 3, 7, 11... | Amplitud |
| **R4** | Q081–Q100 | Runs 4, 8, 12... | Amplitud |

**Cada run ejecuta 40 queries**: 20 core + 20 del bloque rotativo correspondiente.

### 6.2. Ejemplos por categoría

| Categoría | Ejemplo | Propósito |
|-----------|---------|-----------|
| **Informacional** (35) | "¿Qué proyectos existen para enseñar programación a niños en España?" | ¿Aparecemos como referencia? |
| **Comparativa** (35) | "Diferencias entre Code.org, Scratch y otras plataformas educativas" | ¿Nos comparan favorablemente? |
| **Navegacional** (30) | "¿Qué proyectos educativos de programación operan en Andalucía?" | ¿Nos encuentran por ubicación/nombre? |

### 6.3. Justificación del tamaño

- **100 queries**: Suficientes para calcular Coverage con significación estadística por categoría (~30+ por categoría).
- **20 core**: Serie temporal densa — cada query core evaluada en todos los runs.
- **Rotación**: Todas las queries se evalúan al menos cada 4 runs, evitando overfitting a un set pequeño.

---

## 7. Reproducibilidad

### 7.1. Controles implementados

| Control | Implementación | Propósito |
|---------|---------------|-----------|
| **Temperatura 0** | `experiment_config.json` → `rag_simulator.temperature: 0.0` | Minimiza variabilidad del judge |
| **Config versionada** | `experiment_config.json` v1.1.0, `queries.json` v2.0.0 | Trazabilidad de parámetros |
| **Vectorstore congelado** | FAISS local, competidores no re-embeddidos | Retrieval constante |
| **Snapshots HTML** | Se guarda el HTML descargado de cada run | Auditar contenido procesado |
| **Prompts versionados** | `src/prompts/registry.py` con changelog | Reproducir exactamente el prompt usado |

### 7.2. Limitaciones de reproducibilidad

- **No determinismo perfecto**: Gemini no soporta parámetro `seed`. Con temp=0 la variabilidad es mínima pero no cero. Mitigación: cada run experimental se ejecuta 3 veces y se reporta la mediana.
- **Competidores congelados**: El contenido real de los competidores puede cambiar entre runs, pero nuestra copia en FAISS no. Esto es una limitación asumida — el experimental mide el efecto del contenido propio, no del ecosistema.

---

## 8. Evidencia que soporta el diseño

### 8.1. SAGEO Arena (Wu et al. 2025)

- **Alineación de chunking**: SAGEO Arena usa 256 tokens / 64 overlap como configuración de referencia. Nuestro ADR-011 adopta exactamente estos parámetros.
- **Separación retrieval vs generation**: SAGEO demuestra que las dos etapas son independientes — mejorar el contenido para la etapa de generación tiene efecto independiente de la calidad del retrieval.
- **Citation Rate**: SAGEO introduce esta métrica como forma de aislar el efecto de la generación controlando por retrieval.

### 8.2. GEO-Bench (Aggarwal et al. 2023)

- **Framework fundacional**: Define las métricas base (Visibilidad, SoM, PAWC) y demuestra que la optimización de contenido puede mejorar la visibilidad en +115%.
- **Metodología**: Usa un simulador RAG controlado para medir el impacto de diferentes optimizaciones.

### 8.3. Argumento central

> Si el contenido funciona bien en un simulador RAG controlado (donde el retrieval está garantizado), funcionará bien en motores reales (donde el contenido llega a través de búsqueda web). La etapa de generación — decidir qué citar de lo recuperado — es conceptualmente la misma en ambos escenarios.

Este argumento se valida empíricamente con la [arquitectura Live](03_LIVE.md): correlación entre métricas simuladas y métricas reales.

---

## 9. Limitaciones

| Limitación | Impacto | Mitigación |
|-----------|---------|------------|
| Simulador ≠ realidad | No modela el retrieval real (PageRank, authority...) | Validación con Live |
| No determinismo | Gemini sin seed → variabilidad residual | 3 repeticiones por run, mediana |
| Competidores congelados | No captura cambios en el ecosistema | Live monitoriza competidores reales |
| Un solo judge | Sesgo del modelo (Gemini puede tener preferencias) | Live usa 4 motores diferentes |
| Cobertura parcial | 40 queries/run de 100 totales | Rotación asegura cobertura completa cada 4 runs |

Estas limitaciones son asumidas y documentadas. El modo experimental no pretende replicar la realidad — pretende **aislar una variable** con rigor experimental. La validación externa la proporciona el [modo Live](03_LIVE.md).

---

*Anterior: [Catálogo de Métricas GEO](01_METRICAS_GEO.md) | Siguiente: [Arquitectura Live](03_LIVE.md)*
