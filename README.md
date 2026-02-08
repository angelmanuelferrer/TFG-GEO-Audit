🚀 GEO & Technical SEO Audit System: Caso de Estudio "Programamos"
Trabajo de Fin de Grado (TFG) Optimización de Motores Generativos: Arquitectura, Medición y Estrategias de Intervención.

📄 Resumen del Proyecto
La arquitectura fundamental de la recuperación de información está cambiando de un modelo determinista (Google SERP) a un modelo probabilístico y sintetizado (ChatGPT, Perplexity, Gemini). Este cambio de paradigma da lugar a una nueva disciplina: GEO (Generative Engine Optimization).

Este proyecto desarrolla un sistema de Agentes Autónomos capaz de auditar, medir y optimizar la visibilidad de la organización sin ánimo de lucro Programamos.es en este nuevo ecosistema. A diferencia del SEO tradicional, que busca clics, el GEO busca la inclusión semántica en la respuesta generada por la IA.

El sistema combina métricas de Rendimiento Web (Core Web Vitals) con métricas de Visibilidad en IA (PAWC, SoM) para establecer una correlación entre la calidad técnica y la autoridad semántica percibida por los LLMs.

🎯 Objetivos del Proyecto
Auditoría Dual (SEO + GEO): Automatizar la recolección de métricas técnicas (Lighthouse) y de visibilidad generativa (Simulación RAG).

Ingeniería Inversa de Intención: Utilizar agentes de IA para deducir las preguntas de nicho donde la marca debería ser citada, evitando el sesgo de marca (Brand Bias).


Medición Científica: Implementar métricas académicas como Position-Adjusted Word Count (PAWC) y Share of Model (SoM) para cuantificar la visibilidad.

Generación de Activos Web: Desplegar agentes capaces de generar código (HTML/Tailwind) optimizado para ser ingerido por sistemas RAG (Retrieval-Augmented Generation).

🏗️ Arquitectura del Sistema (Agentic Workflow)
El núcleo del proyecto es un grafo de estados (StateGraph) construido con LangGraph que orquesta el flujo de trabajo de múltiples agentes especializados:

Fragmento de código
graph LR
    A[Nodo Estratega] --> B[Nodo Descubridor]
    B --> C[Nodo Procesador]
    C --> D[Nodo Técnico SEO]
    D --> E[Simulador RAG]
    E --> F[Reportero Notion]
Descripción de Nodos:
🧠 Nodo A: El Estratega (Intent Reverse Engineering) Analiza la web objetivo y deduce, mediante GPT-4, cuáles son las necesidades del usuario ("Pain Points") que la web resuelve, generando prompts de búsqueda de nicho.

🕵️ Nodo B: El Descubridor (Competitive Intelligence) Utiliza Tavily para realizar búsquedas profundas en internet y detectar a los competidores reales que dominan esas consultas, ignorando resultados irrelevantes.

⚙️ Nodo C: El Procesador (RAG Pipeline) Realiza scraping ético de la web objetivo y la competencia, aplicando estrategias de chunking (fragmentación) para preparar el contenido para su análisis vectorial.

⚡ Nodo Técnico (Google PageSpeed) Consulta la API de Lighthouse para extraer métricas críticas: LCP (Largest Contentful Paint), TBT (Total Blocking Time) y Puntuación SEO, correlacionando velocidad con visibilidad.

⚖️ Nodo D: El Juez (Simulador de Motor Generativo) Crea una base de datos vectorial efímera (FAISS) y simula el comportamiento de un motor de respuesta (como Perplexity). Evalúa si la marca es citada en la respuesta generada.

📊 Nodo E: El Reportero (Integration) Inyecta los resultados en tiempo real en una base de datos de Notion, creando un dashboard histórico de evolución.

📏 Métricas Implementadas
Basándonos en la investigación de Aggarwal et al. (2024) y Chen et al. (2025), el sistema calcula:

1. Métricas GEO (Visibilidad IA)
PAWC (Position-Adjusted Word Count): Mide la visibilidad ponderada por la posición de la cita. Una mención al principio vale más que al final.


SoM (Share of Model): Porcentaje de citas que pertenecen a nuestra marca frente al total de competidores en una respuesta generada.

Ranking de Citación: Posición ordinal de la primera aparición de la marca (1º, 2º, 3º...).


Subjective Impression: Evaluación cualitativa (Relevancia, Autoridad) realizada por un "LLM-as-a-Judge".

2. Métricas Técnicas (SEO Tradicional)
Performance Score: Puntuación global de rendimiento (0-100).

LCP & TBT: Métricas clave de la experiencia de usuario (Core Web Vitals).

🛠️ Stack Tecnológico
Lenguaje: Python 3.10+

Orquestación: LangChain & LangGraph

LLMs: OpenAI GPT-4o (Cerebro), GPT-4o-Mini (Tareas auxiliares)

Búsqueda & Web: Tavily API (Search), LangChain WebBaseLoader (Scraping)

Vector Store: FAISS (Facebook AI Similarity Search)

Análisis Técnico: Google PageSpeed Insights API

Dashboard: Notion API (client-python)

📚 Fundamentación Teórica
Este proyecto se apoya en la literatura reciente sobre la optimización para motores generativos. Específicamente, adopta la definición de Generative Engine (GE) como sistemas que sintetizan información de múltiples fuentes utilizando LLMs.

Se validan experimentalmente las hipótesis de Aggarwal et al. sobre cómo la Adición de Citas y Estadísticas  influyen positivamente en la probabilidad de que un contenido sea recuperado por el sistema RAG y citado en la respuesta final.

🚀 Instalación y Uso

Bash
pip install -r requirements.txt
# Principales: langchain, langgraph, faiss-cpu, notion-client, openai, tavily-python
Configurar Variables de Entorno (.env):

