# Fase 0: Setup e Infraestructura

**Duracion estimada**: 1 semana
**Dependencias**: Ninguna
**Coste**: $0

---

## Objetivo

Preparar el repositorio, las dependencias y la configuracion base para que todo el desarrollo posterior sea reproducible y ordenado. Esta fase no genera resultados cientificos — es puramente de ingenieria.

---

## Tareas

### 0.1 Reestructurar el repositorio

**Ref. arquitectura**: Seccion 11.1

Crear la estructura de directorios definitiva:

```
TFG/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── .env.example                    # Variables de entorno necesarias (sin valores)
├── .gitignore
│
├── config/
│   ├── experiment_config.json      # Configuracion congelada del experimento
│   └── queries.json                # Set fijo de 15 queries
│
├── src/                            # Codigo fuente modular
│   ├── __init__.py
│   ├── processing/                 # Scraping, chunking, embeddings
│   │   ├── __init__.py
│   │   ├── html_processor.py
│   │   └── chunker.py
│   ├── rag/                        # RAG Simulator
│   │   ├── __init__.py
│   │   ├── judge.py
│   │   └── citation_extractor.py
│   ├── metrics/                    # Framework de metricas GEO
│   │   ├── __init__.py
│   │   ├── geo_metrics.py
│   │   ├── sentiment.py
│   │   └── content_scorer.py
│   ├── evaluation/                 # Evaluacion live LLMs
│   │   ├── __init__.py
│   │   └── live_evaluator.py
│   ├── generation/                 # Generador de paginas
│   │   ├── __init__.py
│   │   ├── page_generator.py
│   │   └── validator.py
│   └── prompts/                    # Registro de prompts
│       ├── __init__.py
│       └── registry.py
│
├── notebooks/                      # Notebooks de ejecucion
│   ├── experimental_run.ipynb      # Pipeline experimental (refactored de firststep.ipynb)
│   └── analysis.ipynb              # Analisis de resultados
│
├── collect_metrics/                # Scripts de recoleccion (ya existente)
│   ├── collect_seo.py
│   └── collect_geo_live.py         # Nuevo: evaluacion live LLMs
│
├── data/
│   ├── seo/                        # Metricas SEO (ya existente)
│   ├── geo/
│   │   ├── experimental/           # Runs experimentales
│   │   │   └── run_YYYYMMDD_NNN/
│   │   └── live/                   # Metricas live diarias
│   ├── content/                    # Snapshots HTML
│   └── pages_generated/            # Paginas generadas por IA
│
├── docs/
│   ├── ARCHITECTURE_REPORT.md
│   └── phases/
│
├── contexto-interno/               # Documentos del profesor (ya existente)
│
├── .github/workflows/              # CI/CD
│   ├── seo_audit.yml               # Ya existente
│   └── geo_live_audit.yml          # Nuevo: auditorias GEO live
│
└── firststep.ipynb                 # Original (mantener como referencia)
```

**Acciones concretas**:
1. Crear directorios `src/`, `config/`, `notebooks/`, `data/geo/`, `data/content/`, `data/pages_generated/`
2. Crear archivos `__init__.py` vacios en cada paquete `src/`
3. Mover o copiar logica de `firststep.ipynb` a modulos en `src/` (Fase 1)
4. Actualizar `.gitignore` para incluir `data/content/`, `*.pyc`, `__pycache__/`

---

### 0.2 Crear `requirements.txt` con versiones fijas

**Ref. arquitectura**: Seccion 14.1

```txt
# Core
langchain==0.3.*
langchain-community==0.3.*
langchain-openai==0.3.*
langchain-google-genai==2.*
langgraph==0.3.*

# LLM APIs
openai==1.*
google-generativeai==0.8.*

# Embeddings & Vector Store
faiss-cpu==1.9.*
tiktoken==0.8.*

# Web Processing
beautifulsoup4==4.*
requests==2.*

# Data
python-dotenv==1.*
notion-client==2.*

# Analysis (Fase 6)
pandas==2.*
matplotlib==3.*
seaborn==0.13.*

# NLP (Fase 2/5)
# transformers==4.*    # Descomentar para perplejidad local
# torch==2.*           # Descomentar para modelos locales en Kaggle
```

**Nota**: Fijar versiones exactas (`==`) cuando se haga el primer run experimental (Fase 3) para garantizar reproducibilidad total.

---

### 0.3 Crear configuracion del experimento

**Ref. arquitectura**: Seccion 4.1

Archivo `config/experiment_config.json`:

