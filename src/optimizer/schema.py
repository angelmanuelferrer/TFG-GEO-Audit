"""Schema Pydantic para el output del GEOOptimizer (v3).

Usado como response_schema en la llamada a Gemini para forzar JSON estructurado,
y como modelo de validación en el parser tolerante de _parse_response.

v3 añade campos opcionales que el agente con tool-calling rellena con evidencia
verbatim, deltas concretos y señales cross-mode. Todos opcionales para no
romper la lectura de runs anteriores.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Lever(str, Enum):
    citation_readiness = "citation_readiness"
    authority_injection = "authority_injection"
    low_perplexity = "low_perplexity"
    machine_scannability = "machine_scannability"
    semantic_clarity = "semantic_clarity"
    caption_injection = "caption_injection"


class Impact(str, Enum):
    alto = "alto"
    medio = "medio"
    bajo = "bajo"


class CrossModeSignal(str, Enum):
    experimental_only = "experimental_only"
    live_only = "live_only"
    both_modes = "both_modes"
    unknown = "unknown"


class Effort(str, Enum):
    xs = "xs"
    s = "s"
    m = "m"
    l = "l"


class RecommendationL1(BaseModel):
    title: str = Field(description="Título corto y accionable de la recomendación (max 80 chars)")
    lever: Lever = Field(description="Palanca GEO que aplica esta recomendación")
    where: str = Field(description="URL concreta o sección/elemento exacto donde aplicar el cambio")
    why: str = Field(description="Qué query recupera y por qué esta palanca funciona en este caso concreto")
    evidence: str = Field(
        description=(
            "Fragmento literal del competidor que ganó la query. DEBE ser substring "
            "exacto de algún chunk devuelto por search_competitors o quote_span en este turno."
        )
    )
    impact: Impact = Field(description="Impacto estimado: alto (palanca estrella + múltiples queries), medio, bajo")
    target_query_ids: List[str] = Field(
        description="Lista de query_ids que esta recomendación ayuda a recuperar (mínimo 1)",
        min_length=1,
    )

    # ---- v3: provenance + grounding (opcionales para no romper históricos)
    current_snippet: Optional[str] = Field(
        default=None,
        description="Texto verbatim de la página target que se va a reescribir (≤200 palabras).",
    )
    suggested_snippet: Optional[str] = Field(
        default=None,
        description="Reescritura concreta sugerida (≤200 palabras) que aplica la palanca.",
    )
    competitor_delta: Optional[str] = Field(
        default=None,
        description="Una frase: 'el competidor X tiene Y; programamos.es carece de Y'.",
    )
    evidence_chunk_id: Optional[str] = Field(
        default=None,
        description="ID del chunk citado en `evidence` (provenance, lo rellenan las tools).",
    )
    evidence_url: Optional[str] = Field(
        default=None,
        description="URL del competidor de la que proviene `evidence`.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confianza [0,1] post-critic. Alta cuando la query falla en ambos modos.",
    )
    cross_mode_signal: Optional[CrossModeSignal] = Field(
        default=None,
        description="Si la query falla solo en experimental, solo en live, o en ambos.",
    )
    effort: Optional[Effort] = Field(
        default=None,
        description="Tamaño estimado del cambio: xs (<30min), s (1-2h), m (medio día), l (>1 día).",
    )


class GEOOptimizerOutput(BaseModel):
    recommendations_l1: List[RecommendationL1] = Field(
        description="Recomendaciones priorizadas de mayor a menor impacto. Máximo 8.",
        max_length=8,
    )
    prompt_l2: str = Field(
        description=(
            "Prompt autocontenido y completo para usar en Claude Code. Incluye rol, "
            "contenido actual, lista numerada de cambios con ubicación+palanca+ejemplo, "
            "restricciones duras y formato de entrega."
        )
    )
