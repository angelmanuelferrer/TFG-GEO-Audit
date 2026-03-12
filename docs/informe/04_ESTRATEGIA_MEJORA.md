# Estrategia de Mejora

> **Versión**: 1.0 | **Última actualización**: Marzo 2026
> Este documento describe la estrategia de optimización dual: SEO (cimientos técnicos) + GEO (optimización de contenido para motores de IA).

---

## 1. Dos frentes complementarios

La visibilidad en motores de IA depende de dos etapas secuenciales:

1. **SEO** — Que el motor de IA pueda encontrar y acceder a tu contenido (retrieval).
2. **GEO** — Que el motor de IA decida citar tu contenido en su respuesta (generation).

**Analogía**: El SEO es conseguir que la biblioteca tenga tu libro en su catálogo. El GEO es conseguir que el bibliotecario lo recomiende cuando alguien pregunta.

```
SEO (cimientos)                    GEO (contenido)
─────────────────                  ──────────────────
Robots.txt limpio                  Estadísticas citables
Sitemap XML                        Párrafos auto-contenidos
HTML semántico                     Baja perplejidad
Schema.org JSON-LD                 Referencias a fuentes autoritativas
Performance (LCP, TBT)            Definiciones explícitas
Accesibilidad                      Estructura clara H1→H6

"Que me encuentren"               "Que me recomienden"
```

Ambos frentes se trabajan en fases secuenciales, midiendo el impacto de cada intervención.

---

## 2. Fase 1 — SEO con MARTE

### 2.1. Qué es MARTE

MARTE es una herramienta desarrollada por el director del TFG que genera sitios web con HTML optimizado, responsive, y orientado a rendimiento. Se utilizará para reconstruir la web de Programamos con una base técnica sólida.

### 2.2. Qué aporta MARTE

| Aspecto | Estado actual | Con MARTE |
|---------|--------------|-----------|
| HTML semántico | Variable | HTML5 con tags semánticos (article, section, nav, aside) |
| Responsive | Parcial | Mobile-first, adaptativo |
| Performance | Medible (Lighthouse) | Optimizado para Core Web Vitals |
| Estructura | Inconsistente | Headers jerárquicos H1→H6 |

### 2.3. Cómo medimos el impacto

**Antes (baseline)**:
- Ejecutar 3 runs experimentales completos
- Registrar métricas Live de la semana
- Capturar Lighthouse scores (ya recolectados diariamente)

**Después (post-MARTE)**:
- Ejecutar 3 runs experimentales con la web nueva
- Registrar métricas Live
- Capturar nuevos Lighthouse scores

**Métricas a comparar**:

| Métrica | Tipo | Expectativa |
|---------|------|------------|
| Lighthouse Performance | SEO | Mejora significativa |
| Lighthouse SEO | SEO | Mejora significativa |
| Lighthouse Accessibility | SEO | Mejora |
| LCP / TBT | SEO | Reducción |
| Visibilidad experimental | GEO | Posible mejora leve (mejor HTML → mejor retrieval simulado) |
| Visibilidad Live | GEO | Posible mejora (mejor indexación → más retrieval en motores reales) |

**Nota**: MARTE mejora los cimientos, no el contenido. El impacto en métricas GEO experimentales puede ser limitado (el simulador ya recupera el contenido). El impacto Live puede ser mayor si la mejora técnica facilita la indexación por motores reales.

---

## 3. Fase 2 — GEO puro

Cinco vectores de optimización respaldados por la [evidencia académica](05_EVIDENCIA.md):

### 3.1. Machine Scannability

> **Paper**: Chen et al. (2025) — *SEO vs. GEO*

**Concepto**: Facilitar que los motores de IA puedan "escanear" y comprender la estructura del contenido.

**Técnicas**:

| Técnica | Implementación | Ejemplo |
|---------|---------------|---------|
| HTML5 semántico | `<article>`, `<section>`, `<aside>` | Cada sección temática en su propio `<section>` |
| Headers jerárquicos | H1 → H2 → H3, sin saltos | Un solo H1 por página, H2 para secciones, H3 para subsecciones |
| Schema.org JSON-LD | Datos estructurados en `<head>` | `Organization`, `EducationalOrganization`, `Course`, `FAQPage` |
| Tablas para datos | `<table>` con `<thead>` y `<tbody>` | Tabla de talleres, tabla de niveles por edad |
| Listas estructuradas | `<ul>`, `<ol>` para enumeraciones | Lista de tecnologías enseñadas, lista de sedes |

**Impacto esperado**: Los LLMs procesan HTML internamente (HtmlRAG, Tan et al. 2024). Una estructura clara facilita la extracción de información y aumenta la probabilidad de citación.

