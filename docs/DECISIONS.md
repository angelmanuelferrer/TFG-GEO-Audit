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

## ADR-009: Discovery con modelos web-grounded (no chat puro)

**Fecha**: 2026-02-16
**Estado**: Reemplazado por ADR-010

**Contexto**: El `CompetitorFinder` original usaba `ChatOpenAI` y `ChatGoogleGenerativeAI` como chat puro. Estos modelos NO tienen acceso a web — las URLs que citan son de memoria (training data) y pueden ser alucinadas o inexistentes. Esto invalida el descubrimiento de competidores porque no refleja lo que un usuario real obtendria al preguntar a un chatbot.

**Problema detectado**: El objetivo del discovery es replicar exactamente la experiencia de un usuario preguntando a un chatbot. Los modelos via API sin grounding no reproducen esa experiencia porque carecen de busqueda web.

**Decision**: Usar **Claude (Anthropic) con `web_search` tool** (`web_search_20250305`). La API de Anthropic ejecuta busquedas web reales del lado del servidor y devuelve URLs verificadas con citas estructuradas.

**Implementacion**:
- SDK: `anthropic` (directo, sin LangChain)
- Modelo: `claude-sonnet-4-5-20250929`
- Tool: `web_search_20250305` con `max_uses=5` por query
- Localizacion: `country=ES`, `timezone=Europe/Madrid`
- Extraccion de URLs: prioriza `citations` del web search (verificadas) sobre URLs en texto

**Justificacion**:
- Claude con web search busca en la web real y cita fuentes verificadas, no alucinadas.
- Las citas vienen estructuradas en la respuesta (`web_search_result_location`), no dependen de regex.
- El `user_location` permite localizar resultados a España, relevante para el caso de estudio.
- Coste: ~$10/1000 busquedas + tokens. Para 15 queries x ~3 busquedas = ~$0.45.

**Alternativa descartada**: Gemini con `google_search` tool + Perplexity API. Rechazado porque requiere mantener dos APIs distintas y Perplexity no ofrece el mismo nivel de control sobre las citas.

**Alternativa descartada**: Tavily (buscador web para agentes). Rechazado en ADR-004 porque busca en la web tradicional, no en motores generativos.

---

## ADR-010: Discovery con Gemini 2.5 Flash + Google Search Grounding

**Fecha**: 2026-03-07
**Estado**: Aprobado (reemplaza ADR-009)

**Contexto**: ADR-009 usaba Claude con `web_search` tool para el discovery. Esto costaba ~$0.45 por ejecucion (15 queries) y dependia de la API de Anthropic. Gemini 2.5 Flash ofrece Google Search grounding gratuito con el SDK nuevo (`google-genai`).

**Decision**: Migrar el discovery a **Gemini 2.5 Flash** con **Google Search grounding**. Usar el SDK nuevo `google-genai>=1` (el antiguo `google-generativeai` fue sunset en agosto 2025).

**Implementacion**:
- SDK: `google-genai` (nuevo, reemplaza `google-generativeai`)
- Modelo: `gemini-2.5-flash`
- Tool: `GoogleSearch()` via `GenerateContentConfig`
- Extraccion de URLs: `grounding_metadata.grounding_chunks[].web.uri` (search URLs) + `grounding_supports[].grounding_chunk_indices` resueltos a chunks (citation URLs, weight=2)
- Rate limiting: 2s delay (Gemini free tier = 15 RPM)

**Justificacion**:
- Coste $0 (Google Search grounding es gratuito en Gemini API).
- Google Search grounding usa el mismo indice que Google Search real, resultados mas relevantes.
- El SDK nuevo es el unico soportado oficialmente desde agosto 2025.
- Las URLs de grounding_metadata son verificadas (vienen del indice de Google).

**Alternativa descartada**: Mantener Claude con web_search. Rechazado por coste ($0.45/ejecucion) cuando Gemini ofrece lo mismo gratis.

---

## ADR-011: Chunking SAGEO Arena (256 tokens, 64 overlap)

**Fecha**: 2026-03-07
**Estado**: Aprobado (actualiza ADR-001)

**Contexto**: ADR-001 establecio chunks de 1024 tokens basandose en Chen et al. (2025). Sin embargo, los motores generativos reales usan ventanas mas pequenias (~200-377 palabras segun analisis de BrightEdge). SAGEO Arena, el benchmark de referencia para evaluacion GEO, usa 256 tokens con 64 de overlap.

