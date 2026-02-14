"""
Registro centralizado de prompts del sistema GEO-Audit.

Cada prompt tiene versión, modelo asociado, parámetros y changelog.
Los prompts se implementan completamente en sus fases correspondientes:
- rag_judge: Fase 1
- metrics_extractor: Fase 2
- sentiment_analyzer: Fase 2
- page_generator: Fase 4
"""

PROMPT_REGISTRY = {
    "rag_judge": {
        "version": "1.0.0",
        "description": "Simula un motor generativo que sintetiza respuestas con citaciones",
        "system": (
            "Eres un motor de busqueda generativo (similar a Perplexity AI). "
            "Tu tarea es responder preguntas del usuario sintetizando informacion "
            "de las fuentes web proporcionadas en el contexto.\n\n"
            "FORMATO DE RESPUESTA:\n"
            "Debes responder EXCLUSIVAMENTE en formato JSON con esta estructura exacta:\n"
            "{\n"
            '  "answer": "Tu respuesta aqui con citas numeradas [1], [2]...",\n'
            '  "citations": [\n'
            '    {"index": 1, "url": "https://fuente1.com/pagina", "quote": "Texto exacto usado de la fuente"}\n'
            "  ],\n"
            '  "sources_used": ["https://fuente1.com/pagina", "https://fuente2.com"],\n'
            '  "sources_available_but_unused": ["https://fuente3.com"]\n'
            "}\n\n"
            "REGLAS DE CITACION:\n"
            "1. Cada afirmacion factual en tu respuesta DEBE tener una cita numerada [N] inmediatamente despues.\n"
            "2. El campo 'quote' debe contener el texto EXACTO de la fuente que respalda la afirmacion.\n"
            "3. Enumera TODAS las fuentes proporcionadas, clasificandolas como usadas o no usadas.\n"
            "4. NO inventes informacion que no este presente en el contexto.\n"
            "5. Si el contexto no contiene suficiente informacion, indicalo en tu respuesta.\n"
            "6. Las citas deben aparecer en orden de aparicion en la respuesta.\n\n"
            "ESTILO DE RESPUESTA:\n"
            "- Se conciso e informativo, como un motor de busqueda IA.\n"
            "- Sintetiza informacion de multiples fuentes cuando sea apropiado.\n"
            "- Prioriza las fuentes que responden directamente a la pregunta.\n"
            "- Usa lenguaje natural en espanol, no listas de hechos sueltos.\n"
            "- Si una fuente es especialmente relevante, dale mayor peso en la respuesta."
        ),
        "user_template": (
            "Las siguientes fuentes web estan disponibles:\n\n"
            "{context}\n\n"
            "---\n\n"
            "Pregunta: {question}\n\n"
            "Responde en formato JSON con tu respuesta y citaciones estructuradas."
        ),
        "model": "gpt-4o",
        "temperature": 0.0,
        "seed": 42,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"},
        "changelog": [
            "0.1.0: Estructura base creada (Fase 0)",
            "1.0.0: Prompt completo del RAG Judge con reglas JSON y citacion (Fase 1)",
        ],
    },
    "metrics_extractor": {
        "version": "0.1.0",
        "description": "Extrae métricas GEO estructuradas de una respuesta generada",
        "system": "",  # Implementar en Fase 2
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "seed": 42,
        "response_format": {"type": "json_object"},
        "changelog": [
            "0.1.0: Estructura base creada (Fase 0)",
        ],
    },
    "sentiment_analyzer": {
        "version": "0.1.0",
        "description": "Clasifica sentimiento de menciones de marca (POSITIVO/NEUTRO/NEGATIVO)",
        "system": "",  # Implementar en Fase 2
        "model": "gpt-4o-mini",
        "temperature": 0.0,
        "changelog": [
            "0.1.0: Estructura base creada (Fase 0)",
        ],
    },
    "page_generator": {
        "version": "0.1.0",
        "description": "Genera páginas HTML/CSS optimizadas para GEO",
        "system": "",  # Implementar en Fase 4
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 4000,
        "changelog": [
            "0.1.0: Estructura base creada (Fase 0)",
        ],
    },
    "page_clone": {
        "version": "0.1.0",
        "description": "Clona y optimiza una página web existente para GEO",
        "system": "",  # Implementar en Fase 4
        "model": "gpt-4o",
        "temperature": 0.3,
        "max_tokens": 4000,
        "changelog": [
            "0.1.0: Estructura base creada (Fase 0)",
        ],
    },
}


def get_prompt(name: str) -> dict:
    """Obtiene un prompt del registro por nombre."""
    if name not in PROMPT_REGISTRY:
        raise KeyError(f"Prompt '{name}' no encontrado. Disponibles: {list(PROMPT_REGISTRY.keys())}")
    return PROMPT_REGISTRY[name]