### 3.2. Citation Readiness

> **Paper**: Aggarwal et al. (2023) — *GEO: Generative Engine Optimization* (+55-85% visibilidad)

**Concepto**: Hacer que el contenido sea fácil de citar literalmente. Un LLM cita cuando encuentra un fragmento que responde directamente a la pregunta del usuario.

**Técnicas**:

| Técnica | Implementación | Ejemplo |
|---------|---------------|---------|
| Estadísticas concretas | Datos numéricos con fuente | "Más de 3.500 jóvenes han participado en talleres de Programamos desde 2013 (datos propios, 2025)" |
| Párrafos auto-contenidos | Cada párrafo comprensible sin contexto | "Programamos es una asociación sin ánimo de lucro fundada en 2013 que enseña programación y pensamiento computacional a jóvenes de 6 a 18 años en España." |
| Fechas y datos verificables | Información temporal concreta | "En el curso 2024-2025, Programamos opera en 8 provincias de Andalucía" |
| Citas a estudios | Referencias a investigación | "Según el informe PISA 2023, las competencias digitales..." |
| Definiciones explícitas | Formato "X es Y que Z" | "Scratch es un lenguaje de programación visual desarrollado por el MIT..." |

**Chunk-Aligned Writing**: Además de ser auto-contenidos, los párrafos deben diseñarse para caber dentro de un chunk de retrieval (~256 tokens ≈ 190 palabras). Si una estadística clave o una definición se parte entre dos chunks, es menos probable que el LLM la recupere completa y la cite. Regla práctica: cada unidad citable (dato + contexto + fuente) debería ocupar un solo párrafo de 150-200 palabras máximo. Esto es especialmente relevante porque nuestro chunking usa separadores jerárquicos (`\n## `, `\n### `, `\n\n`) — si cada sección H3 contiene 1-2 párrafos auto-contenidos, cada chunk será una unidad citable completa.

**Impacto esperado**: Los fragmentos auto-contenidos con datos concretos son los que los LLMs seleccionan para citar. Sin estadísticas ni datos verificables, el contenido es "descriptivo pero no citable". El alineamiento con el tamaño de chunk maximiza la probabilidad de que cada unidad citable sea recuperada intacta.

### 3.3. Low Perplexity

> **Paper**: Lijia et al. (2025) — *Low Perplexity and GEO* (+20-35% citabilidad)

**Concepto**: Escribir de forma clara y predecible. Los LLMs asignan mayor probabilidad a textos con baja perplejidad (textos donde cada palabra es la esperada dado el contexto).

**Técnicas**:

| Técnica | Implementación | Contra-ejemplo |
|---------|---------------|----------------|
| Estructura SVO | Sujeto-Verbo-Objeto directo | Evitar: "Es en el contexto de la transformación digital donde..." |
| Topic sentences | Primera frase resume el párrafo | Evitar: párrafos que revelan su punto al final |
| Vocabulario consistente | Mismo término para mismo concepto | Evitar: alternar entre "taller", "workshop", "sesión formativa" |
| Frases cortas-medias | 15-25 palabras por frase | Evitar: frases de 50+ palabras con subordinadas |
| Voz activa | "Programamos enseña..." | Evitar: "La programación es enseñada por..." |

**Impacto esperado**: Los textos con baja perplejidad son más fáciles de procesar para el LLM y más probables de ser seleccionados como cita. No se trata de simplificar — se trata de clarificar.

### 3.4. Authority Signals

> **Papers**: Chen & Wu (2025), Aggarwal et al. (2023) (+30-40% visibilidad)

**Concepto**: Señalar que Programamos es una fuente autoritativa y confiable. Los LLMs muestran sesgo hacia fuentes con señales de autoridad.

**Técnicas**:

| Técnica | Implementación | Ejemplo |
|---------|---------------|---------|
| Referencias a instituciones | Mencionar colaboraciones | "En colaboración con la Universidad de Málaga..." |
| Datos oficiales | Citar fuentes gubernamentales | "Según datos del INTEF (Instituto Nacional de Tecnologías Educativas)..." |
| Reconocimientos | Premios y distinciones | "Premio Nacional de Innovación Educativa 20XX" |
| Presencia en medios | Menciones en prensa | "Como informó El País en marzo de 2025..." |
| Backlinks implícitos | Referencias recíprocas | Que Wikipedia, INTEF u otras instituciones enlacen a Programamos |

**Impacto esperado**: Los LLMs ponderan la autoridad percibida de las fuentes. Incluir señales explícitas de autoridad en el contenido aumenta la probabilidad de ser citado frente a competidores sin estas señales.

