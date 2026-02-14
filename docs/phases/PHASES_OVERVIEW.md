# GEO-Audit: Roadmap de Desarrollo por Fases

## Vision General

```
FASE 0          FASE 1            FASE 2           FASE 3              FASE 4           FASE 5          FASE 6
Setup     →   Pipeline Core  →  Metricas     →   Experimentacion  →  Page Generator → Validacion  →  Analisis
(Semana 1)    (Semanas 2-3)     (Semana 4)       (Semanas 5-8)       (Semana 7)      (Semana 8)     (Semanas 9-10)
```

---

## Fases y Dependencias

| Fase | Nombre | Depende de | Entregables Clave | Semana |
|------|--------|------------|-------------------|--------|
| **0** | Setup e Infraestructura | — | Repo reestructurado, `requirements.txt`, config congelada, prompt registry | 1 |
| **1** | Pipeline Core Mejorado | Fase 0 | HTML-aware processor, JSON judge, token-based chunking, citation extractor | 2-3 |
| **2** | Framework de Metricas | Fase 1 | Todas las metricas GEO, sentiment, GEO content scorer, live LLM evaluator, scorecard | 4 |
| **3** | Experimentacion | Fase 2 | Baseline + 4 fases de intervencion, datos longitudinales, snapshots | 5-8 |
| **4** | Generador de Paginas | Fase 1 | Modo A (descripcion), Modo B (clon), validador, paginas generadas | 7 (paralelo a Fase 3) |
| **5** | Validacion Multi-Modelo | Fase 3 | Resultados Gemini, Llama local, comparacion con motores reales | 8 |
| **6** | Analisis y Redaccion | Fases 3+5 | Graficos temporales, correlaciones SEO-GEO, conclusiones, guia buenas practicas | 9-10 |

### Diagrama de Dependencias

```
Fase 0 ──→ Fase 1 ──→ Fase 2 ──→ Fase 3 ──→ Fase 5 ──→ Fase 6
                 │                    │
                 └──→ Fase 4 ────────┘ (paralelo)
```

---

## Estado Actual del Proyecto

### Ya implementado
- [x] Pipeline LangGraph basico en `firststep.ipynb` (6 nodos)
- [x] Recoleccion SEO automatizada (`collect_metrics/collect_seo.py`)
- [x] GitHub Actions para SEO diario
- [x] Almacenamiento en `data/seo/`
- [x] Integracion con Notion

### Pendiente (por fase)
- [ ] **Fase 0**: Reestructuracion, config, requirements
- [ ] **Fase 1**: HTML-aware processing, JSON judge, fix chunking
- [ ] **Fase 2**: Metricas GEO completas, live evaluator
- [ ] **Fase 3**: Runs experimentales con intervenciones
- [ ] **Fase 4**: Generador de paginas IA
- [ ] **Fase 5**: Validacion cruzada multi-modelo
- [ ] **Fase 6**: Analisis final y redaccion

---

## Criterio de Avance entre Fases

Cada fase tiene **criterios de aceptacion** definidos en su documento detallado. No se avanza a la siguiente fase hasta que se cumplan todos los criterios de la fase actual.

**Excepcion**: La Fase 4 (Page Generator) puede desarrollarse en paralelo a la Fase 3 porque solo depende de la Fase 1.

---

## Presupuesto por Fase

| Fase | Coste Estimado | Acumulado |
|------|---------------|-----------|
| 0 | $0 | $0 |
| 1 | $1.00 (pruebas pipeline) | $1.00 |
| 2 | $0.50 (pruebas metricas) | $1.50 |
| 3 | $3.15 (15 runs experimentales) | $4.65 |
| 4 | $2.00 (generacion paginas) | $6.65 |
| 5 | $2.10 (validacion multi-modelo) | $8.75 |
| 6 | $0 (analisis local) | $8.75 |
| Desarrollo/pruebas misc | $5.00 | **~$13.75** |

---

## Documentos Detallados

- [`PHASE_0_SETUP.md`](./PHASE_0_SETUP.md) — Setup e Infraestructura
- [`PHASE_1_CORE_PIPELINE.md`](./PHASE_1_CORE_PIPELINE.md) — Pipeline Core Mejorado
- [`PHASE_2_METRICS.md`](./PHASE_2_METRICS.md) — Framework de Metricas
- [`PHASE_3_EXPERIMENTATION.md`](./PHASE_3_EXPERIMENTATION.md) — Experimentacion Controlada
- [`PHASE_4_PAGE_GENERATOR.md`](./PHASE_4_PAGE_GENERATOR.md) — Generador de Paginas con IA
- [`PHASE_5_VALIDATION.md`](./PHASE_5_VALIDATION.md) — Validacion Multi-Modelo
- [`PHASE_6_ANALYSIS.md`](./PHASE_6_ANALYSIS.md) — Analisis y Redaccion

---

## Referencia

Arquitectura completa: [`ARCHITECTURE_REPORT.md`](../ARCHITECTURE_REPORT.md)
