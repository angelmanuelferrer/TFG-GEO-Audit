# Registro de Decisiones Tecnicas (ADR)

Documento vivo con todas las decisiones de diseño del sistema GEO-Audit, sus justificaciones y alternativas descartadas.

---

## ADR-001: Chunking basado en tokens (no caracteres)

**Fecha**: 2026-02-14
**Estado**: Aprobado

**Contexto**: El prototipo `firststep.ipynb` usa `RecursiveCharacterTextSplitter` con `chunk_size=1000` caracteres (~200-250 tokens). La literatura (Chen et al., 2025) recomienda 512-1024 tokens para RAG.

**Decision**: Usar tiktoken (`cl100k_base`) como `length_function` en el splitter. Default 1024 tokens, FAQ 256 tokens.

**Justificacion**: Los modelos procesan tokens, no caracteres. Un chunk de 1000 caracteres puede tener 200 o 400 tokens dependiendo del idioma, generando inconsistencias.

**Alternativa descartada**: Mantener caracteres con un factor de conversion (x4). Rechazado por impreciso.

---

## ADR-002: Salida JSON estructurada del RAG Judge (no regex)

**Fecha**: 2026-02-14
**Estado**: Aprobado

**Contexto**: El prototipo extrae citas con `re.findall(r'\[Fuente: (.*?)\]', ans)`. Si el LLM varia el formato ("Fuente:", "Source:", sin corchetes), el regex falla silenciosamente.

**Decision**: Usar `response_format={"type": "json_object"}` de OpenAI con un schema explicito:
```json
{
  "answer": "Respuesta con citas [1] [2]...",
  "citations": [{"index": 1, "url": "...", "quote": "cita exacta"}],
  "sources_used": ["url1"],
  "sources_available_but_unused": ["url2"]
}
```

**Justificacion**: JSON mode de OpenAI garantiza salida parseable. El schema explicito permite calcular metricas GEO directamente sin parseo fragil.

**Alternativa descartada**: Mejorar el regex con multiples patrones. Rechazado: sigue siendo fragil y dificil de mantener.

---

## ADR-003: Embeddings locales (multilingual-e5-large) con fallback OpenAI

**Fecha**: 2026-02-14
**Estado**: Aprobado

**Contexto**: El prototipo usa `OpenAIEmbeddings(model="text-embedding-3-small")`. Esto cuesta tokens por cada ejecucion y crea dependencia de API.

**Decision**: Usar `intfloat/multilingual-e5-large` (1024 dimensiones) como embedding primario en Kaggle (GPU). Fallback a OpenAI `text-embedding-3-small` (1536d) si no hay GPU disponible.

**Justificacion**:
- El modelo E5-large es SOTA para embeddings multilingues y es gratuito.
- Kaggle provee GPUs T4/P100 suficientes para este modelo (~1.2GB).
- El fallback garantiza que el pipeline funciona tambien en local sin GPU.
- Una vez elegido el modelo de embeddings, se congela para todo el experimento (los vectores no son compatibles entre modelos distintos).

**Restriccion critica**: El modelo de embeddings NO puede cambiar entre runs experimentales. Si se cambia, hay que regenerar todos los vectores (incluido el vectorstore congelado de competidores).

**Alternativa descartada**: Usar solo OpenAI. Rechazado por coste recurrente y dependencia externa para un TFG.

---

## ADR-004: Competidores descubiertos desde LLMs reales (no predefinidos)

**Fecha**: 2026-02-14
**Estado**: Aprobado

**Contexto**: El config tenia una lista fija de dominios competidores (code.org, scratch.mit.edu, etc.), pero estos fueron elegidos manualmente. No sabemos si realmente son los que los motores generativos citan.

**Decision**: Ejecutar las 15 queries experimentales contra ChatGPT y Gemini reales UNA vez. Extraer las URLs que citan en sus respuestas. Esas URLs = competidores reales con buen GEO actual.

**Justificacion**:
- Los competidores descubiertos son los que realmente aparecen en motores generativos, no los que nosotros creemos que deberian aparecer.
- Esto hace que el benchmark sea realista: programamos.es compite contra las fuentes que los LLMs ya conocen y citan.
- Los competidores se congelan tras el discovery para mantener control experimental.

**Alternativa descartada**: Lista manual de competidores. Rechazada por sesgo de seleccion: podriamos incluir competidores que los LLMs nunca citan.

**Alternativa descartada**: Busqueda con Tavily por query. Rechazada porque Tavily busca en la web, no en motores generativos. Lo que aparece en Google no es lo mismo que lo que cita ChatGPT.

---

## ADR-005: Vectorstore congelado con FAISS local (no cloud)