### 3.5. Bot Accessibility

> **Paper**: Chen et al. (2025) — Prerequisito SEO para GEO

**Concepto**: Asegurar que los crawlers de los motores de IA pueden acceder y procesar el contenido correctamente.

**Técnicas**:

| Técnica | Implementación | Verificación |
|---------|---------------|-------------|
| robots.txt limpio | Permitir GPTBot, ClaudeBot, PerplexityBot | Análisis del robots.txt actual |
| Sitemap XML | Incluir todas las páginas relevantes | Validar con Google Search Console |
| HTML bajo ruido | Ratio contenido/HTML alto | Eliminar JS innecesario, CSS inline |
| Tiempos de respuesta | TTFB < 500ms | PageSpeed API |
| SSL/HTTPS | Certificado válido | Verificación automática |
| `llms.txt` | Archivo markdown en raíz del sitio con info estructurada para LLMs | Verificar acceso en `/llms.txt` |

#### `llms.txt` — Información estructurada para LLMs

Propuesta emergente (Jeremy Howard, fast.ai, 2024): un archivo markdown en la raíz del sitio (`/llms.txt`) que proporciona a los motores de IA un resumen estructurado del sitio optimizado para su consumo. Contenido típico:

- Descripción del sitio y su misión
- Datos clave (año fundación, ámbito, cifras)
- Preguntas frecuentes en formato Q&A
- Enlaces a las páginas más importantes
- Información de contacto y autoría

**Estado actual**: No es un estándar oficial. Algunos sitios lo implementan (fast.ai, varios proyectos open source) y hay señales de que crawlers como PerplexityBot empiezan a buscarlo. Los motores principales (GPTBot, GoogleBot) aún no lo leen de forma documentada.

**Por qué incluirlo**: El coste de crearlo es prácticamente cero (un archivo markdown). Si/cuando los motores empiecen a leerlo, Programamos ya lo tendría. Y podemos medir su impacto: añadirlo como intervención y comparar visibilidad Live antes/después. Además, demuestra visión de futuro en el TFG — anticiparse a un posible estándar emergente.

**Implementación para Programamos**: Un archivo `llms.txt` en la raíz con: misión de la organización, cifras de impacto, tecnologías enseñadas, ámbito geográfico, colaboraciones institucionales, y links a páginas principales. Formato markdown limpio, sin HTML, optimizado para baja perplejidad.

**Estudio experimental con RAG**: Más allá de esperar a que los motores lo lean en producción, podemos estudiar el efecto del `llms.txt` ya con nuestro simulador. Si incluimos el contenido del `llms.txt` como un documento adicional en el vectorstore FAISS, podemos medir si su presencia mejora las métricas GEO. Un `llms.txt` bien escrito — con párrafos auto-contenidos, estadísticas, baja perplejidad — es esencialmente un documento diseñado para ser el chunk perfecto. Es un candidato ideal para obtener Citation Rate alto. Esto nos permite anticipar qué pasará cuando los motores empiecen a vectorizarlo e indexarlo: si funciona bien en nuestro RAG simulado, funcionará bien cuando los LLMs lo procesen en producción. Es una línea de estudio interesante para el TFG con coste cero adicional.

**Impacto esperado**: Es un prerequisito, no una optimización directa. Sin accesibilidad para bots, ninguna otra optimización GEO tiene efecto en motores reales. Su impacto se mide principalmente en el Live, no en el experimental. El `llms.txt` es una apuesta de futuro con coste marginal cero, y su estudio en RAG simulado puede aportar evidencia anticipada de su valor.

---

## 4. Protocolo de intervención

### 4.1. Secuencia de fases

```
Fase 0: BASELINE
  │  3 runs experimentales + 1 semana Live
  │  Métricas SEO diarias
  │
  ▼
Fase 1: SEO (MARTE)
  │  Implementar nueva web con MARTE
  │  3 runs experimentales + 1 semana Live
  │  Comparar Lighthouse before/after
  │
  ▼
Fase 2: MACHINE SCANNABILITY
  │  Schema.org JSON-LD + HTML semántico
  │  3 runs experimentales + 1 semana Live
  │
  ▼
Fase 3: CITATION READINESS
  │  Estadísticas, párrafos auto-contenidos
  │  3 runs experimentales + 1 semana Live
  │
  ▼
Fase 4: LOW PERPLEXITY + AUTHORITY
  │  Reescritura clara + señales de autoridad
  │  3 runs experimentales + 1 semana Live
  │
  ▼
ANÁLISIS FINAL
   Correlación experimental-Live
   Delta acumulado por fase
   Informe de resultados
```