**Decision**: Reducir chunking a **256 tokens** con **64 tokens de overlap** para ambos perfiles (default y FAQ). Alineado con SAGEO Arena.

**Justificacion**:
- SAGEO Arena (benchmark de referencia) usa exactamente 256/64.
- Motores reales (Perplexity, ChatGPT con search) procesan fragmentos cortos, no paginas enteras.
- Chunks mas pequenios = mas granularidad en citaciones = metricas GEO mas discriminativas.
- Compatible con nuestro top_k=5: 5 chunks x 256 tokens = ~1280 tokens de contexto, bien dentro del presupuesto.

**Impacto**: Invalida el vectorstore congelado existente. Requiere re-ejecutar `00_discover_competitors.ipynb`.

**Alternativa descartada**: 512 tokens (punto medio). Rechazado porque no se alinea con el benchmark de referencia.

---

## ADR-012: RAG Judge con Gemini 2.5 Flash + agente de busqueda

**Fecha**: 2026-03-07
**Estado**: Aprobado (actualiza ADR-002)

**Contexto**: El RAG Judge usaba GPT-4o con chunks pre-recuperados. Esto no replica como funciona un motor generativo real, donde el modelo decide que buscar y puede reformular queries.

**Decision**: Migrar a **Gemini 2.5 Flash** y convertir el judge en un **agente con herramienta de busqueda FAISS**. El LLM no sabe que busca en FAISS — cree que tiene un buscador web. Puede hacer 1-5 busquedas con queries que el mismo formula.

**Implementacion**:
- Modelo: `gemini-2.5-flash` via `langchain-google-genai`
- Modo: agente con `create_tool_calling_agent` de LangChain
- Tool: `search()` que wrappea FAISS retriever, devuelve chunks formateados
- `max_iterations=5` (el agente puede buscar varias veces)
- Fallback: modo `classic` (pre-retrieval) sigue disponible via config

**Justificacion**:
1. **Coste ~10x menor**: Gemini 2.5 Flash vs GPT-4o.
2. **Pipeline mas realista**: el agente reformula queries como un motor real.
3. **Reproducibilidad**: `temperature=0.0` (sin seed, Gemini no lo soporta).
4. **Flexibilidad**: el agente puede buscar multiples veces si la primera busqueda no es suficiente.

**Alternativa descartada**: Mantener GPT-4o. Rechazado por coste excesivo para un TFG (~$0.50/run de 15 queries).

---

## ADR-013: Expansion a 100 queries con sistema de rotacion

**Fecha**: 2026-03-07
**Estado**: Aprobado

**Contexto**: El set original de 15 queries era insuficiente para analisis estadisticamente significativos y cubria pocos subtemas del dominio (programacion educativa infantil en Espana).

**Decision**: Expandir a **100 queries** (35 informacionales + 35 comparativas + 30 navegacionales) con sistema de rotacion:
- **Core 20**: se ejecutan en TODOS los runs (incluye las 15 originales + 5 nuevas).
- **4 bloques rotativos** (R1-R4): 20 queries cada uno, se ejecuta 1 bloque por run.
- Cada run ejecuta 40 queries (20 core + 20 rotativas).

**Formato v2** de `queries.json`: cada query tiene ID unico (`Q001`-`Q100`), categoria, y flag `original_15`.

**Justificacion**:
- 100 queries cubren mas subtemas: robotica, STEAM, IA, inclusividad, formacion docente, etc.
- La rotacion permite cubrir los 100 en 4 runs sin sobrecargar un solo run.
- Las 20 core garantizan comparabilidad longitudinal entre runs.
- Las 15 originales siempre se ejecutan (estan en core), preservando serie temporal.

**Alternativa descartada**: Ejecutar las 100 en cada run. Rechazado por coste y tiempo de ejecucion (~2.5h con 100 queries x Gemini rate limits).

---

## ADR-014: Kaggle como endpoint remoto de GPU + scripts locales

**Fecha**: 2026-03-18
**Estado**: Aprobado (actualiza ADR-008)

**Contexto**: ADR-008 establecia que toda la ejecucion se hacia en Kaggle (clonar repo, instalar deps, ejecutar notebooks). Sin embargo, la unica operacion que necesita GPU es `create_embeddings()` (multilingual-e5-large, ~1.2GB). Todo lo demas (Gemini API, scraping, chunking, FAISS, metricas) es CPU o llamadas API que pueden ejecutarse localmente.

Ejecutar todo en Kaggle tiene desventajas:
- Sesiones limitadas a 12h con reinicio de estado.
- No se puede automatizar con cron ni CI/CD.
- La interfaz de notebooks dificulta debugging y logging.