```json
{
  "version": "1.0.0",
  "target_url": "https://programamos.es",
  "target_brand": "Programamos",

  "rag_simulator": {
    "model": "gpt-4o",
    "temperature": 0.0,
    "seed": 42,
    "max_tokens": 2000,
    "response_format": "json_object"
  },

  "embeddings": {
    "model": "text-embedding-3-small",
    "dimensions": 1536
  },

  "chunking": {
    "default_chunk_size_tokens": 1024,
    "default_overlap_tokens": 128,
    "faq_chunk_size_tokens": 256,
    "faq_overlap_tokens": 64
  },

  "retrieval": {
    "top_k": 5,
    "search_type": "similarity"
  },

  "competitors": [
    "code.org",
    "scratch.mit.edu",
    "codelearn.es",
    "campustecnologico.es"
  ],

  "live_evaluation": {
    "engines": ["chatgpt", "gemini", "perplexity"],
    "chatgpt_model": "gpt-4o",
    "gemini_model": "gemini-2.0-flash"
  }
}
```

---

### 0.4 Congelar set de queries

**Ref. arquitectura**: Seccion 4.2

Archivo `config/queries.json`:

```json
{
  "version": "1.0.0",
  "description": "Set fijo de 15 queries para modo experimental. No modificar entre runs.",
  "categories": {
    "informacional": [
      "Que proyectos existen para ensenar programacion a ninos en Espana?",
      "Como puedo ensenar a programar a ninos de primaria?",
      "Que recursos gratuitos hay para aprender Scratch?",
      "Cuales son las mejores iniciativas de educacion tecnologica para jovenes?",
      "Que organizaciones sin animo de lucro promueven la programacion infantil?"
    ],
    "comparativa": [
      "Cual es la mejor plataforma para que los ninos aprendan a programar?",
      "Diferencias entre Code.org, Scratch y otras plataformas educativas de programacion",
      "Que alternativas a Code.org existen en espanol?",
      "Comparativa de herramientas para ensenar pensamiento computacional",
      "Que proyectos educativos de programacion operan en Andalucia?"
    ],
    "navegacional": [
      "En que consiste el proyecto Programamos?",
      "Quien esta detras de Programamos.es?",
      "Que ofrece la web programamos.es?",
      "Recursos de Programamos para docentes",
      "Como participar en Programamos?"
    ]
  }
}
```

---

### 0.5 Crear `.env.example`

```env
# OpenAI
OPENAI_API_KEY=sk-...

# Google
GOOGLE_API_KEY=AI...
GOOGLE_PAGESPEED_KEY=AI...

# Tavily
TAVILY_API_KEY=tvly-...

# Notion
NOTION_TOKEN=ntn_...
NOTION_DATABASE_ID=...

# User Agent
USER_AGENT=GeoAuditBot/1.0 (TFG Research)
```

---

### 0.6 Crear prompt registry inicial

**Ref. arquitectura**: Seccion 8.4

Archivo `src/prompts/registry.py` con la estructura base (los prompts completos se implementan en Fase 1):

```python
"""
Registro centralizado de prompts.
Cada prompt tiene version, modelo asociado y changelog.
"""

PROMPT_REGISTRY = {
    "rag_judge": {
        "version": "1.0.0",
        "system": "",      # Se implementa en Fase 1
        "model": "gpt-4o",
        "temperature": 0.0,
        "seed": 42,
        "changelog": []
    },
    "metrics_extractor": {
        "version": "1.0.0",
        "system": "",      # Se implementa en Fase 2
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "seed": 42,
        "changelog": []
    },
    "page_generator": {
        "version": "1.0.0",
        "system": "",      # Se implementa en Fase 4
        "model": "gpt-4o",
        "temperature": 0.3,
        "changelog": []
    },
}
```

---

## Criterios de Aceptacion

- [ ] Estructura de directorios creada segun esquema
- [ ] `requirements.txt` existe y `pip install -r requirements.txt` funciona sin errores
- [ ] `config/experiment_config.json` creado y validado como JSON valido
- [ ] `config/queries.json` creado con 15 queries (5 por categoria)
- [ ] `.env.example` documentando todas las variables necesarias
- [ ] `src/prompts/registry.py` con estructura base
- [ ] `.gitignore` actualizado (data/content/, __pycache__, .env)
- [ ] `firststep.ipynb` original preservado como referencia
- [ ] Todo commiteado y pusheado

---

## Notas

- **No refactorizar `firststep.ipynb` todavia** — eso es tarea de la Fase 1. Aqui solo creamos la estructura.
- Los `__init__.py` vacios son necesarios para que Python reconozca los paquetes.
- Las versiones en `requirements.txt` se fijaran con `==` exacto al inicio de la Fase 3 (antes del baseline).