### 4.2. Por qué este orden

1. **MARTE primero** (Fase 1): Establece los cimientos técnicos. Sin buena estructura HTML, las optimizaciones de contenido GEO son menos efectivas.
2. **Machine Scannability** (Fase 2): Trabaja sobre la estructura que MARTE proporciona. Schema.org y headers jerárquicos son incrementales sobre buen HTML.
3. **Citation Readiness** (Fase 3): Trabaja sobre el contenido. Requiere que la estructura ya sea buena.
4. **Low Perplexity + Authority** (Fase 4): Refinamiento final del contenido. Combinadas porque son técnicas de reescritura que se aplican mejor juntas.

### 4.3. Medición por fase

Cada fase genera:
- **3 runs experimentales**: Para calcular mediana y variabilidad intra-fase
- **1 semana de Live**: Para validar con motores reales
- **Métricas SEO diarias**: Para controlar confounding

El **delta** se calcula respecto a la fase anterior (no respecto al baseline original):

$$\Delta_{\text{fase}} = \text{mediana}_{\text{fase}} - \text{mediana}_{\text{fase anterior}}$$

Esto permite atribuir cada mejora a la intervención correspondiente.

---

## 5. Generador de páginas

### 5.1. Dos modos de generación

El sistema incluye un generador de páginas optimizadas para GEO con dos modos:

| Modo | Input | Output | Uso |
|------|-------|--------|-----|
| **Mode A** | Descripción textual de lo que debe contener la página | HTML completo optimizado para GEO | Crear páginas nuevas desde cero |
| **Mode B** | HTML de la página actual | HTML clonado + optimizado para GEO | Mejorar páginas existentes sin cambiar su esencia |

### 5.2. GEOContentScorer

El generador incluye un evaluador automático que puntúa el contenido generado en 5 dimensiones:

| Dimensión | Qué evalúa | Rango |
|-----------|-----------|-------|
| **Machine Scannability** | HTML semántico, Schema.org, headers | 0–10 |
| **Citation Readiness** | Estadísticas, párrafos auto-contenidos, datos | 0–10 |
| **Semantic Structure** | Coherencia temática, organización | 0–10 |
| **Schema.org** | Presencia y calidad de datos estructurados | 0–10 |
| **Meta Completeness** | title, description, og:tags, canonical | 0–10 |

### 5.3. Feedback loop

Si el GEOContentScorer devuelve una puntuación por debajo del umbral (configurable, por defecto 7/10 en cada dimensión), el generador reintenta con instrucciones específicas sobre qué mejorar.

```
Descripción / HTML original
        │
        ▼
    Generador LLM
    (Mode A o B)
        │
        ▼
    HTML generado
        │
        ▼
  GEOContentScorer ──── score < umbral ──► Re-generar con feedback
        │                                        │
        │ score >= umbral                        │
        ▼                                        │
    HTML final  ◄────────────────────────────────┘
```

### 5.4. Estado de implementación

El generador está diseñado en `src/prompts/registry.py` (prompts `page_generator` v0.1.0 y `page_clone` v0.1.0) pero la implementación completa está pendiente (Fase 4 del desarrollo).

---

## 6. Medición del impacto acumulado

### 6.1. Ejemplo hipotético

| Fase | Visibilidad (exp) | SoM (exp) | Visibilidad (Live, promedio) |
|------|-------------------|-----------|------------------------------|
| 0 - Baseline | 25% | 8% | 15% |
| 1 - MARTE | 28% (+3) | 9% (+1) | 20% (+5) |
| 2 - Scannability | 35% (+7) | 14% (+5) | 28% (+8) |
| 3 - Citation Ready | 50% (+15) | 22% (+8) | 38% (+10) |
| 4 - Perplexity + Auth | 58% (+8) | 28% (+6) | 45% (+7) |

**Nota**: Estos son valores hipotéticos para ilustrar la metodología. Los valores reales se obtendrán durante la ejecución del TFG.

### 6.2. Qué buscamos demostrar

1. **Que cada fase aporta mejora incremental** — las optimizaciones GEO tienen efecto medible.
2. **Que Citation Readiness es la fase de mayor impacto** — alineado con Aggarwal 2023 (+55-85%).
3. **Que las mejoras experimentales correlacionan con las Live** — validación del simulador.
4. **Que el impacto acumulado es significativo** — la suma de optimizaciones produce una mejora sustancial.

---

*Anterior: [Arquitectura Live](03_LIVE.md) | Siguiente: [Base de Evidencia](05_EVIDENCIA.md)*