**Decision**: Separar la GPU del resto del pipeline:
1. **Kaggle solo sirve embeddings**: Un notebook (`kaggle_gpu_server.ipynb`) carga `multilingual-e5-large` en GPU y expone un endpoint HTTP (`POST /embed`) via localtunnel. Auth con Bearer token.
2. **Scripts locales**: `scripts/run_discovery.py` y `scripts/run_experimental.py` automatizan el pipeline completo por terminal, usando `RemoteEmbeddings` para llamar al servidor de Kaggle.
3. **Notebooks intactos**: Los notebooks originales (`00_discover_competitors.ipynb`, `experimental_run.ipynb`) se mantienen para trazabilidad y referencia.

**Implementacion**:
- `src/processing/remote_embeddings.py`: Clase `RemoteEmbeddings` que implementa `langchain_core.embeddings.Embeddings` via HTTP POST con retry y batching.
- `src/processing/embeddings.py`: Simplificado para devolver siempre `RemoteEmbeddings`.
- `notebooks/kaggle_gpu_server.ipynb`: Flask server + localtunnel en 4 celdas.
- `scripts/run_discovery.py`: Pipeline completo de discovery (equivalente al notebook).
- `scripts/run_experimental.py`: Pipeline completo experimental (equivalente al notebook).

**Justificacion**:
- La GPU solo se necesita para embeddings (~5% del tiempo de ejecucion). El resto son llamadas API o CPU.
- Localtunnel expone el servidor de Kaggle sin configuracion de red.
- Los scripts son mas faciles de automatizar, debuggear y versionar que notebooks.
- `RemoteEmbeddings` es un drop-in compatible con LangChain (misma interfaz que `HuggingFaceEmbeddings`).

**Alternativa descartada**: Serverless GPU (Modal, RunPod). Rechazado por coste y complejidad para un TFG. Kaggle es gratuito.

**Alternativa descartada**: OpenAI embeddings como unico proveedor. Rechazado por ADR-003: coste recurrente y dimensiones diferentes (1536 vs 1024) invalidarian el vectorstore congelado.

---

## ADR-015: Metricas GEO adaptadas al tipo de sitio web (modo plataforma)

**Fecha**: 2026-03-23
**Estado**: Aprobado (diseño para modo plataforma)

**Contexto**: Las metricas GEO actuales (visibility rate, Share of Mind, citation count) se tratan de forma uniforme para todos los sitios. Sin embargo, no todos los tipos de sitio web necesitan optimizar las mismas metricas. Una tienda online necesita aparecer en listas de "mejores X", mientras que un articulo cientifico necesita ser citado como fuente de autoridad. Programamos.es, como plataforma educativa, necesita visibilidad y recomendacion como recurso.

**Decision**: En el **modo plataforma** (extension futura), el sistema clasificara automaticamente el tipo de sitio web tras el crawling y priorizara las metricas GEO relevantes. La clasificacion la hara el LLM analizando el contenido crawleado.

**Taxonomia de tipos y metricas prioritarias**:

| Tipo de sitio | Metricas prioritarias | Justificacion |
|---|---|---|
| **E-commerce / tienda** | Posicion en lista, citation count | Aparicion en rankings "top N mejores X" |
| **Academico / cientifico** | Authority citation, cita textual | Ser referenciado como fuente fiable |
| **Educativo / formativo** | Visibility rate, Share of Mind | Ser recomendado como recurso de aprendizaje |
| **SaaS / herramienta** | Citation con enlace, recomendacion directa | Ser sugerido como solucion a un problema |
| **Blog / medio de comunicacion** | Frecuencia de cita, recencia | Ser citado para informacion actualizada |
| **Institucional / ONG** | Visibilidad, autoridad tematica | Ser reconocido como referente en su ambito |

**Flujo en modo plataforma**:
1. Usuario introduce URL de su sitio.
2. `SiteCrawler` scrapea el contenido.
3. LLM clasifica el tipo de sitio a partir del contenido.
4. El sistema prioriza y pondera metricas segun la taxonomia.
5. El dashboard muestra las metricas relevantes destacadas y recomendaciones adaptadas.

**Alcance**: Solo modo plataforma. El modo experimental (TFG) usa las metricas uniformes actuales con Programamos.es (tipo: educativo).

**Justificacion**:
- Hace el sistema util para cualquier tipo de web, no solo educativas.
- Las recomendaciones de optimizacion son mas accionables si estan contextualizadas al tipo de negocio.
- Diferenciador respecto a herramientas GEO genericas que tratan todas las metricas por igual.

