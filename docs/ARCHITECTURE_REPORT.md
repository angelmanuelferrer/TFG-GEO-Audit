# Reporte de Arquitectura del Sistema GEO-Audit
## Trabajo Fin de Grado: Generative Engine Optimization para Programamos.es

**Autor**: Angel Manuel Ferrer Alvarez
**Directores**: Jesús Moreno León, Miguel Camacho
**Universidad de Sevilla** | Febrero 2026

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Análisis de Requisitos](#2-análisis-de-requisitos)
3. [Arquitectura del Sistema](#3-arquitectura-del-sistema)
4. [Modo Experimental (Core TFG)](#4-modo-experimental-core-tfg)
5. [Pipeline RAG Simulator](#5-pipeline-rag-simulator)
6. [Framework de Métricas GEO](#6-framework-de-métricas-geo)
7. [Pipeline de Procesamiento NLP](#7-pipeline-de-procesamiento-nlp)
8. [Sistema de Prompts](#8-sistema-de-prompts)
9. [Generador de Páginas Optimizadas con IA](#9-generador-de-páginas-optimizadas-con-ia)
10. [Modo Plataforma (Extensión)](#10-modo-plataforma-extensión)
11. [Pipeline de Datos y Almacenamiento](#11-pipeline-de-datos-y-almacenamiento)
12. [Estrategia de Despliegue](#12-estrategia-de-despliegue)
13. [Control de Costes y Presupuesto](#13-control-de-costes-y-presupuesto)
14. [Reproducibilidad y Rigor Científico](#14-reproducibilidad-y-rigor-científico)
15. [Plan de Desarrollo por Fases](#15-plan-de-desarrollo-por-fases)
16. [Apéndice: Justificaciones con Referencias](#16-apéndice-justificaciones-con-referencias)

---

## 1. Resumen Ejecutivo

Este TFG diseña e implementa un **sistema de auditoría GEO (Generative Engine Optimization)** que mide la visibilidad de un sitio web (caso de estudio: programamos.es) en las respuestas generadas por motores de IA (ChatGPT, Gemini, Perplexity). El proyecto combina:

- **Recogida automatizada de métricas SEO técnicas** (PageSpeed/Lighthouse)
- **Simulación de motores generativos** mediante un pipeline RAG con LangGraph
- **Evaluación cuantitativa** con métricas GEO respaldadas por la literatura (Share of Model, Citation Rate, Position-Adjusted Word Count)
- **Experimentación controlada** que mide el impacto de cambios en el contenido web sobre la visibilidad en IA
- **Generación de páginas optimizadas** con agentes IA

El sistema opera en dos modos: **Experimental** (rigor científico, variables controladas) y **Plataforma** (multi-agente, dashboards, recomendaciones automatizadas).

### Diferenciación respecto al estado del arte

| Aspecto | Papers existentes | Este TFG |
|---------|------------------|----------|
| Scope | Benchmarks estáticos | Caso de estudio longitudinal real |
| Métricas | Solo visibilidad | Visibilidad + SEO técnico + correlación |
| Idioma | Predominantemente inglés | Español (underrepresented) |
| Pipeline | Evaluación puntual | Monitorización continua automatizada |
| Accionable | Solo métricas | Métricas + generador de páginas optimizadas |

---

## 2. Análisis de Requisitos

### 2.1 Requisitos del Profesor (3 Bloques)

Derivados de `contexto-interno/guia.md`:

**Bloque 1 — Recolección de Métricas**
- Métricas de desempeño web (SEO técnico): PageSpeed/Lighthouse periódico
- Métricas de autoridad en LLMs (GEO): Prompts controlados a ChatGPT, Gemini, Perplexity
- Objetivo: Analizar evolución temporal ante cambios en la web

**Bloque 2 — Buenas Prácticas SEO+GEO y Experimentación**
- Revisión de buenas prácticas (estructura, semántica, schema, arquitectura de contenidos)
- Aplicación progresiva en programamos.es
- Evaluación de impacto con las métricas del Bloque 1

**Bloque 3 — Generación de Páginas Optimizadas con IA**
- Agentes IA que generen HTML/CSS optimizado
- Dos modos: desde descripción del usuario o clonando otra web
- Uso de modelos como Gemini o Claude Sonnet

### 2.2 Requisitos Técnicos Derivados de la Reunión con Miguel Camacho

De `contexto-interno/reunion1.md`:
- **Stack docente**: Jupyter Notebooks, Kaggle, LangChain, FAISS
- **Principio de selección de modelo**: "El más pequeño y más malo que haga lo que necesitas"
- **Gestión de costes**: Fundamental en todas las decisiones
- **Temperatura**: 0.2-0.4 para RAG (determinismo)
- **Ejecución en Kaggle**: GPUs gratuitas (T4/P100), 30h semanales

### 2.3 Requisitos Derivados de la Literatura

De `contexto-interno/papers.md`:
- GEO requiere métricas propias (no reutilizar SEO clásico) — (Aggarwal et al., 2023)
- Preservar estructura HTML mejora RAG — (Tan et al., 2024; HtmlRAG)
- Chunks de 512-1024 tokens con 128 overlap como default — (Ammar et al., 2025)
- Multi-agente supera single-prompt en tareas complejas estructuradas — (Tang et al., 2025)
- LLMs prefieren contenido de baja perplejidad y alta similitud semántica — (Lijia et al., 2025)

---

## 3. Arquitectura del Sistema

### 3.1 Diagrama de Componentes de Alto Nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GEO-AUDIT SYSTEM                             │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    MODO EXPERIMENTAL                          │  │
│  │                                                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │  │
│  │  │Strategist│→ │Discovery │→ │Processor │→ │Technical SEO│  │  │
│  │  │(Queries) │  │(Compet.) │  │(Chunks)  │  │(PageSpeed)  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────┬──────┘  │  │
│  │                                                    │         │  │
│  │  ┌──────────────────────┐  ┌──────────────────┐   │         │  │
│  │  │   RAG Simulator      │← ┘                  │   │         │  │
│  │  │ (Generative Judge)   │→ │    Reporter       │   │         │  │
│  │  │ GPT-4o, temp=0       │  │  (Notion + JSON)  │   │         │  │
│  │  └──────────────────────┘  └──────────────────┘   │         │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    SUBSISTEMAS TRANSVERSALES                   │  │
│  │                                                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │  │
│  │  │  NLP     │  │ Metrics  │  │ Prompt   │  │   Page      │  │  │
│  │  │ Pipeline │  │Framework │  │ Registry │  │  Generator  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                    INFRAESTRUCTURA                             │  │
│  │                                                               │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────┐  │  │
│  │  │  Kaggle  │  │ GitHub   │  │  Notion  │  │  JSON/CSV   │  │  │
│  │  │  (GPUs)  │  │ Actions  │  │   (DB)   │  │  (Storage)  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └─────────────┘  │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 Decisiones Arquitectónicas y Justificaciones

| Decisión | Alternativas Consideradas | Elección | Justificación |
|----------|--------------------------|----------|---------------|
| **Orquestación** | Chains simples, CrewAI, AutoGen | **LangGraph** | Grafo de estados con control explícito de flujo; mejor para pipeline reproducible que agentes autónomos (Becker, 2024: MAS puede sufrir "problem drift") |
| **Vector Store** | ChromaDB, Pinecone, Weaviate | **FAISS** | Sin servidor, sin coste, ejecución local en Kaggle, suficiente para el volumen (<10K docs) |
| **Modelo Judge** | GPT-4o-mini, Claude, Gemini | **GPT-4o (temp=0)** | Mayor capacidad de seguir instrucciones de citación; temperatura 0 para reproducibilidad (Camacho: 0.2-0.4 para RAG) |
| **Embeddings** | OpenAI ada-002, Cohere, E5 | **text-embedding-3-small** | Buen rendimiento en español, coste bajo ($0.02/1M tokens), 1536 dimensiones |
| **Chunking** | Fixed, Semantic, Sentence | **HTML-aware + RecursiveCharacter** | HtmlRAG demuestra que preservar estructura HTML mejora RAG (Tan et al., 2024) |
| **Búsqueda web** | SerpAPI, Google Custom Search | **Tavily** | API específica para agentes IA, integración nativa LangChain, search_depth="advanced" |
| **Almacenamiento** | PostgreSQL, MongoDB, SQLite | **JSON + Notion** | JSON para datos crudos (versionado en Git), Notion para dashboards visuales |
| **CI/CD** | Jenkins, GitLab CI | **GitHub Actions** | Ya configurado, cron diario para auditorías SEO |

### 3.3 Flujo de Datos Principal

```
                    Queries Fijas (Modo Experimental)
                              │
                              ▼
                    ┌─────────────────┐
                    │   Tavily Search  │──→ URLs Competidores
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  Web Scraping    │──→ HTML crudo
                    │  (BeautifulSoup) │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ HTML-Aware       │
                    │ Chunking         │──→ Chunks con metadatos
                    │ (512-1024 tok,   │
                    │  128 overlap)    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Embedding        │
                    │ (text-emb-3-sm)  │──→ FAISS Index
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ RAG Simulator    │
                    │ (GPT-4o Judge)   │──→ Respuesta con [Fuente: URL]
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Metrics Extract  │──→ Visibilidad, SoM, Rank, Coverage
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Reporter         │──→ Notion DB + JSON timestamped
                    └─────────────────┘
```

---

## 4. Modo Experimental (Core TFG)

### 4.1 Diseño Experimental

El modo experimental es el **corazón científico** del TFG. Su objetivo es medir el impacto de cambios en el contenido web sobre la visibilidad en motores generativos, aislando variables.

#### Variables del Experimento

| Variable | Tipo | Valor |
|----------|------|-------|
| **Queries** | Controlada (fija) | Set de 15-20 queries predefinidas |
| **Pipeline RAG** | Controlada (congelada) | Mismo código, mismos hiperparámetros |
| **Modelo Judge** | Controlada (constante) | GPT-4o, temp=0, seed fijo |
| **Embeddings** | Controlada (constante) | text-embedding-3-small |
| **Chunk size/overlap** | Controlada (constante) | 1024/128 |
| **Contenido web target** | **Variable independiente** | Cambia entre runs |
| **Métricas GEO** | **Variable dependiente** | Se mide cada run |
| **Métricas SEO** | Covariable (observada) | Se registra pero no se manipula |

#### Protocolo de Ejecución

```python
# Pseudocódigo del protocolo experimental
EXPERIMENT_CONFIG = {
    "queries": FIXED_QUERY_SET,           # Nunca cambian
    "model": "gpt-4o",                    # Nunca cambia
    "temperature": 0,                      # Determinismo
    "seed": 42,                            # Reproducibilidad
    "embedding_model": "text-embedding-3-small",
    "chunk_size": 1024,
    "chunk_overlap": 128,
    "top_k": 5,                           # Documentos recuperados
    "competitors": FIXED_COMPETITOR_SET,   # Lista cerrada
}

# Cada run:
# 1. Freeze config (hash SHA256 del config)
# 2. Scrape contenido actual (target + competidores)
# 3. Ejecutar pipeline completo
# 4. Extraer métricas
# 5. Guardar con timestamp + config_hash
# 6. Comparar con runs anteriores
```

### 4.2 Set de Queries Fijas

Diseñadas para cubrir tres categorías de intención:

**Informacionales (conocimiento general)**
1. "¿Qué proyectos existen para enseñar programación a niños en España?"
2. "¿Cómo puedo enseñar a programar a niños de primaria?"
3. "¿Qué recursos gratuitos hay para aprender Scratch?"
4. "¿Cuáles son las mejores iniciativas de educación tecnológica para jóvenes?"
5. "¿Qué organizaciones sin ánimo de lucro promueven la programación infantil?"

**Comparativas (competitivas)**
6. "¿Cuál es la mejor plataforma para que los niños aprendan a programar?"
7. "Diferencias entre Code.org, Scratch y otras plataformas educativas de programación"
8. "¿Qué alternativas a Code.org existen en español?"
9. "Comparativa de herramientas para enseñar pensamiento computacional"
10. "¿Qué proyectos educativos de programación operan en Andalucía?"

**Navegacionales/Marca (directas)**
11. "¿En qué consiste el proyecto Programamos?"
12. "¿Quién está detrás de Programamos.es?"
13. "¿Qué ofrece la web programamos.es?"
14. "Recursos de Programamos para docentes"
15. "¿Cómo participar en Programamos?"

**Justificación**: La distribución 5-5-5 permite medir visibilidad en queries donde la marca NO se menciona (informacionales), donde compite directamente (comparativas), y donde debería aparecer siempre (navegacionales). Esto replica los tres escenarios de descubrimiento real en motores generativos (Chen et al., 2025).

### 4.3 Línea Temporal del Experimento

```
Semana 0: Baseline (sin cambios)
    → Run inicial, métricas de referencia

Semana 1-2: Optimización de estructura HTML
    → Schema.org, headers semánticos, datos estructurados
    → Runs post-cambio

Semana 3-4: Optimización de contenido
    → Citas explícitas, estadísticas, claridad semántica
    → Runs post-cambio

Semana 5-6: Optimización GEO avanzada
    → Citation readiness, baja perplejidad, machine scannability
    → Runs post-cambio

Semana 7-8: Generación de páginas con IA
    → Nuevas páginas optimizadas por agentes
    → Runs post-cambio

Semana 9-10: Análisis y redacción
    → Correlación métricas, gráficos temporales, conclusiones
```

---

## 5. Pipeline RAG Simulator

### 5.1 Arquitectura del Simulador de Motor Generativo

El RAG Simulator es el componente más crítico: **simula cómo un motor generativo (Perplexity, ChatGPT con browse, Gemini)** selecciona y cita fuentes al responder una pregunta.

```
┌──────────────────────────────────────────────────────────┐
│                    RAG SIMULATOR                          │
│                                                          │
│  Query ──→ [Retriever] ──→ Top-K Documents               │
│                │                                          │
│                ▼                                          │
│         [Context Builder]                                │
│         - Preserva HTML headers                          │
│         - Incluye URL source en cada chunk               │
│         - Ordena por relevancia                          │
│                │                                          │
│                ▼                                          │
│         [Judge LLM (GPT-4o)]                             │
│         - System prompt: "Actúa como Perplexity AI"      │
│         - Temp=0, seed=42                                │
│         - Formato: respuesta + [Fuente: URL]             │
│                │                                          │
│                ▼                                          │
│         [Metrics Extractor]                              │
│         - Regex: \[Fuente: (.*?)\]                       │
│         - Visibilidad: target_url in citations           │
│         - SoM: my_citations / total_citations            │
│         - Rank: posición de primera mención              │
│         - Sentiment: análisis del contexto citado        │
│                │                                          │
│                ▼                                          │
│         {metrics_dict} → Reporter                        │
└──────────────────────────────────────────────────────────┘
```

### 5.2 Mejoras Propuestas sobre la Implementación Actual

La implementación actual en `firststep.ipynb` tiene varias áreas de mejora:

| Aspecto | Actual | Propuesto | Justificación |
|---------|--------|-----------|---------------|
| **Chunking** | `RecursiveCharacterTextSplitter(1000, 100)` | `HTMLAwareChunker(1024, 128)` | HtmlRAG: preservar headers mejora retrieval (Tan et al., 2024) |
| **Formato contexto** | `[URL: url] content` | `## [Fuente: url]\n### {heading}\ncontent` | Estructura jerárquica mejora citación del LLM |
| **Prompt judge** | Genérico "Actúa como Perplexity" | Prompt detallado con formato de citación explícito | Prompts estructurados mejoran consistencia (Chen & Liao, 2025) |
| **Seed** | No fijo | `seed=42` en cada llamada | Reproducibilidad del experimento |
| **k retrieval** | `k=5` fijo | `k=5` con re-ranking | Mejora precisión del contexto recuperado |
| **Error handling** | `except: pass` | Logging estructurado + retry con backoff | Producción-ready, trazabilidad |
| **Métricas** | Solo SoM y Rank | +Position-Adjusted Word Count, Coverage, Sentiment | Cobertura completa de métricas GEO (Aggarwal et al., 2023) |

### 5.3 HTML-Aware Content Processing

```python
# Propuesta de procesador HTML-aware
class HTMLAwareProcessor:
    """
    Preserva estructura semántica del HTML al hacer chunking.
    Justificación: HtmlRAG (Tan et al., 2024) demuestra que
    preservar headings, lists y tables mejora retrieval en RAG.
    """

    def process(self, url: str) -> List[Document]:
        # 1. Descargar HTML crudo
        html = requests.get(url).text
        soup = BeautifulSoup(html, 'html.parser')

        # 2. Extraer contenido principal (eliminar nav, footer, ads)
        # Salem et al., 2025: aislar main content mejora RAG
        main = soup.find('main') or soup.find('article') or soup.body

        # 3. Preservar estructura semántica
        structured_text = self._extract_with_structure(main)

        # 4. Chunking respetando headers
        chunks = self._semantic_chunk(structured_text,
                                       max_tokens=1024,
                                       overlap=128)

        # 5. Enriquecer metadatos
        for chunk in chunks:
            chunk.metadata.update({
                "source_url": url,
                "title": soup.title.string if soup.title else "",
                "schema_org": self._extract_schema(soup),
                "heading_path": chunk.heading_hierarchy,
            })

        return chunks

    def _extract_with_structure(self, element) -> str:
        """Convierte HTML a texto preservando jerarquía de headings."""
        lines = []
        for tag in element.descendants:
            if tag.name in ['h1','h2','h3','h4']:
                level = int(tag.name[1])
                lines.append(f"{'#' * level} {tag.get_text().strip()}")
            elif tag.name == 'li':
                lines.append(f"- {tag.get_text().strip()}")
            elif tag.name == 'p':
                text = tag.get_text().strip()
                if text:
                    lines.append(text)
        return '\n\n'.join(lines)
```

### 5.4 Estrategia Multi-Modelo de Validación

Para validar que los resultados no dependen de un solo LLM:

```
Pipeline Principal (Experimental):
    GPT-4o (temp=0, seed=42) → Métricas oficiales del estudio

Pipeline de Validación (cruzada, ejecutado en Kaggle):
    Gemini 1.5 Flash → Comparar resultados
    Llama 3.1 8B (local, Kaggle GPU) → Verificar sin API

Frecuencia: Pipeline principal cada run; validación cada 2 runs
```

**Justificación**: Chen et al. (2025) muestran que la "Engine Coverage" (presencia cross-engine) es una métrica clave. Validar con múltiples LLMs confirma que la visibilidad no es artefacto de un modelo específico.

---

## 6. Framework de Métricas GEO

### 6.1 Métricas Cuantitativas de Visibilidad

Basadas en la taxonomía de Aggarwal et al. (2023), Chen et al. (2025), y Wu et al. (2025):

#### 6.1.1 Visibilidad (Binary Presence)

```
Visibilidad(q) = 1 si target_url ∈ citations(response(q)), 0 en caso contrario

Visibilidad_total = Σ Visibilidad(q_i) / N
```

- **Tipo**: Binaria por query, ratio agregada
- **Rango**: [0, 1]
- **Interpretación**: Fracción de queries donde la marca aparece citada

#### 6.1.2 Share of Model (SoM)

```
SoM(q) = count(citations_target(q)) / count(citations_total(q)) × 100

SoM_agregado = Σ SoM(q_i) / N
```

- **Tipo**: Porcentaje por query
- **Rango**: [0%, 100%]
- **Interpretación**: Proporción del "espacio de citación" ocupado por la marca
- **Referencia**: Análogo a "Share of Voice" en marketing (Makrydakis et al., 2025)

#### 6.1.3 Ranking (Citation Position)

```
Rank(q) = posición de la primera citación de target_url en response(q)
           (1 = primera fuente citada, None si no aparece)

Rank_promedio = Σ Rank(q_i) / count(q_i donde Rank ≠ None)
```

- **Tipo**: Ordinal
- **Rango**: [1, ∞) o None
- **Interpretación**: Cuanto más bajo, mejor (aparecer primero)

#### 6.1.4 Position-Adjusted Word Count (PAWC)

```
PAWC(q) = Σ_i (words_from_target_in_citation_i × discount(position_i))

donde discount(pos) = 1 / log2(pos + 1)  # Similar a nDCG
```

- **Tipo**: Continua
- **Rango**: [0, ∞)
- **Interpretación**: Cantidad de palabras atribuibles a la marca, penalizadas por posición tardía
- **Referencia**: Métrica primaria en GEO-Bench (Aggarwal et al., 2023; Lüttgenau et al., 2025)

#### 6.1.5 Coverage (Query Coverage)

```
Coverage = count(queries con Visibilidad=1) / N_total_queries

Coverage_por_categoría = {
    "informacional": coverage en queries informacionales,
    "comparativa": coverage en queries comparativas,
    "navegacional": coverage en queries navegacionales,
}
```

- **Tipo**: Ratio
- **Rango**: [0, 1]
- **Interpretación**: Amplitud del descubrimiento

#### 6.1.6 Citation Rate

```
Citation_Rate(q) = count(citas_correctas_a_target) / count(veces_que_target_fue_retrieved)
```

- **Tipo**: Ratio
- **Interpretación**: Eficiencia de conversión de retrieval a citación

### 6.2 Métricas Cualitativas

| Métrica | Método | Herramienta |
|---------|--------|-------------|
| **Sentimiento** | Análisis del contexto alrededor de la mención | LLM como evaluador (GPT-4o-mini) |
| **Precisión factual** | Verificar afirmaciones vs. contenido real del sitio | Comparación embeddings claim vs. content |
| **Completitud** | ¿La respuesta cubre los servicios principales? | Checklist manual + scoring automático |
| **Tono** | Positivo/Neutro/Negativo hacia la marca | Clasificación con prompt |

### 6.3 Métricas SEO Técnicas (Covariables)

Ya implementadas en `collect_metrics/collect_seo.py`:

| Métrica | Fuente | Frecuencia |
|---------|--------|------------|
| SEO Score | Lighthouse | Diaria (GitHub Actions) |
| Performance Score | Lighthouse | Diaria |
| Accessibility Score | Lighthouse | Diaria |
| Best Practices Score | Lighthouse | Diaria |
| LCP (Largest Contentful Paint) | Lighthouse | Diaria |
| TBT (Total Blocking Time) | Lighthouse | Diaria |

### 6.4 Scorecard Integrado

```json
{
  "run_id": "2026-02-08_001",
  "config_hash": "sha256:abc123...",
  "timestamp": "2026-02-08T10:00:00Z",
  "target_url": "https://programamos.es",

  "geo_metrics": {
    "visibilidad_total": 0.73,
    "som_promedio": 28.5,
    "rank_promedio": 2.1,
    "pawc_total": 342.7,
    "coverage": {
      "total": 0.73,
      "informacional": 0.60,
      "comparativa": 0.80,
      "navegacional": 1.00
    },
    "citation_rate": 0.85,
    "sentiment": "positivo"
  },

  "seo_metrics": {
    "seo_score": 92,
    "performance": 78,
    "accessibility": 95,
    "best_practices": 88,
    "lcp": "2.1s",
    "tbt": "150ms"
  },

  "meta": {
    "model": "gpt-4o",
    "temperature": 0,
    "seed": 42,
    "n_queries": 15,
    "n_competitors": 5
  }
}
```

---

## 7. Pipeline de Procesamiento NLP

### 7.1 Estrategia de Scraping y Preservación de Estructura

```python
# Componentes del pipeline NLP

# 1. SCRAPING CON ESTRUCTURA
class StructuredWebLoader:
    """
    Extiende WebBaseLoader para preservar estructura HTML.
    Justificación: HtmlRAG (Tan et al., 2024) - preservar headings,
    lists y tables mejora RAG sobre plain text.
    """

    REMOVE_TAGS = ['nav', 'footer', 'header', 'aside', 'script',
                   'style', 'noscript', 'iframe']

    def load(self, url: str) -> dict:
        response = requests.get(url, headers={
            'User-Agent': 'GeoAuditBot/1.0 (TFG Research)'
        })
        soup = BeautifulSoup(response.text, 'html.parser')

        # Eliminar ruido (Salem et al., 2025)
        for tag in soup(self.REMOVE_TAGS):
            tag.decompose()

        return {
            "url": url,
            "title": soup.title.string if soup.title else "",
            "structured_content": self._to_structured_markdown(soup),
            "schema_org": self._extract_jsonld(soup),
            "meta_description": self._get_meta(soup, "description"),
            "raw_html": str(soup),
        }
```

### 7.2 Estrategia de Chunking

Basada en los hallazgos de Ammar et al. (2025) y Stäbler et al. (2025):

| Tipo de Contenido | Chunk Size | Overlap | Justificación |
|-------------------|-----------|---------|---------------|
| Páginas de contenido largo | 1024 tokens | 128 tokens | Ammar et al. (2025): mejor context precision (0.90) y recall (0.94) |
| FAQs / Preguntas cortas | 256 tokens | 64 tokens | Bhat et al. (2025): chunks pequeños para respuestas locales |
| Tablas / Datos estructurados | Unidad semántica completa | 0 | Song (2025): preservar tabla íntegra mejora table QA |
| Schema.org / Metadatos | Separado como metadato | N/A | No chunked, adjuntado al documento |

```python
class HTMLAwareChunker:
    """
    Chunking que respeta fronteras semánticas HTML.

    Estrategia:
    1. Dividir por H1/H2 (secciones principales)
    2. Dentro de cada sección, RecursiveCharacterTextSplitter
    3. Preservar heading path en metadatos
    4. Overlap de 128 tokens entre chunks de misma sección
    """

    def __init__(self, chunk_size=1024, overlap=128):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
            # Separadores que respetan estructura markdown
        )

    def chunk(self, structured_content: str, metadata: dict) -> List[Document]:
        # Dividir por secciones H2
        sections = re.split(r'\n(?=## )', structured_content)

        chunks = []
        for section in sections:
            # Extraer heading
            heading_match = re.match(r'^(#+)\s+(.+)', section)
            heading = heading_match.group(2) if heading_match else "Sin título"

            # Chunk dentro de la sección
            section_chunks = self.splitter.split_text(section)

            for i, chunk_text in enumerate(section_chunks):
                chunks.append(Document(
                    page_content=chunk_text,
                    metadata={
                        **metadata,
                        "section_heading": heading,
                        "chunk_index": i,
                        "total_section_chunks": len(section_chunks),
                    }
                ))

        return chunks
```

### 7.3 Estrategia de Embeddings

**Modelo seleccionado**: `text-embedding-3-small` (OpenAI)

| Modelo | Dimensiones | Español | Coste/1M tokens | Benchmark MTEB |
|--------|------------|---------|-----------------|----------------|
| text-embedding-3-small | 1536 | Bueno | $0.02 | 62.3 |
| text-embedding-3-large | 3072 | Mejor | $0.13 | 64.6 |
| multilingual-e5-large | 1024 | Excelente | Gratis (local) | 61.5 |
| Cohere embed-multilingual-v3 | 1024 | Excelente | $0.10 | 63.8 |

**Justificación**: `text-embedding-3-small` ofrece el mejor balance coste/rendimiento para el presupuesto del TFG. Para validación, se puede ejecutar `multilingual-e5-large` localmente en Kaggle (gratis, GPU).

**Configuración FAISS**:
```python
# FAISS con IndexFlatIP (Inner Product = Cosine Similarity para vectores normalizados)
# Para <10K documentos, búsqueda exacta es suficiente y más simple
vectorstore = FAISS.from_documents(
    documents=chunks,
    embedding=OpenAIEmbeddings(model="text-embedding-3-small"),
)
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}
)
```

### 7.4 Extracción de Citaciones y Menciones

```python
class CitationExtractor:
    """
    Extrae y analiza citaciones de respuestas generadas.

    Patrones soportados:
    - [Fuente: URL]
    - [1] URL
    - según URL, ...
    - fuente: URL
    """

    PATTERNS = [
        r'\[Fuente:\s*(https?://[^\]]+)\]',
        r'\[(?:Fuente|Source):\s*(https?://[^\]]+)\]',
        r'(?:según|fuente|referencia|ver)\s*(?:en\s*)?(https?://\S+)',
        r'\[(https?://[^\]]+)\]',
    ]

    def extract(self, response: str, target_url: str) -> dict:
        citations = []
        for pattern in self.PATTERNS:
            for match in re.finditer(pattern, response, re.IGNORECASE):
                url = match.group(1).strip().rstrip('.')
                citations.append({
                    "url": url,
                    "position": match.start(),
                    "is_target": target_url in url,
                })

        # Detectar menciones de marca sin URL
        brand_mentions = self._find_brand_mentions(
            response, "Programamos"
        )

        # Calcular métricas
        total = len(citations)
        target_cites = [c for c in citations if c["is_target"]]

        return {
            "citations": citations,
            "brand_mentions": brand_mentions,
            "total_citations": total,
            "target_citations": len(target_cites),
            "is_visible": len(target_cites) > 0 or len(brand_mentions) > 0,
            "som": (len(target_cites) / total * 100) if total > 0 else 0,
            "first_citation_rank": self._get_rank(citations, target_url),
        }

    def _find_brand_mentions(self, text: str, brand: str) -> list:
        mentions = []
        for match in re.finditer(brand, text, re.IGNORECASE):
            # Extraer contexto (±50 chars) para sentiment
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            mentions.append({
                "position": match.start(),
                "context": text[start:end],
            })
        return mentions
```

### 7.5 Análisis de Sentimiento de Menciones

```python
class BrandSentimentAnalyzer:
    """
    Analiza el sentimiento del contexto alrededor de menciones de marca.
    Usa GPT-4o-mini para clasificación (bajo coste).
    Justificación: Krugmann & Hartmann (2024) - sentimiento en era
    de IA generativa requiere LLMs para capturar matices.
    """

    PROMPT = """Analiza el sentimiento hacia la marca "{brand}" en este fragmento.

Fragmento: "{context}"

Clasifica como:
- POSITIVO: La marca se presenta favorablemente
- NEUTRO: Mención factual sin valoración
- NEGATIVO: La marca se presenta desfavorablemente

Responde SOLO con: POSITIVO, NEUTRO o NEGATIVO"""

    def analyze(self, mentions: list, brand: str) -> dict:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        sentiments = []

        for mention in mentions:
            response = llm.invoke(
                self.PROMPT.format(brand=brand, context=mention["context"])
            )
            sentiments.append(response.content.strip().upper())

        return {
            "sentiments": sentiments,
            "positive_ratio": sentiments.count("POSITIVO") / len(sentiments) if sentiments else 0,
            "distribution": {
                "positivo": sentiments.count("POSITIVO"),
                "neutro": sentiments.count("NEUTRO"),
                "negativo": sentiments.count("NEGATIVO"),
            }
        }
```

---

## 8. Sistema de Prompts

### 8.1 Prompt del RAG Simulator Judge (Crítico)

Este es el prompt más importante del sistema. Simula cómo un motor generativo sintetiza respuestas.

```python
RAG_JUDGE_SYSTEM_PROMPT = """Eres un motor de búsqueda generativo (similar a Perplexity AI).
Tu trabajo es responder preguntas sintetizando información de múltiples fuentes.

REGLAS ESTRICTAS:
1. Usa SOLAMENTE la información del contexto proporcionado.
2. SIEMPRE cita las fuentes con el formato exacto: [Fuente: URL_completa]
3. Si múltiples fuentes son relevantes, cita TODAS las que uses.
4. Coloca las citaciones INMEDIATAMENTE después de la información que respaldan.
5. Si una fuente es más relevante o autoritativa, menciónala primero.
6. NO inventes información que no esté en el contexto.
7. Si el contexto no contiene suficiente información, dilo explícitamente.
8. Responde en español.
9. Estructura tu respuesta con párrafos claros.
10. Prioriza fuentes con información más específica y detallada.

FORMATO DE RESPUESTA:
[Párrafo 1 con información sintetizada] [Fuente: URL1] [Fuente: URL2]

[Párrafo 2 con información adicional] [Fuente: URL3]

...

Fuentes consultadas:
- [Fuente: URL1] - Breve descripción
- [Fuente: URL2] - Breve descripción
"""

RAG_JUDGE_USER_TEMPLATE = """Contexto recuperado de la web:

{context}

---

Pregunta del usuario: {question}

Responde sintetizando la información del contexto, citando las fuentes."""
```

**Justificación del diseño**:
- **Formato de citación explícito**: Chen et al. (2025) muestran que la citation readiness del contenido afecta qué fuentes son citadas. El prompt fuerza un formato parseable.
- **Temperatura 0**: Reproducibilidad (Camacho: 0.2-0.4 para RAG determinista).
- **Priorización por relevancia**: Simula el authority bias observado en motores generativos reales (Chen et al., 2025).
- **Solo contexto**: Evita contaminación por conocimiento paramétrico del LLM.

### 8.2 Prompt del Strategist

```python
STRATEGIST_SYSTEM_PROMPT = """Eres un consultor experto en GEO (Generative Engine Optimization).
Tu tarea es generar preguntas estratégicas que usuarios reales harían a motores de búsqueda IA.

REGLAS:
1. Genera exactamente {n_queries} preguntas.
2. NO uses el nombre de la marca en las preguntas informacionales.
3. Las preguntas deben ser naturales (como las haría un usuario real).
4. Distribuye las preguntas en 3 categorías:
   - INFORMACIONALES: Buscan conocimiento general del dominio
   - COMPARATIVAS: Comparan opciones/alternativas
   - NAVEGACIONALES: Buscan información específica de la marca
5. Cada pregunta debe terminar con "?"
6. Las preguntas deben estar en español.

CONTEXTO DE LA MARCA:
{brand_context}

FORMATO DE SALIDA (una pregunta por línea):
[INFO] pregunta informacional?
[COMP] pregunta comparativa?
[NAV] pregunta navegacional?
"""
```

### 8.3 Prompts del Generador de Páginas

```python
PAGE_GENERATOR_SYSTEM_PROMPT = """Eres un experto en GEO (Generative Engine Optimization) y
desarrollo web. Generas páginas HTML/CSS optimizadas para máxima visibilidad en motores
de búsqueda generativos (ChatGPT, Gemini, Perplexity).

PRINCIPIOS GEO QUE APLICAS:
1. MACHINE SCANNABILITY: Estructura HTML semántica (h1>h2>h3), schema.org, datos estructurados
2. CITATION READINESS: Incluir datos verificables, estadísticas, nombres propios, fechas
3. SEMANTIC CLARITY: Frases claras y directas, evitar ambigüedad
4. BAJA PERPLEJIDAD: Texto predecible y bien estructurado (Lijia et al., 2025)
5. AUTHORITY SIGNALS: Referencias externas, credenciales, testimonios

REQUISITOS TÉCNICOS:
- HTML5 semántico
- CSS con Tailwind (CDN)
- Schema.org JSON-LD
- Meta tags completos (title, description, og:*, twitter:*)
- Headers jerárquicos (solo un H1)
- Alt text en todas las imágenes
- Responsive design

FORMATO DE SALIDA:
Devuelve el HTML completo listo para desplegar.
"""

PAGE_CLONE_PROMPT = """Analiza la siguiente página web y genera una versión optimizada
para GEO siguiendo los principios anteriores.

URL ORIGINAL: {source_url}
CONTENIDO EXTRAÍDO:
{extracted_content}

INSTRUCCIONES ADICIONALES:
- Mantén la misma información y propósito
- Mejora la estructura semántica
- Añade schema.org apropiado
- Optimiza para citation readiness
- Señala dependencias backend que NO se pueden replicar (formularios, APIs, etc.)

LIMITACIONES DETECTADAS:
{detected_limitations}
"""
```

### 8.4 Gestión y Versionado de Prompts

```python
# prompts/registry.py
PROMPT_REGISTRY = {
    "rag_judge": {
        "version": "1.0.0",
        "system": RAG_JUDGE_SYSTEM_PROMPT,
        "user_template": RAG_JUDGE_USER_TEMPLATE,
        "model": "gpt-4o",
        "temperature": 0,
        "seed": 42,
        "max_tokens": 2000,
        "changelog": [
            "1.0.0: Initial version with explicit citation format",
        ]
    },
    "strategist": {
        "version": "1.0.0",
        "system": STRATEGIST_SYSTEM_PROMPT,
        "model": "gpt-4o",
        "temperature": 0.7,  # Creatividad para generar queries diversas
        "changelog": [
            "1.0.0: Initial with 3-category query generation",
        ]
    },
    "page_generator": {
        "version": "1.0.0",
        "system": PAGE_GENERATOR_SYSTEM_PROMPT,
        "model": "gpt-4o",  # Necesita capacidad de generación larga
        "temperature": 0.3,
        "max_tokens": 4000,
        "changelog": [
            "1.0.0: Initial with GEO principles and Tailwind",
        ]
    },
}
```

---

## 9. Generador de Páginas Optimizadas con IA

### 9.1 Arquitectura (Bloque 3 del Profesor)

```
┌─────────────────────────────────────────────────┐
│              PAGE GENERATOR                      │
│                                                  │
│  MODO A: Desde Descripción                       │
│  ┌──────────┐   ┌──────────┐   ┌─────────────┐ │
│  │ User      │→  │ GEO      │→  │ HTML/CSS    │ │
│  │ Description│   │ Optimizer│    │ Generator  │ │
│  └──────────┘   └──────────┘   └──────┬──────┘ │
│                                        │        │
│  MODO B: Clonación Optimizada          │        │
│  ┌──────────┐   ┌──────────┐   │      │        │
│  │ Source    │→  │ Analyzer  │→  │      │        │
│  │ URL      │   │(structure,│   │      │        │
│  │          │   │ limits)   │   │      │        │
│  └──────────┘   └──────────┘   │      │        │
│                                 │      │        │
│                          ┌──────▼──────▼──────┐ │
│                          │   Validator         │ │
│                          │   - HTML validity   │ │
│                          │   - GEO score       │ │
│                          │   - Lighthouse sim  │ │
│                          └────────────────────┘ │
└─────────────────────────────────────────────────┘
```

### 9.2 Pipeline de Generación

1. **Análisis** (si es clonación): Scrape + estructura + detectar limitaciones
2. **Generación**: LLM genera HTML/CSS con principios GEO
3. **Validación**: Verificar HTML válido, schema.org presente, headers semánticos
4. **GEO Scoring**: Evaluar machine scannability, citation readiness, perplejidad
5. **Iteración**: Si GEO score < umbral, feedback loop con el LLM

### 9.3 GEO Content Scoring

```python
class GEOContentScorer:
    """
    Evalúa el nivel de optimización GEO de una página.
    Basado en factores identificados en la literatura.
    """

    def score(self, html: str) -> dict:
        soup = BeautifulSoup(html, 'html.parser')

        scores = {
            "machine_scannability": self._score_scannability(soup),
            "citation_readiness": self._score_citation_readiness(soup),
            "semantic_structure": self._score_structure(soup),
            "schema_org": self._score_schema(soup),
            "meta_completeness": self._score_meta(soup),
        }

        scores["total"] = sum(scores.values()) / len(scores)
        return scores

    def _score_scannability(self, soup) -> float:
        """Headers jerárquicos, listas, párrafos cortos."""
        score = 0
        if soup.find('h1'): score += 20
        if soup.find_all('h2'): score += 20
        if soup.find_all('li'): score += 20
        paragraphs = soup.find_all('p')
        if paragraphs:
            avg_len = sum(len(p.text) for p in paragraphs) / len(paragraphs)
            if avg_len < 200: score += 20  # Párrafos concisos
        if soup.find_all('table'): score += 10
        if soup.find_all('strong') or soup.find_all('b'): score += 10
        return min(score, 100)

    def _score_citation_readiness(self, soup) -> float:
        """Datos verificables, estadísticas, fechas."""
        text = soup.get_text()
        score = 0
        # Números/estadísticas
        if re.findall(r'\d+%|\d+\.\d+', text): score += 25
        # Fechas
        if re.findall(r'\d{4}|\d{1,2}/\d{1,2}/\d{4}', text): score += 25
        # Nombres propios (heurística: palabras capitalizadas)
        if re.findall(r'[A-Z][a-záéíóú]+\s[A-Z][a-záéíóú]+', text): score += 25
        # Enlaces externos como referencias
        external_links = [a for a in soup.find_all('a', href=True)
                         if a['href'].startswith('http')]
        if external_links: score += 25
        return min(score, 100)

    def _score_schema(self, soup) -> float:
        """Presencia y calidad de schema.org."""
        scripts = soup.find_all('script', type='application/ld+json')
        if not scripts: return 0
        score = 50  # Tiene al menos un schema
        for script in scripts:
            try:
                data = json.loads(script.string)
                if '@type' in data: score += 25
                if 'name' in data: score += 12.5
                if 'description' in data: score += 12.5
            except: pass
        return min(score, 100)
```

---

## 10. Modo Plataforma (Extensión)

### 10.1 Justificación de Arquitectura Multi-Agente

Basada en los hallazgos de la literatura sobre MAS (Multi-Agent Systems):

> "MAS and role-based agentic workflows are most beneficial for deep, compositional, and structured tasks where decomposition, critique, and reflection matter." — (Tang et al., 2025; Becker, 2024)

El modo plataforma **sí justifica** MAS porque:
- La tarea es multi-step y estructurada (análisis + recomendación + generación)
- Cada agente se especializa en un dominio diferente
- El coste adicional (3-4x) se amortiza con la automatización

### 10.2 Agentes del Modo Plataforma

```
┌──────────────────────────────────────────────────────────┐
│                    MODO PLATAFORMA                        │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│  │ Strategist│  │ Analyst  │  │ Content Optimizer    │  │
│  │ Agent     │  │ Agent    │  │ Agent                │  │
│  │ (queries) │  │ (metrics)│  │ (recommendations)    │  │
│  └─────┬────┘  └─────┬────┘  └──────────┬───────────┘  │
│        │             │                    │              │
│        └──────┬──────┘                    │              │
│               │                           │              │
│        ┌──────▼──────┐            ┌──────▼───────────┐  │
│        │ Orchestrator │←──────────│ Page Generator    │  │
│        │ (LangGraph)  │           │ Agent             │  │
│        └──────┬──────┘            └──────────────────┘  │
│               │                                          │
│        ┌──────▼──────┐                                   │
│        │  Reporter    │                                   │
│        │ (Notion +    │                                   │
│        │  Dashboard)  │                                   │
│        └─────────────┘                                   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 10.3 Flujo del Modo Plataforma

1. **Strategist**: Genera queries dinámicas basadas en tendencias actuales
2. **Discovery**: Encuentra competidores actualizados
3. **Processor**: Descarga y procesa contenido
4. **Analyst**: Ejecuta RAG Simulator + calcula métricas + identifica gaps
5. **Content Optimizer**: Genera recomendaciones específicas de mejora
6. **Page Generator**: Genera/mejora páginas según recomendaciones
7. **Reporter**: Publica en Notion con dashboard comparativo

**Diferencia clave vs. Modo Experimental**:
- Queries **dinámicas** (no fijas)
- Competidores **actualizados** (no congelados)
- Recomendaciones **automatizadas**
- No tiene rigor de experimento controlado (es herramienta práctica)

---

## 11. Pipeline de Datos y Almacenamiento

### 11.1 Estructura de Datos

```
data/
├── seo/                          # Métricas SEO (GitHub Actions daily)
│   ├── seo_20260208_080000.json
│   ├── seo_20260209_080000.json
│   └── ...
├── geo/                          # Resultados GEO por run
│   ├── run_20260208_001/
│   │   ├── config.json           # Configuración congelada
│   │   ├── queries.json          # Queries usadas
│   │   ├── raw_responses.json    # Respuestas completas del LLM
│   │   ├── citations.json        # Citaciones extraídas
│   │   ├── metrics.json          # Métricas calculadas
│   │   └── scorecard.json        # Scorecard integrado
│   └── ...
├── content/                      # Snapshots del contenido web
│   ├── 20260208/
│   │   ├── programamos_es.html
│   │   ├── competitor_1.html
│   │   └── ...
│   └── ...
├── pages_generated/              # Páginas generadas por IA
│   ├── from_description/
│   └── from_clone/
└── analysis/                     # Análisis y visualizaciones
    ├── temporal_evolution.csv
    ├── correlation_matrix.csv
    └── figures/
```

### 11.2 Almacenamiento Dual

| Dato | Almacenamiento Primario | Almacenamiento Visual |
|------|------------------------|----------------------|
| Métricas SEO | `data/seo/*.json` (Git) | Notion DB |
| Resultados GEO | `data/geo/run_*/` (Git) | Notion DB |
| Configuración | `data/geo/run_*/config.json` | — |
| Respuestas crudas | `data/geo/run_*/raw_responses.json` | — |
| Scorecards | `data/geo/run_*/scorecard.json` | Notion DB |
| Páginas generadas | `data/pages_generated/` (Git) | — |

**Justificación**: JSON en Git permite versionado, reproducibilidad y diff entre runs. Notion proporciona visualización inmediata para el profesor y stakeholders.

---

## 12. Estrategia de Despliegue

### 12.1 Distribución de Carga

| Componente | Entorno | Justificación |
|-----------|---------|---------------|
| **Pipeline GEO completo** | Kaggle (GPU T4) | Embeddings locales posibles, 30h gratis/semana |
| **Auditoría SEO diaria** | GitHub Actions | Cron 08:00 UTC, sin GPU, solo API calls |
| **Desarrollo y versionado** | GitHub Codespaces / Local | IDE con Black formatter |
| **Page Generator** | Kaggle o local | Depende del modelo (GPT-4o = API, Gemini = API) |
| **Validación multi-modelo** | Kaggle (GPU) | Llama 3.1 local requiere GPU |
| **Análisis y visualización** | Local / Jupyter | Pandas, matplotlib, seaborn |

### 12.2 Configuración de Kaggle

```python
# Notebook Kaggle: geo_audit_experimental.ipynb
# Requisitos:
# - Internet: ON (para APIs)
# - GPU: T4 x2 (para modelos locales) o None (solo APIs)
# - Secrets: OPENAI_API_KEY, GOOGLE_API_KEY, TAVILY_API_KEY,
#            NOTION_TOKEN, NOTION_DATABASE_ID, GOOGLE_PAGESPEED_KEY
```

### 12.3 GitHub Actions (ya existente, mejorar)

```yaml
# .github/workflows/seo_audit.yml
name: Daily SEO Audit
on:
  schedule:
    - cron: '0 8 * * *'  # 08:00 UTC diario
  workflow_dispatch:       # Manual trigger

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install requests
      - run: python collect_metrics/collect_seo.py
        env:
          PAGESPEED_API_KEY: ${{ secrets.PAGESPEED_API_KEY }}
      - run: |
          git config user.name "GEO-Audit Bot"
          git config user.email "bot@geo-audit.local"
          git add data/seo/
          git commit -m "Auto: Nuevas métricas SEO capturadas" || true
          git push
```

---

## 13. Control de Costes y Presupuesto

### 13.1 Estimación de Costes por Run

| Componente | Tokens/Run | Coste/Run | Notas |
|-----------|-----------|-----------|-------|
| **Strategist** (GPT-4o) | ~2K in + 500 out | $0.015 | 1 llamada |
| **Discovery** (GPT-4o-mini) | ~10K in + 1K out | $0.005 | 5 llamadas Tavily + LLM |
| **Tavily Search** | N/A | $0.01 | ~10 búsquedas |
| **Embeddings** | ~50K tokens | $0.001 | ~50 chunks de 1024 |
| **RAG Simulator** (GPT-4o) | ~50K in + 10K out | $0.175 | 15 queries × (3K context + 700 response) |
| **PageSpeed API** | N/A | Gratis | Límite: 25K/día |
| **Sentiment** (GPT-4o-mini) | ~5K tokens | $0.003 | ~15 clasificaciones |
| **TOTAL POR RUN** | | **~$0.21** | |

### 13.2 Presupuesto del Proyecto

| Concepto | Cantidad | Coste Total |
|----------|----------|-------------|
| Runs experimentales | ~20 runs | $4.20 |
| Runs de validación multi-modelo | ~10 runs | $2.10 |
| Generación de páginas | ~10 páginas | $2.00 |
| Desarrollo y pruebas | ~50 llamadas misc | $5.00 |
| **TOTAL ESTIMADO** | | **~$13.30** |

**Nota**: Kaggle GPU es gratis (30h/semana). GitHub Actions es gratis (2000 min/mes).

### 13.3 Estrategias de Ahorro

1. **Modelo por tarea** (principio de Camacho: "el más pequeño que funcione"):
   - Clasificación/routing → `gpt-4o-mini` ($0.15/1M in)
   - Judge/generación → `gpt-4o` ($2.50/1M in)
   - Embeddings → `text-embedding-3-small` ($0.02/1M)
2. **Caching**: Guardar embeddings de competidores (solo re-embeddear si cambia el contenido)
3. **Batching**: Procesar todas las queries en un solo run, no individualmente
4. **Modelos locales en Kaggle**: Usar Llama/Gemma para validación (coste $0)

---

## 14. Reproducibilidad y Rigor Científico

### 14.1 Garantías de Reproducibilidad

| Aspecto | Mecanismo |
|---------|-----------|
| **Configuración** | `config.json` hasheado (SHA256) por cada run |
| **Queries** | Set fijo, versionado en Git |
| **Modelo** | Modelo + versión + temperatura + seed documentados |
| **Seed** | `seed=42` en todas las llamadas a GPT-4o |
| **Contenido** | Snapshots HTML guardados en `data/content/` |
| **Código** | Versionado en Git, tag por cada run experimental |
| **Dependencias** | `requirements.txt` con versiones fijas |
| **Entorno** | devcontainer.json para entorno reproducible |

### 14.2 Limitaciones Reconocidas

1. **Determinismo imperfecto**: Incluso con `temp=0` y `seed`, OpenAI no garantiza determinismo 100% entre llamadas a diferentes horas. Se mitiga ejecutando 3 repeticiones por run y reportando media ± desviación.

2. **Sesgo del simulador**: El RAG Simulator NO es un motor generativo real (Perplexity, ChatGPT Browse). Es una simulación. Se valida comparando con queries manuales a motores reales.

3. **Sesgo de selección de queries**: Las queries fijas pueden no representar el espacio completo de búsquedas. Se mitiga con la distribución 3-categorías y validación con queries dinámicas.

4. **Evolución de modelos**: GPT-4o puede cambiar su comportamiento con actualizaciones. Se mitiga registrando el `model_version` en cada run.

### 14.3 Protocolo de Validación

```
1. VALIDACIÓN INTERNA:
   - 3 repeticiones por run → media ± std
   - Test de consistencia: misma query, mismo contenido → ¿mismos resultados?

2. VALIDACIÓN EXTERNA:
   - Comparar resultados del RAG Simulator con queries manuales a:
     * Perplexity (pro)
     * ChatGPT (con browse)
     * Gemini
   - Calcular correlación entre métricas simuladas y reales

3. VALIDACIÓN MULTI-MODELO:
   - Ejecutar pipeline con Gemini 1.5 Flash
   - Ejecutar pipeline con Llama 3.1 8B (local)
   - Comparar rankings y visibilidad
```

---

## 15. Plan de Desarrollo por Fases

### Fase 0: Setup (Semana 1)
- [ ] Reestructurar repositorio según sección 11.1
- [ ] Crear `requirements.txt` con versiones fijas
- [ ] Implementar `config.py` con EXPERIMENT_CONFIG
- [ ] Crear prompt registry (sección 8.4)

### Fase 1: Mejora del Pipeline Core (Semanas 2-3)
- [ ] Implementar `HTMLAwareProcessor` (sección 7.1)
- [ ] Implementar `HTMLAwareChunker` (sección 7.2)
- [ ] Mejorar prompt del RAG Judge (sección 8.1)
- [ ] Implementar `CitationExtractor` mejorado (sección 7.4)
- [ ] Añadir seed y reproducibilidad a todas las llamadas
- [ ] Refactorizar `firststep.ipynb` → módulos Python

### Fase 2: Framework de Métricas (Semana 4)
- [ ] Implementar todas las métricas GEO (sección 6.1)
- [ ] Implementar `BrandSentimentAnalyzer` (sección 7.5)
- [ ] Implementar `GEOContentScorer` (sección 9.3)
- [ ] Crear scorecard integrado (sección 6.4)
- [ ] Mejorar reporter de Notion con métricas completas

### Fase 3: Modo Experimental (Semanas 5-8)
- [ ] Definir set final de queries fijas (sección 4.2)
- [ ] Run baseline (Semana 5)
- [ ] Aplicar optimizaciones SEO+GEO progresivas en programamos.es
- [ ] Ejecutar runs post-cambio (Semanas 6-8)
- [ ] Guardar snapshots de contenido

### Fase 4: Generador de Páginas (Semana 7)
- [ ] Implementar Modo A: Generación desde descripción
- [ ] Implementar Modo B: Clonación optimizada
- [ ] Implementar validador y GEO scorer
- [ ] Generar páginas de prueba

### Fase 5: Validación y Multi-modelo (Semana 8)
- [ ] Ejecutar validación con Gemini
- [ ] Ejecutar validación con Llama local (Kaggle)
- [ ] Comparar con queries manuales a motores reales
- [ ] Documentar correlaciones

### Fase 6: Análisis y Redacción (Semanas 9-10)
- [ ] Generar gráficos de evolución temporal
- [ ] Calcular correlaciones SEO↔GEO
- [ ] Redactar resultados y conclusiones
- [ ] Preparar guía de buenas prácticas SEO+GEO

### (Opcional) Fase 7: Modo Plataforma
- [ ] Implementar agentes del modo plataforma (sección 10)
- [ ] Dashboard en Notion
- [ ] Recomendaciones automatizadas

---

## 16. Apéndice: Justificaciones con Referencias

### Tabla de Decisiones ↔ Papers

| Decisión | Referencia | Hallazgo Clave |
|----------|-----------|----------------|
| Métricas GEO propias (no SEO clásico) | Aggarwal et al., 2023 | GEO necesita position-adjusted word count, impression score |
| HTML-aware chunking | Tan et al., 2024 (HtmlRAG) | Preservar HTML mejora retrieval en 6 benchmarks QA |
| Chunk 1024/128 | Ammar et al., 2025 | Mejor precision (0.90), recall (0.94), faithfulness |
| LangGraph sobre MAS autónomo | Becker, 2024 | MAS puede sufrir "problem drift" en tareas simples |
| Multi-agente para plataforma | Tang et al., 2025 | MAS beneficia tareas deep/compositional/structured |
| Share of Model como métrica | Chen et al., 2025; Makrydakis et al., 2025 | Fracción de citaciones como proxy de visibilidad |
| Authority bias en retrieval | Chen et al., 2025 | LLMs prefieren fuentes autoritativas third-party |
| Baja perplejidad del contenido | Lijia et al., 2025 | Contenido predecible = más citado |
| Citation readiness | Chen et al., 2025 | Citas/estadísticas explícitas aumentan citación |
| Machine scannability | Chen et al., 2025 | Estructura parseable mejora inclusión en respuestas |
| Eliminación de ruido DOM | Salem et al., 2025 | Main content isolation mejora RAG efficiency |
| Preservar tablas íntegras | Song, 2025; Ji et al., 2025 | Table retrieval correlaciona con downstream QA |
| Semantic clarity | Lüttgenau et al., 2025 | Transformer-based optimization del contenido web |
| Sentimiento con LLMs | Krugmann & Hartmann, 2024 | Era de IA generativa requiere LLMs para sentiment |
| Validación multi-modelo | Chen et al., 2025 | Engine Coverage como métrica cross-engine |
| Temperatura 0.2-0.4 para RAG | Camacho (reunión) | Determinismo en respuestas basadas en documentación |
| "El más pequeño que funcione" | Camacho (reunión) | Gestión de costes y velocidad |

---

---

## 17. Evaluación Dual: RAG Simulado + LLMs Reales

### 17.1 Justificación del Sistema Dual

El profesor requiere explícitamente consultar ChatGPT, Gemini y Perplexity. Esto implica dos sistemas de evaluación complementarios:

```
SIMULATED (RAG Simulator)              LIVE (API Queries)
========================               =================
- Entorno controlado                   - Medición real
- Reproducible                         - No reproducible
- Mide: "¿se citaría este contenido?" - Mide: "¿se cita realmente?"
- Variable independiente:              - Variable independiente:
  contenido del sitio                    contenido del sitio
- Confounders: ninguno                 - Confounders: actualizaciones
  (pipeline congelado)                   del modelo, índice, otros sitios

EJECUTAR: Cada fase experimental       EJECUTAR: Diario / semanal
COSTE: ~$0.40 por run                  COSTE: ~$0.02 por run
```

### 17.2 Arquitectura de Evaluación Live

```python
class LiveLLMEvaluator:
    """
    Consulta motores generativos reales con prompts fijos y analiza
    respuestas para visibilidad de marca.
    """

    engines = {
        "chatgpt": {
            "api": "openai",
            "model": "gpt-4o",
            "method": "chat_completion"
        },
        "gemini": {
            "api": "google_genai",
            "model": "gemini-2.0-flash",
            "method": "generate_content"
        },
        "perplexity": {
            "api": "openai_compatible",
            "base_url": "https://api.perplexity.ai",
            "model": "sonar",
            "method": "chat_completion"
            # Perplexity devuelve citaciones nativamente
        }
    }

    # Prompts fijos de evaluación (del profesor)
    prompts = [
        "¿En qué consiste el proyecto sin ánimo de lucro Programamos?",
        "¿Qué proyectos sin ánimo de lucro existen que fomenten "
        "la enseñanza de programación?",
        "Mejores recursos gratuitos para aprender programación infantil",
        "Cómo enseñar pensamiento computacional en primaria",
        "Plataformas para aprender Scratch en español"
    ]

    def analyze_response(self, response_text, target="programamos"):
        return {
            "mention_count": self._count_mentions(response_text, target),
            "url_present": "programamos.es" in response_text.lower(),
            "first_mention_position": self._find_first_mention_normalized(
                response_text, target
            ),  # 0.0 = inicio, 1.0 = final
            "sentiment": self._classify_sentiment(response_text, target),
            "recommendation_strength": self._classify_recommendation(
                response_text, target
            ),  # "primary" | "alternative" | "mentioned" | "absent"
            "competitors_mentioned": self._extract_competitors(response_text),
        }
```

### 17.3 Métrica: Engine Coverage (Cross-Engine)

```
EC(q) = engines_que_citan_target(q) / total_engines_consultados

EC_agregado = media(EC(q_i)) para todas las queries

Ejemplo: Si para "recursos de programación":
  - ChatGPT cita programamos.es → 1
  - Gemini NO cita → 0
  - Perplexity cita → 1
  → EC = 2/3 = 0.67
```

### 17.4 GitHub Actions para Recolección Live Diaria

```yaml
# .github/workflows/geo_live_audit.yml
name: Daily GEO Live LLM Audit
on:
  schedule:
    - cron: '0 9 * * *'  # 09:00 UTC, 1h después de SEO
  workflow_dispatch:

jobs:
  geo_live:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install openai requests google-generativeai
      - run: python collect_metrics/collect_geo_live.py
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
      - run: |
          git config user.name "GEO-Audit Bot"
          git config user.email "bot@geo-audit.local"
          git add data/geo/live/
          git commit -m "Auto: New GEO live metrics captured" || true
          git push
```

---

## 18. Salida Estructurada del Judge (JSON, no Regex)

### 18.1 Problema con la Implementación Actual

El código actual en `firststep.ipynb` usa regex para parsear citaciones:

```python
# ACTUAL — Frágil, depende del cumplimiento del LLM
citations = re.findall(r'\[Fuente: (.*?)\]', ans)
```

Esto falla si el LLM cambia el formato, omite la URL, o usa variaciones.

### 18.2 Solución: Salida JSON Estructurada

```python
JUDGE_SYSTEM_PROMPT = """Eres un motor de búsqueda generativo como Perplexity AI.
Dado contexto recuperado con URLs de fuente, genera una respuesta sintetizada.

REGLAS:
1. Usa SOLO información del contexto proporcionado.
2. Cita fuentes con referencias numeradas [1], [2], etc.
3. Devuelve tu respuesta como JSON válido con este esquema exacto:

{
  "answer": "Tu respuesta con citas [1] [2] inline...",
  "citations": [
    {"index": 1, "url": "...", "quote": "cita exacta usada"},
    {"index": 2, "url": "...", "quote": "cita exacta usada"}
  ],
  "sources_used": ["url1", "url2"],
  "sources_available_but_unused": ["url3"]
}

CONTEXTO:
{context}

PREGUNTA: {question}"""

# Configuración con JSON mode de OpenAI
JUDGE_CONFIG = {
    "model": "gpt-4o",
    "temperature": 0.0,
    "seed": 42,
    "response_format": {"type": "json_object"},
    "max_tokens": 2000,
}
```

**Ventajas**:
- Parsing determinista (JSON, no regex)
- Citas exactas permiten verificar fidelidad (Venkit et al., 2024)
- `sources_available_but_unused` revela sesgo de selección del LLM
- Compatible con OpenAI JSON mode (garantiza JSON válido)

---

## 19. Chunking Token-Based (Bug Crítico en Código Actual)

### 19.1 Problema Detectado

```python
# ACTUAL en firststep.ipynb — INCORRECTO
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # ← Esto son CARACTERES, no tokens
    chunk_overlap=100     # ← Esto son CARACTERES, no tokens
)
```

1000 caracteres ≈ 200-250 tokens. La investigación recomienda 512-1024 **tokens** (Ammar et al., 2025).

### 19.2 Corrección: Token-Based Splitter

```python
import tiktoken

enc = tiktoken.encoding_for_model("gpt-4o")

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1024,
    chunk_overlap=128,
    length_function=lambda text: len(enc.encode(text)),  # TOKENS
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

### 19.3 Chunking por Tipo de Contenido

Basado en la literatura, distintos tipos de contenido necesitan configuraciones diferentes:

| Tipo Contenido | Chunk Size (tokens) | Overlap | Justificación |
|----------------|-------------------|---------|---------------|
| **Párrafo estándar** | 768 | 128 | Ammar et al., 2025: óptimo general |
| **Sección + Heading** | 896 | 128 | Budget extra para jerarquía H1>H2>contenido |
| **Lista** | 640 | 64 | Bhat et al., 2025: chunks pequeños mejoran precisión |
| **Tabla** | 1024 | 0 | Song, 2025: NUNCA dividir tablas |
| **FAQ** | 768 | 0 | Pares Q&A son unidades atómicas, 40% más citables |

---

## 20. Prompts Completos de Producción

### 20.1 Prompt de Extracción de Métricas (JSON Mode)

Este prompt extrae las 9 métricas GEO de forma determinista:

```python
def get_metrics_extraction_prompt(query, answer, target_domain="programamos.es"):
    return f"""Eres un sistema de análisis de métricas GEO. Extrae métricas
estructuradas de la respuesta de un motor generativo.

MÉTRICAS A EXTRAER:
1. visibility: ¿Aparece el dominio objetivo en alguna cita? (boolean)
2. total_citations: Número total de citas [N] (integer)
3. target_citations: Citas al dominio objetivo (integer)
4. share_of_model: (target_citations/total_citations)*100 (float)
5. citation_rank: Posición de primera cita objetivo (integer|null)
6. text_mentions: Menciones del nombre de marca (integer)
7. sentiment: "positive"|"neutral"|"negative"|"not_mentioned"
8. context: "primary_recommendation"|"alternative_option"|"brief_mention"|"not_mentioned"
9. position_adjusted_word_count: Σ(palabras_target × 1/posición) (float)

Dominio objetivo: {target_domain}
Query: {query}
Respuesta: {answer}

Responde SOLO con JSON válido."""

METRICS_CONFIG = {
    "model": "gpt-4o-mini",  # Coste eficiente para extracción
    "temperature": 0.0,
    "response_format": {"type": "json_object"},
    "seed": 42,
}
```

### 20.2 Prompt del Generador de Páginas con Reglas GEO

```python
PAGE_GENERATOR_PROMPT = """Eres un experto en GEO y desarrollo web.
Genera una página HTML5 optimizada para visibilidad en motores generativos.

PRINCIPIOS GEO (basados en investigación):

1. MACHINE SCANNABILITY (Chen et al., 2025):
   - HTML5 semántico: <article>, <section>, <nav>, <header>
   - Heading jerárquico: un solo <h1>, <h2>-<h6> secuenciales
   - Schema.org JSON-LD: Article, HowTo, FAQPage, Organization

2. CITATION READINESS (Aggarwal et al., 2023):
   - Estadísticas explícitas con <data value="X">
   - Citas en <blockquote cite="URL">
   - Fechas en <time datetime="YYYY-MM-DD">
   - Párrafos auto-contenidos (fáciles de extraer como cita)

3. LOW PERPLEXITY (Lijia et al., 2025):
   - Oraciones claras: sujeto-verbo-objeto
   - Definiciones explícitas de términos técnicos
   - Topic sentence al inicio de cada párrafo

4. AUTHORITY SIGNALS (Chen et al., 2025):
   - Referencias externas y citaciones
   - Atribución de autor con credenciales
   - Fecha de publicación/actualización

REQUISITOS TÉCNICOS:
- Tailwind CSS (CDN)
- Responsive (mobile-first)
- Meta tags: title, description, og:*, twitter:*
- Alt text en todas las imágenes
- <html lang="es">

DESCRIPCIÓN: {description}
KEYWORDS: {keywords}

Genera el HTML completo."""
```

### 20.3 Tests Automatizados de Prompts

```python
def test_judge_reproducibility():
    """Verifica que el judge produce outputs consistentes."""
    prompt = get_rag_judge_prompt(sample_context, sample_query)
    llm = ChatOpenAI(**JUDGE_CONFIG)

    outputs = [llm.invoke(prompt).content for _ in range(5)]

    from difflib import SequenceMatcher
    similarities = [
        SequenceMatcher(None, outputs[i], outputs[i+1]).ratio()
        for i in range(len(outputs)-1)
    ]
    avg_sim = sum(similarities) / len(similarities)
    assert avg_sim > 0.90, f"Reproducibilidad insuficiente: {avg_sim:.2%}"

def test_metrics_json_validity():
    """Verifica que la extracción produce JSON válido."""
    prompt = get_metrics_extraction_prompt(query, answer)
    llm = ChatOpenAI(**METRICS_CONFIG)
    output = llm.invoke(prompt).content

    metrics = json.loads(output)  # Debe ser JSON válido
    assert "visibility" in metrics
    assert "share_of_model" in metrics
    assert isinstance(metrics["total_citations"], int)
```

---

## 21. Pipeline NLP Avanzado: Scoring GEO de Contenido

### 21.1 Medición de Perplejidad del Contenido

```python
class ContentPerplexityScorer:
    """
    Contenido con baja perplejidad = más predecible para LLMs = más citado.
    (Lijia et al., 2025)
    """

    def calculate_perplexity(self, text):
        """Usa GPT-2 como proxy de perplejidad."""
        from transformers import GPT2LMHeadModel, GPT2TokenizerFast
        import torch

        model = GPT2LMHeadModel.from_pretrained('gpt2')
        tokenizer = GPT2TokenizerFast.from_pretrained('gpt2')

        encodings = tokenizer(text, return_tensors='pt', truncation=True, max_length=512)
        with torch.no_grad():
            outputs = model(**encodings, labels=encodings['input_ids'])
            perplexity = torch.exp(outputs.loss).item()

        return perplexity  # Menor = más predecible = mejor para GEO
```

### 21.2 Scoring de Citation Readiness

```python
class CitationReadinessScorer:
    """
    Evalúa qué tan "citable" es un contenido para LLMs.
    """

    def score(self, text):
        score = 0.0

        # Estadísticas presentes (Chen et al., 2025)
        if re.search(r'\d+%|\d+\.\d+', text):
            score += 0.25

        # Citas explícitas
        if re.search(r'\[.*?\]|\(.*?\d{4}.*?\)', text):
            score += 0.25

        # Estructura (listas, tablas)
        if any(marker in text for marker in ['•', '-', '1.', '|']):
            score += 0.25

        # Headers claros
        if re.search(r'^#{1,3}\s+.+$', text, re.MULTILINE):
            score += 0.25

        return score  # 0.0 - 1.0, objetivo > 0.75
```

### 21.3 Comparativa Target vs Competidores

```python
def compare_geo_readiness(target_docs, competitor_docs):
    """Compara preparación GEO del target vs competidores."""
    scorer = GEOContentScorer()

    target_scores = [scorer.score(d.page_content) for d in target_docs]
    competitor_scores = [scorer.score(d.page_content) for d in competitor_docs]

    return {
        "target_avg": sum(target_scores) / len(target_scores),
        "competitor_avg": sum(competitor_scores) / len(competitor_scores),
        "gap": target_avg - competitor_avg,  # Positivo = ventaja
        "recommendation": "IMPROVE" if gap < 0 else "MAINTAIN"
    }
```

---

## 22. Coste Total Detallado del Proyecto

### 22.1 Por Componente

| Componente | Tokens/Run | Coste/Run | Modelo |
|-----------|-----------|-----------|--------|
| Strategist (platform mode) | ~2K in + 500 out | $0.015 | GPT-4o |
| Discovery (5 queries) | ~10K in + 1K out | $0.005 | GPT-4o-mini |
| Tavily Search | N/A | $0.01 | API |
| Embeddings | ~50K tokens | $0.001 | text-emb-3-small |
| RAG Judge (15 queries) | ~50K in + 10K out | $0.175 | GPT-4o |
| Metrics Extraction | ~20K tokens | $0.003 | GPT-4o-mini |
| Sentiment Analysis | ~5K tokens | $0.003 | GPT-4o-mini |
| PageSpeed API | N/A | Gratis | Google API |
| **TOTAL POR RUN EXPERIMENTAL** | | **~$0.21** | |

### 22.2 Presupuesto Total del Proyecto

| Concepto | Cantidad | Coste |
|----------|----------|-------|
| Runs experimentales (5 fases × 3 runs) | 15 runs | $3.15 |
| Live LLM diario (60 días) | 60 runs | $1.20 |
| Runs de validación multi-modelo | 10 runs | $2.10 |
| Generación de páginas | 10 páginas | $2.00 |
| Desarrollo y pruebas | ~50 llamadas | $5.00 |
| **TOTAL** | | **~$13.45** |

### 22.3 Infraestructura Gratuita

| Recurso | Coste | Límite |
|---------|-------|--------|
| Kaggle GPU (T4 x2) | $0 | 30h/semana |
| GitHub Actions | $0 | 2000 min/mes |
| PageSpeed API | $0 | 25K queries/día |
| Gemini API (free tier) | $0 | 15 req/min |
| Notion API | $0 | Ilimitado |

---

## 23. Prioridad de Implementación

Ordenado por impacto y dependencias:

### Semana 1 (Setup Crítico)
1. **Fix chunking** character→token (1024/128) — 1 hora
2. **Crear `requirements.txt`** con versiones fijas — 30 min
3. **Reestructurar repositorio** (sección 11.1) — 1 hora
4. **Congelar query set** + competidores en JSON — 2 horas

### Semana 2 (Pipeline Core)
5. **Implementar HTML-aware processor** — 4 horas
6. **Implementar structured JSON judge** — 3 horas
7. **Implementar metrics extraction con JSON mode** — 2 horas
8. **Añadir PAWC metric** — 1 hora

### Semana 3 (Live + Métricas)
9. **Crear `collect_geo_live.py`** — 4 horas
10. **GitHub Actions workflow para GEO live** — 1 hora
11. **Implementar sentiment analysis** — 2 horas
12. **Implementar GEO content scorer** — 3 horas

### Semana 4 (Baseline + Validación)
13. **Run Phase 0 baseline** (3 repeticiones) — 1 día
14. **Validar reproducibilidad** (CV < 0.15) — 1 día
15. **Documentar métricas baseline** — 1 día

### Semanas 5-8 (Experimentación)
16. **Aplicar intervenciones SEO+GEO** progresivas
17. **Ejecutar runs post-cambio** (3 por fase)
18. **Recoger datos Live LLM** continuamente

### Semana 7 (Page Generator)
19. **Implementar Modo A** (desde descripción) — 1 día
20. **Implementar Modo B** (clonación) — 1 día
21. **Validador + GEO scorer** — 1 día

### Semanas 9-10 (Análisis y Redacción)
22. **Gráficos evolución temporal** (matplotlib/seaborn)
23. **Correlaciones SEO↔GEO**
24. **Redacción de resultados**
25. **Guía de buenas prácticas**

---

*Reporte de arquitectura completo. Generado con la colaboración de agentes especializados en LLM Architecture, NLP Engineering y Prompt Engineering. Cada decisión está respaldada por la literatura científica (50+ papers) y el contexto específico del proyecto.*
