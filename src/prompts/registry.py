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
        "version": "0.1.0",
        "description": "Simula un motor generativo que sintetiza respuestas con citaciones",
        "system": "",  # Implementar en Fase 1
        "user_template": "",  # Implementar en Fase 1
        "model": "gpt-4o",
        "temperature": 0.0,
        "seed": 42,
        "max_tokens": 2000,
        "response_format": {"type": "json_object"},
        "changelog": [
            "0.1.0: Estructura base creada (Fase 0)",
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