**Alternativa descartada**: Dejar que el usuario elija manualmente su tipo de sitio. Rechazado como opcion unica porque muchos usuarios no sabrian clasificarse. Se ofrecera como override si la clasificacion automatica no es correcta.

---

## ADR-016: Migración de embeddings a Google text-embedding-004 (API)

**Fecha**: 2026-04-04
**Estado**: Aprobado (reemplaza ADR-014 en lo relativo a embeddings)

**Contexto**: ADR-014 establecía Kaggle GPU como servidor remoto de embeddings via localtunnel/serveo. En la práctica, los tunnels SSH disponibles (ngrok, localtunnel, serveo) resultaron bloqueados o inestables en el entorno de desarrollo, haciendo inviable el flujo de trabajo. Cada ejecución requería levantar manualmente el servidor en Kaggle, obtener la URL del tunnel y configurar las variables de entorno.

**Decision**: Sustituir `RemoteEmbeddings` (HTTP a Kaggle) por `GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")` de `langchain-google-genai`. La ejecución pasa a ser 100% local sin dependencias de GPU.

**Implementacion**:
- `src/processing/embeddings.py`: `create_embeddings()` devuelve `GoogleGenerativeAIEmbeddings` con `task_type="retrieval_document"`. `embed_query()` usa automáticamente `task_type="retrieval_query"`.
- `config/experiment_config.json`: modelo actualizado a `models/text-embedding-004`, dimensiones 768 (vs 1024 anterior), provider `google`.
- `GOOGLE_API_KEY` ya existía en `.env` para Gemini — cero variables nuevas.
- Variables eliminadas: `EMBEDDING_SERVER_URL`, `EMBEDDING_SERVER_TOKEN`.

**Consecuencia operativa**: El vectorstore congelado existente queda invalidado (dimensiones incompatibles: 1024 → 768). Se debe ejecutar `scripts/run_discovery.py` desde cero para regenerar el vectorstore con el nuevo modelo.

**Justificacion**:
- Elimina la dependencia de GPU y de tunneling completamente.
- `text-embedding-004` tiene soporte multilingüe nativo (español incluido) y rendimiento comparable a `multilingual-e5-large` en benchmarks de retrieval semántico.
- `GOOGLE_API_KEY` ya estaba presente: cero coste de configuración adicional.
- A la escala del TFG (discovery one-time ~200k tokens, target por run ~50k tokens), el coste de API es de céntimos.
- `GoogleGenerativeAIEmbeddings` es drop-in compatible con la interfaz `langchain_core.embeddings.Embeddings` — los scripts no cambian.

**Alternativa descartada**: Google Colab con Cloudflare tunnel. Mejora la situación de tunneling respecto a Kaggle pero no la elimina: sesiones limitadas (~90 min inactivo), infraestructura adicional que mantener.

**Alternativa descartada**: OpenAI `text-embedding-3-small`. Requeriría `OPENAI_API_KEY` adicional. Google ya cubre el stack completo (Gemini discovery + RAG Judge + embeddings).

---

## Indice de decisiones

| ADR | Titulo | Estado |
|-----|--------|--------|
| 001 | Chunking basado en tokens | Actualizado por ADR-011 |
| 002 | JSON estructurado del RAG Judge | Actualizado por ADR-012 |
| 003 | Embeddings locales con fallback | Actualizado por ADR-014 |
| 004 | Competidores desde LLMs reales | Aprobado |
| 005 | FAISS local para vectorstore | Aprobado |
| 006 | Separacion discovery vs runs | Aprobado |
| 007 | Procesamiento HTML-aware | Aprobado |
| 008 | Ejecucion Kaggle, desarrollo local | Actualizado por ADR-014 |
| 009 | Discovery con modelos web-grounded (Anthropic) | Reemplazado por ADR-010 |
| 010 | Discovery con Gemini 2.5 Flash + Google Search | Aprobado |
| 011 | Chunking SAGEO Arena (256/64) | Aprobado |
| 012 | RAG Judge Gemini + agente de busqueda | Aprobado |
| 013 | Expansion a 100 queries con rotacion | Aprobado |
| 014 | Kaggle como endpoint remoto de GPU | Aprobado |
| 015 | Metricas GEO adaptadas al tipo de sitio | Aprobado (modo plataforma) |
| 016 | Embeddings Google text-embedding-004 (API) | Aprobado (reemplaza ADR-014 embeddings) |
