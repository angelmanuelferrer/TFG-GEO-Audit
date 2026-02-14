## 1. Introducción

La evolución de los motores de búsqueda hacia sistemas basados en **modelos generativos** (como Google AI Overviews, Perplexity o ChatGPT con navegación) ha provocado un cambio de paradigma: la visibilidad de una marca ya no depende únicamente del posicionamiento en rankings clásicos, sino de **su aparición y citación dentro de respuestas generadas por IA**.

Este proyecto propone el diseño e implementación de un **pipeline de auditoría GEO (Generative Engine Optimization)** que permita medir, analizar y mejorar la visibilidad de un sitio web dentro de respuestas generativas, tomando como caso de estudio **Programamos.es**.

---

## 2. Objetivos del proyecto

### Objetivo principal

Diseñar un sistema que permita **medir de forma sistemática la visibilidad de un sitio web en motores generativos**, y analizar cómo dicha visibilidad evoluciona tras cambios controlados en el contenido del sitio.

### Objetivos secundarios

* Definir métricas GEO cuantificables (visibilidad, Share of Model, ranking de citación).
* Evaluar la evolución temporal de dichas métricas ante intervenciones de contenido.
* Analizar de forma exploratoria la coexistencia entre métricas GEO y métricas SEO técnicas (Lighthouse).
* Diseñar una arquitectura extensible que pueda evolucionar hacia una plataforma de auditoría completa.

---

## 3. Enfoque metodológico

El proyecto sigue un **enfoque experimental y evolutivo**, alineado con la literatura reciente sobre GEO y sistemas RAG:

* Se define un **pipeline de evaluación fijo**, que actúa como “juez”.
* El pipeline se ejecuta periódicamente sobre el sitio web.
* **La única variable experimental es el contenido del sitio**, que se modifica de forma controlada entre versiones.
* Las variaciones en las métricas observadas se atribuyen exclusivamente a dichos cambios de contenido.

Este enfoque evita introducir sesgos derivados de cambios en el sistema de evaluación.

---

## 4. Métricas de evaluación

### 4.1 Métricas GEO (principales)

El sistema mide, entre otras, las siguientes métricas:

* **Visibilidad**: aparición del sitio web en la respuesta generativa.
* **Share of Model (SoM)**: proporción de citas atribuidas al sitio respecto al total de fuentes citadas.
* **Ranking de citación**: posición en la que aparece citado el sitio dentro de la respuesta.
* **Cobertura**: número de consultas en las que el sitio aparece citado.

Estas métricas se calculan a partir de respuestas generadas por un modelo SOTA que actúa como simulador de motor generativo.

---

### 4.2 Métricas SEO técnicas (exploratorias)

De forma complementaria, se recogen métricas técnicas mediante Lighthouse/PageSpeed (SEO score, performance, CWV).

⚠️ Estas métricas **no se utilizan para establecer causalidad**, sino para analizar su coexistencia temporal con las métricas GEO.

---

## 5. Arquitectura del sistema

El sistema se estructura en un pipeline modular con dos modos de operación:

### 5.1 Modo Experimental (núcleo del TFG)

Modo diseñado para garantizar rigor científico:

* Queries fijas y versionadas.
* Pipeline de evaluación completamente congelado.
* Modelo juez SOTA constante.
* Cambios únicamente en el contenido del sitio web.

Este modo es el utilizado para la validación experimental del trabajo.

---

### 5.2 Modo Plataforma (extensión)

Modo orientado a auditorías completas y uso industrial:

* Arquitectura multi-agente (estratega, descubridor, procesador, auditor técnico).
* Análisis de competidores.
* Integración con dashboards (Notion).
* Generación automática de recomendaciones.

Este modo se presenta como evolución natural del sistema una vez validado el enfoque experimental.

---

## 6. Simulación de motores generativos

La literatura indica que la evaluación GEO **no es válida** si se realiza únicamente con modelos locales o simulaciones offline.

Por este motivo:

* El sistema utiliza **modelos SOTA accesibles vía API** como referencia de comportamiento real.
* El simulador actúa como juez generativo, obligado a citar explícitamente las fuentes utilizadas.

Este enfoque garantiza realismo y alineación con el funcionamiento de los motores actuales.

---

## 7. Principios de optimización GEO considerados

El diseño del sistema y las intervenciones propuestas se apoyan en los siguientes principios descritos en la literatura:

* Claridad semántica y baja ambigüedad.
* Estructura fácilmente parseable (machine scannability).
* Preparación para la citación (citation readiness).
* Similitud semántica con las consultas objetivo.
* Consideración del **sesgo hacia fuentes de autoridad externas (earned media bias)**.
* Análisis del trade-off entre predictabilidad del contenido y diversidad expresiva.

---

## 8. Alcance y limitaciones

* El estudio se centra en un único caso de estudio.
* No se pretende demostrar causalidad directa entre métricas SEO técnicas y visibilidad GEO.
* Los resultados están condicionados al comportamiento probabilístico de los modelos generativos.
* Se mitiga dicha variabilidad mediante ejecuciones repetidas y análisis agregado.

---

## 9. Conclusión

Este proyecto propone un marco reproducible y extensible para el estudio de la optimización GEO, combinando rigor experimental con una arquitectura cercana a escenarios reales de industria.

La validación del pipeline experimental sienta las bases para futuras extensiones hacia plataformas completas de auditoría y optimización para motores generativos.
