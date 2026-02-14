# Fase 5: Validacion Multi-Modelo

**Duracion estimada**: 1 semana (Semana 8)
**Dependencias**: Fase 3 (al menos baseline + 2 intervenciones)
**Coste**: ~$2.10

---

## Objetivo

Validar que los resultados del experimento no son artefacto de un unico LLM. Ejecutar el pipeline con modelos alternativos y comparar con consultas manuales a motores generativos reales.

---

## Tareas

### 5.1 Validacion con Gemini

**Ref. arquitectura**: Seccion 5.4

**Implementar**:
- Ejecutar el pipeline RAG Simulator sustituyendo GPT-4o por Gemini 2.0 Flash
- Usar las mismas queries, mismo contexto, mismo retrieval
- Comparar metricas: visibilidad, SoM, ranking
- 3 runs con datos del baseline y de la ultima intervencion

**Archivos**: Parametrizar el judge en `src/rag/judge.py` para aceptar distintos modelos

---

### 5.2 Validacion con modelo local (Kaggle)

**Implementar**:
- Ejecutar el pipeline con Llama 3.1 8B en Kaggle (GPU T4)
- Adaptar el prompt del judge para formato compatible con Llama
- Comparar metricas con GPT-4o y Gemini
- Documentar diferencias en calidad de citacion

**Nota**: Este paso se ejecuta en Kaggle, no en GitHub Actions ni local.

---

### 5.3 Comparacion con motores generativos reales

**Ref. arquitectura**: Seccion 14.3

**Implementar** (manualmente):
- Ejecutar las 15 queries fijas en Perplexity (web), ChatGPT (con browse) y Gemini (web)
- Para cada respuesta, registrar: menciona programamos? URL presente? Posicion? Sentiment?
- Comparar resultados manuales con metricas del RAG Simulator
- Calcular correlacion (Spearman) entre rankings simulados y reales

**Formato de registro** (`data/geo/validation/manual_YYYYMMDD.json`):
```json
{
  "date": "2026-03-XX",
  "queries": [
    {
      "query": "...",
      "engines": {
        "perplexity": {"mentions_target": true, "rank": 2, "sentiment": "positivo"},
        "chatgpt": {"mentions_target": false, "rank": null, "sentiment": null},
        "gemini": {"mentions_target": true, "rank": 1, "sentiment": "neutro"}
      }
    }
  ]
}
```

---

### 5.4 Analisis de consistencia inter-modelo

**Implementar**:
- Tabla comparativa: misma query → resultado en GPT-4o vs Gemini vs Llama vs Real
- Calcular Engine Coverage por query
- Identificar queries donde hay consenso (todos citan) vs divergencia
- Documentar sesgos observados por modelo

---

## Criterios de Aceptacion

- [ ] Pipeline ejecutado con Gemini (al menos 2 runs)
- [ ] Pipeline ejecutado con Llama local en Kaggle (al menos 1 run)
- [ ] 15 queries ejecutadas manualmente en 3 motores reales
- [ ] Tabla comparativa inter-modelo generada
- [ ] Correlacion calculada entre simulado y real
- [ ] Documentacion de sesgos y limitaciones por modelo
- [ ] Datos guardados en `data/geo/validation/`

---

## Riesgos

| Riesgo | Mitigacion |
|--------|-----------|
| Llama 3.1 no sigue bien el prompt JSON | Usar prompt simplificado con formato texto; parsear manualmente |
| Queries manuales consumen mucho tiempo | Reducir a 5 queries representativas (2 info, 2 comp, 1 nav) si necesario |
| Motores reales dan resultados muy distintos al simulador | Documentar como limitacion; es un hallazgo valido del TFG |
| Kaggle no disponible | Usar Google Colab como alternativa con GPU T4 |
