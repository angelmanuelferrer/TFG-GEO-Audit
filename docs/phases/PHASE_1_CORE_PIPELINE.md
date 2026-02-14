# Fase 1: Pipeline Core Mejorado

**Duracion estimada**: 2 semanas
**Dependencias**: Fase 0 completada
**Coste**: ~$1.00 (pruebas)

---

## Objetivo

Refactorizar el pipeline de `firststep.ipynb` en modulos Python reutilizables, corrigiendo los problemas criticos detectados (chunking por caracteres, parseo regex fragil) e implementando las mejoras del reporte de arquitectura.

---

## Tareas

### 1.1 Fix critico: Chunking token-based

**Ref. arquitectura**: Seccion 19

**Problema**: El chunking actual usa caracteres (1000 chars ~ 200-250 tokens). La literatura recomienda 512-1024 tokens.

**Archivo**: `src/processing/chunker.py`

**Implementar**:
- `RecursiveCharacterTextSplitter` con `length_function` basada en `tiktoken`
- Chunk size: 1024 tokens, overlap: 128 tokens
- Separadores que respetan estructura markdown: `["\n## ", "\n### ", "\n\n", "\n", ". ", " "]`
- Chunking diferenciado por tipo de contenido (parrafo, FAQ, tabla)

**Test manual**: Verificar que un texto de 5000 tokens produce ~5 chunks de ~1024 tokens cada uno.

---

### 1.2 HTML-Aware Processor

**Ref. arquitectura**: Secciones 5.3, 7.1

**Archivo**: `src/processing/html_processor.py`

**Implementar**:
- `StructuredWebLoader`: descarga HTML, elimina ruido (nav, footer, ads, scripts), extrae contenido principal
- `_extract_with_structure()`: convierte HTML a markdown preservando headings (h1-h4), listas y parrafos
- Extraccion de metadatos: title, meta description, schema.org JSON-LD
- Headers de request apropiados (`User-Agent: GeoAuditBot/1.0`)
- Timeout de 10s en requests, retry con backoff exponencial (max 3 intentos)

**Test manual**: Procesar `https://programamos.es` y verificar que el markdown preserva la jerarquia de headings.

---

### 1.3 JSON Structured Judge

**Ref. arquitectura**: Seccion 18

**Archivo**: `src/rag/judge.py`

**Problema**: El parseo actual con regex `\[Fuente: (.*?)\]` es fragil.

**Implementar**:
- System prompt del RAG Judge con formato JSON obligatorio
- Usar `response_format={"type": "json_object"}` de OpenAI
- Esquema de salida:
  ```json
  {
    "answer": "Respuesta con citas [1] [2]...",
    "citations": [
      {"index": 1, "url": "...", "quote": "cita exacta usada"}
    ],
    "sources_used": ["url1", "url2"],
    "sources_available_but_unused": ["url3"]
  }
  ```
- `temperature=0.0`, `seed=42`
- Logging de tokens usados por llamada (para control de costes)

**Test manual**: Ejecutar 3 veces la misma query con el mismo contexto y verificar consistencia > 90%.

---

### 1.4 Citation Extractor mejorado

**Ref. arquitectura**: Seccion 7.4

**Archivo**: `src/rag/citation_extractor.py`

**Implementar**:
- Parseo JSON (no regex) de la salida del judge
- Deteccion de menciones de marca sin URL explicita
- Calculo de metricas basicas: total_citations, target_citations, is_visible, SoM, first_citation_rank
- Extraccion de contexto (+-50 chars) alrededor de cada mencion para sentiment posterior

---

### 1.5 Refactorizar firststep.ipynb en modulos

**Archivo**: `notebooks/experimental_run.ipynb` (nuevo)

**Acciones**:
1. Crear notebook limpio que importa desde `src/`
2. Mantener la estructura LangGraph de 6 nodos pero usando los nuevos modulos
3. Cada nodo llama a funciones de `src/` en vez de tener logica inline
4. El notebook solo orquesta: configuracion → ejecucion → guardado
5. Preservar `firststep.ipynb` original sin cambios

**Estructura del nuevo notebook**:
```python
# Cell 1: Imports y config
from src.processing.html_processor import StructuredWebLoader
from src.processing.chunker import HTMLAwareChunker
from src.rag.judge import RAGJudge
from src.rag.citation_extractor import CitationExtractor
# ...

# Cell 2: Cargar config
config = json.load(open("config/experiment_config.json"))

# Cell 3: Definir nodos LangGraph
# Cell 4: Construir grafo
# Cell 5: Ejecutar
# Cell 6: Guardar resultados
```

---

### 1.6 Implementar prompts del RAG Judge

**Ref. arquitectura**: Secciones 8.1, 18.2

**Archivo**: Actualizar `src/prompts/registry.py`

**Implementar**:
- `rag_judge.system`: Prompt completo con reglas de citacion JSON
- `rag_judge.user_template`: Template con `{context}` y `{question}`
- Documentar cada regla del prompt con justificacion (ref. a paper)

---

### 1.7 Context Builder para el RAG

**Archivo**: `src/rag/judge.py` (funcion auxiliar)

**Implementar**:
- Formateo del contexto recuperado para el judge
- Incluir URL, heading path y contenido de cada chunk
- Formato markdown estructurado:
  ```
  ## [Fuente 1: https://example.com]
  ### Seccion: Titulo
  Contenido del chunk...

  ## [Fuente 2: https://other.com]
  ...
  ```

---

## Criterios de Aceptacion

- [ ] `src/processing/chunker.py` produce chunks de ~1024 tokens (no caracteres)
- [ ] `src/processing/html_processor.py` extrae contenido estructurado de una URL real
- [ ] `src/rag/judge.py` produce salida JSON valida con citaciones parseables
- [ ] `src/rag/citation_extractor.py` extrae metricas de la salida JSON del judge
- [ ] `notebooks/experimental_run.ipynb` ejecuta el pipeline completo end-to-end
- [ ] `firststep.ipynb` original no ha sido modificado
- [ ] `src/prompts/registry.py` tiene el prompt del RAG judge completo y versionado
- [ ] El pipeline produce un `scorecard.json` basico por cada run
- [ ] Todos los modulos tienen imports funcionales (sin errores de importacion)

---

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Scraping de algunos sitios bloqueado | Implementar fallback con headers alternativos; documentar sitios inaccesibles |
| JSON mode de OpenAI genera JSON invalido | Implementar `json.loads()` con try/except y retry |
| Cambio en la API de OpenAI | Fijar version de `openai` en requirements.txt |
