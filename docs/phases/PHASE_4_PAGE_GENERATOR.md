# Fase 4: Generador de Paginas con IA

**Duracion estimada**: 1 semana (Semana 7, paralelo a Fase 3)
**Dependencias**: Fase 1 completada
**Coste**: ~$2.00

---

## Objetivo

Implementar el Bloque 3 del profesor: agentes IA que generen paginas HTML/CSS optimizadas para GEO. Dos modos: desde descripcion del usuario (Modo A) y clonando/mejorando una web existente (Modo B).

---

## Tareas

### 4.1 Modo A: Generacion desde descripcion

**Ref. arquitectura**: Seccion 9.1

**Archivo**: `src/generation/page_generator.py`

**Implementar**:
- Entrada: descripcion textual del usuario + keywords opcionales
- Prompt con principios GEO integrados (machine scannability, citation readiness, low perplexity, authority signals)
- Salida: HTML5 completo con Tailwind CSS (CDN), Schema.org JSON-LD, meta tags
- Modelo: GPT-4o con `temperature=0.3`, `max_tokens=4000`

**Ejemplo de uso**:
```python
generator = PageGenerator()
html = generator.from_description(
    description="Pagina sobre recursos de programacion para ninos en Espana",
    keywords=["programacion infantil", "Scratch", "pensamiento computacional"]
)
```

---

### 4.2 Modo B: Clonacion optimizada

**Archivo**: `src/generation/page_generator.py`

**Implementar**:
- Entrada: URL de una pagina existente
- Pipeline: scrape → analisis de estructura → deteccion de limitaciones → generacion optimizada
- Preservar la informacion y proposito original
- Mejorar estructura semantica, schema.org, citation readiness
- Detectar y senalar dependencias backend no replicables (formularios, APIs, login)

**Ejemplo de uso**:
```python
generator = PageGenerator()
html = generator.from_clone(
    source_url="https://programamos.es/aprende",
    instructions="Optimizar para GEO manteniendo el contenido"
)
```

---

### 4.3 Validador de paginas generadas

**Archivo**: `src/generation/validator.py`

**Implementar**:
- Validacion HTML: HTML5 valido, charset UTF-8, lang="es"
- Validacion SEO basica: h1 unico, meta title y description presentes, alt en imagenes
- Validacion GEO: schema.org presente, headers jerarquicos, datos estructurados
- Scoring con `GEOContentScorer` (de Fase 2)
- Feedback loop: si score < umbral (70/100), regenerar con feedback especifico

**Interfaz**:
```python
validator = PageValidator()
result = validator.validate(html)
# result.is_valid: bool
# result.geo_score: float
# result.issues: list[str]
# result.suggestions: list[str]
```

---

### 4.4 Implementar prompts del generador

**Ref. arquitectura**: Secciones 8.3, 20.2

**Archivo**: Actualizar `src/prompts/registry.py`

**Implementar**:
- `page_generator.system`: Prompt con principios GEO detallados y requisitos tecnicos
- `page_clone.system`: Prompt para modo clonacion con deteccion de limitaciones
- Documentar cada principio GEO con referencia al paper correspondiente

---

### 4.5 Generar paginas de prueba

Generar al menos:
- [ ] 2 paginas en Modo A (tematicas relacionadas con programamos.es)
- [ ] 2 paginas en Modo B (clones optimizados de paginas reales de programamos.es)
- [ ] Guardar en `data/pages_generated/from_description/` y `data/pages_generated/from_clone/`
- [ ] Evaluar cada pagina con GEOContentScorer
- [ ] Comparar scores con paginas originales

---

## Criterios de Aceptacion

- [ ] Modo A genera HTML5 valido con schema.org y meta tags
- [ ] Modo B clona y mejora una pagina real manteniendo el contenido
- [ ] Validador detecta problemas comunes (h1 faltante, sin schema, etc.)
- [ ] GEO score de paginas generadas > 70/100
- [ ] Al menos 4 paginas generadas y guardadas
- [ ] Prompts del generador versionados en registry
- [ ] Las paginas generadas son responsive (Tailwind)

---

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| GPT-4o genera HTML invalido | Validacion post-generacion + retry con feedback |
| max_tokens insuficiente para paginas complejas | Limitar scope de cada pagina; generar por secciones si necesario |
| Tailwind CDN no disponible offline | Alternativa: CSS inline basico |
