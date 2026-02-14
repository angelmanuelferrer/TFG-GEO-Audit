# Fase 6: Analisis y Redaccion

**Duracion estimada**: 2 semanas (Semanas 9-10)
**Dependencias**: Fases 3 y 5 completadas
**Coste**: $0 (analisis local)

---

## Objetivo

Analizar los datos recopilados, generar visualizaciones, calcular correlaciones, redactar resultados y conclusiones, y producir la guia de buenas practicas SEO+GEO.

---

## Tareas

### 6.1 Evolucion temporal de metricas GEO

**Archivo**: `notebooks/analysis.ipynb`

**Generar graficos**:
- Visibilidad total a lo largo de las intervenciones (linea temporal)
- SoM promedio por intervencion (barras)
- Coverage por categoria (informacional/comparativa/navegacional) por intervencion
- PAWC total por intervencion
- Ranking promedio por intervencion (invertido, menor = mejor)
- GEO Content Score del target vs competidores a lo largo del tiempo

**Herramientas**: matplotlib + seaborn

---

### 6.2 Correlacion SEO ↔ GEO

**Generar**:
- Matriz de correlacion: metricas SEO (score, performance, LCP, TBT) vs metricas GEO (visibilidad, SoM, PAWC)
- Scatter plots para pares con correlacion significativa
- Test de significancia estadistica (p-value)
- Documentar si la correlacion es causal o coincidental

**Hipotesis a evaluar**:
- H1: Mejor SEO score → mejor visibilidad GEO
- H2: Mejor estructura HTML → mayor SoM
- H3: GEO Content Score predice visibilidad

---

### 6.3 Comparacion simulado vs real

**Generar**:
- Tabla: metricas RAG Simulator vs metricas Live LLM
- Correlacion Spearman entre rankings simulados y reales
- Grafico de concordancia por query
- Conclusiones sobre la validez del simulador

---

### 6.4 Analisis del Page Generator

**Generar**:
- Comparativa GEO score: paginas originales vs generadas
- Impacto en metricas cuando se despliegan paginas generadas (Intervencion 4)
- Analisis cualitativo de calidad del HTML generado

---

### 6.5 Redaccion de resultados

**Estructura sugerida** para la memoria del TFG:

1. **Resultados del baseline**: Estado inicial de programamos.es
2. **Impacto de cada intervencion**: Delta en metricas respecto al baseline
3. **Analisis comparativo inter-modelo**: Consistencia de resultados
4. **Validacion con motores reales**: Correlacion simulado-real
5. **Paginas generadas**: Calidad y efectividad
6. **Limitaciones**: Todo lo que no funciono o no se pudo medir

---

### 6.6 Guia de buenas practicas SEO+GEO

**Entregable**: Documento practico con recomendaciones accionables

**Estructura**:
1. Machine Scannability: que hacer y que evitar
2. Citation Readiness: como hacer contenido citable
3. Semantic Clarity: como escribir para LLMs
4. Authority Signals: como demostrar autoridad
5. Estructura HTML optima: checklist
6. Schema.org: tipos recomendados y ejemplos
7. Errores comunes a evitar

---

### 6.7 Exportar datos finales

- [ ] `data/analysis/temporal_evolution.csv` — Todas las metricas por run
- [ ] `data/analysis/correlation_matrix.csv` — Correlaciones SEO-GEO
- [ ] `data/analysis/figures/` — Todos los graficos en PNG 300dpi
- [ ] Scorecard final con metricas comparativas

---

## Criterios de Aceptacion

- [ ] Al menos 6 graficos generados (evolucion temporal, correlaciones, comparativas)
- [ ] Matriz de correlacion SEO-GEO calculada
- [ ] Comparacion simulado vs real documentada
- [ ] Seccion de resultados redactada
- [ ] Guia de buenas practicas completada
- [ ] Todos los datos exportados en formatos reutilizables (CSV, JSON, PNG)
- [ ] Notebook de analisis ejecutable y reproducible

---

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| No hay suficientes datos para correlacion significativa | Documentar como limitacion; usar analisis descriptivo |
| Los resultados no muestran mejora clara | Es un resultado valido; documentar por que y que se aprendio |
| Graficos no suficientemente claros para la memoria | Iterar con el profesor; usar paleta de colores accesible |