**Fecha**: 2026-02-14
**Estado**: Aprobado

**Contexto**: El vectorstore de competidores debe ser accesible desde Kaggle en cada run experimental. Opciones: FAISS local, Pinecone, Qdrant Cloud.

**Decision**: FAISS local. El indice se guarda como archivos (`.faiss` + `.pkl`, ~5-20MB) en `data/frozen_vectorstore/` dentro del repo.

**Justificacion**:
- Sin dependencias externas ni API keys adicionales.
- 100% reproducible: el mismo archivo produce los mismos resultados.
- El tamanio es pequenio (<20MB para ~100 documentos chunkeados).
- Accesible directamente en Kaggle al clonar el repo.
- FAISS es suficiente para <10K documentos (busqueda exacta, no hace falta HNSW).

**Alternativa descartada**: Pinecone/Qdrant Cloud. Rechazados porque anadian dependencia externa y punto de fallo para un proyecto academico. El free tier podria expirar o cambiar condiciones.

---

## ADR-006: Separacion discovery (una vez) vs experimental runs (N veces)

**Fecha**: 2026-02-14
**Estado**: Aprobado

**Contexto**: El prototipo ejecutaba el discovery de competidores en cada run, generando competidores distintos cada vez. Esto invalida el diseno experimental porque la variable "competidores" cambia.

**Decision**: Dos notebooks separados:
1. `00_discover_competitors.ipynb` — se ejecuta UNA vez. Descubre competidores, scrapea, genera embeddings, congela vectorstore.
2. `experimental_run.ipynb` — se ejecuta N veces. Carga vectorstore congelado, solo re-embedea programamos.es, ejecuta el RAG judge.

**Justificacion**: Diseno experimental riguroso. La unica variable que cambia entre runs es el contenido de programamos.es. Todo lo demas (queries, competidores, vectores de competidores, modelo judge, parametros) permanece congelado.

**Flujo**:
```
[UNA VEZ]  15 queries → ChatGPT/Gemini → URLs citadas → Scrape → Embed → Congelar FAISS

[CADA RUN] Scrape programamos.es → Chunk → Embed → Merge con FAISS congelado →
           Para cada query: Retrieve → RAG Judge (JSON) → Metricas GEO → Scorecard
```

---

## ADR-007: Procesamiento HTML-aware (no WebBaseLoader crudo)

**Fecha**: 2026-02-14
**Estado**: Aprobado

**Contexto**: El prototipo usa `WebBaseLoader` de LangChain que devuelve todo el texto de la pagina incluyendo navegacion, footer, scripts, etc. Esto contamina los chunks con contenido irrelevante.

**Decision**: Implementar `StructuredWebLoader` propio que:
1. Descarga HTML con retry (backoff exponencial, max 3 intentos, timeout 10s)
2. Elimina ruido: `<nav>`, `<footer>`, `<script>`, `<style>`, `<aside>`
3. Extrae contenido principal: `<main>` o `<article>`, fallback al div mas grande
4. Convierte a markdown preservando h1-h4, listas, parrafos
5. Extrae metadata: title, meta description, JSON-LD schema.org

**Justificacion**: La calidad del RAG depende directamente de la calidad de los chunks. Un chunk que mezcla contenido de navegacion con contenido real degrada la recuperacion.

---

## ADR-008: Ejecucion en Kaggle, desarrollo en local

**Fecha**: 2026-02-14
**Estado**: Aprobado

**Contexto**: Los embeddings locales requieren GPU. El desarrollo se hace en GitHub Codespaces/local.

**Decision**:
- **Desarrollo y versionado**: En este repositorio (GitHub).
- **Ejecucion computacional**: En Kaggle (GPUs T4/P100 gratuitas).
- **CI/CD (GitHub Actions)**: Solo para metricas SEO diarias y consultas live a LLMs (no necesitan GPU ni embeddings).

**Justificacion**: Kaggle ofrece GPUs gratuitas suficientes para embeddings y no requiere setup de infraestructura. GitHub Actions no tiene GPU pero no la necesita para sus tareas.

---

## Indice de decisiones

| ADR | Titulo | Estado |
|-----|--------|--------|
| 001 | Chunking basado en tokens | Aprobado |
| 002 | JSON estructurado del RAG Judge | Aprobado |
| 003 | Embeddings locales con fallback | Aprobado |
| 004 | Competidores desde LLMs reales | Aprobado |
| 005 | FAISS local para vectorstore | Aprobado |
| 006 | Separacion discovery vs runs | Aprobado |
| 007 | Procesamiento HTML-aware | Aprobado |
| 008 | Ejecucion Kaggle, desarrollo local | Aprobado |
