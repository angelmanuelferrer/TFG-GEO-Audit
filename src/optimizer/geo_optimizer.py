"""GEOOptimizer — analiza queries perdidas y genera recomendaciones GEO.

Búsqueda: Serper API (Google real, sin rate limit de IA).
Análisis: Claude Haiku via tool use (structured output nativo, sin parsing frágil).
Prompt versionado en src/prompts/registry.py (clave: "geo_optimizer").
Schema de output en src/optimizer/schema.py (GEOOptimizerOutput).
"""
from __future__ import annotations

import asyncio
import json
import os
import pathlib
import sys
from typing import Any, Dict, List, Optional, Set
from urllib.parse import urlparse

PROJECT_ROOT = pathlib.Path(__file__).parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env", override=False)

import logging

import anthropic
from pydantic import ValidationError

logger = logging.getLogger(__name__)

from src.optimizer.schema import GEOOptimizerOutput
from src.prompts.registry import get_prompt

TARGET_DOMAIN = "programamos.es"
MAX_PAGE_CHARS = 1500
MAX_QUERIES = 4

# Tool de Claude para structured output nativo (tool use forzado).
_CLAUDE_TOOL: Dict[str, Any] = {
    "name": "geo_optimizer_output",
    "description": "Devuelve las recomendaciones GEO priorizadas y el prompt L2 para Claude Code.",
    "input_schema": {
        "type": "object",
        "properties": {
            "recommendations_l1": {
                "type": "array",
                "description": "Recomendaciones priorizadas de mayor a menor impacto. Máximo 8.",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "lever": {"type": "string", "enum": [
                            "citation_readiness", "authority_injection", "low_perplexity",
                            "machine_scannability", "semantic_clarity", "caption_injection",
                        ]},
                        "where": {"type": "string"},
                        "why": {"type": "string"},
                        "evidence": {"type": "string"},
                        "impact": {"type": "string", "enum": ["alto", "medio", "bajo"]},
                        "target_query_ids": {"type": "array", "items": {"type": "string"}},
                        "current_snippet": {"type": "string"},
                        "suggested_snippet": {"type": "string"},
                        "effort": {"type": "string", "enum": ["xs", "s", "m", "l"]},
                    },
                    "required": ["title", "lever", "where", "why", "evidence", "impact", "target_query_ids"],
                },
            },
            "prompt_l2": {"type": "string"},
        },
        "required": ["recommendations_l1", "prompt_l2"],
    },
}

_CLAUDE_MODEL = "claude-sonnet-4-6"
_CRITIC_MODEL = "claude-haiku-4-5-20251001"

_SITEMAP_CACHE: List[str] = []  # module-level cache, populated once per process
_SITEMAP_LASTMOD: Dict[str, str] = {}  # url → lastmod date string


def _load_sitemap() -> List[str]:
    """Fetches programamos.es sitemap and returns all <loc> URLs. Cached."""
    global _SITEMAP_CACHE, _SITEMAP_LASTMOD
    if _SITEMAP_CACHE:
        return _SITEMAP_CACHE
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": os.getenv("USER_AGENT", "GEO-Optimizer/1.0")}
        r = requests.get(f"https://{TARGET_DOMAIN}/sitemap.xml", headers=headers, timeout=10)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "xml")
        for url_elem in soup.find_all("url"):
            loc = url_elem.find("loc")
            lastmod = url_elem.find("lastmod")
            if loc:
                url_str = loc.get_text(strip=True)
                _SITEMAP_CACHE.append(url_str)
                if lastmod:
                    _SITEMAP_LASTMOD[url_str] = lastmod.get_text(strip=True)
        if not _SITEMAP_CACHE:
            # fallback: sitemap sin <url> wrapper (solo <loc>)
            _SITEMAP_CACHE = [loc.get_text(strip=True) for loc in soup.find_all("loc")]
    except Exception:
        _SITEMAP_CACHE = []
    return _SITEMAP_CACHE


def _sitemap_score(url: str, query_text: str) -> int:
    """Simple word-overlap score between URL path tokens and query words."""
    path = url.replace(f"https://{TARGET_DOMAIN}", "").lower()
    path_tokens = set(t for t in path.replace("-", " ").replace("/", " ").split() if len(t) > 2)
    query_tokens = set(w.lower() for w in query_text.split() if len(w) > 2)
    return len(path_tokens & query_tokens)


def _build_combined_search_string(queries: List[Dict[str, Any]]) -> str:
    """Una sola query site-scoped combinando las primeras palabras de cada query seleccionada."""
    seen: set[str] = set()
    terms: List[str] = []
    for q in queries[:MAX_QUERIES]:
        for w in q.get("query_text", "").split()[:4]:
            token = w.strip("¿?¡!.,;:()").lower()
            if token and token not in seen:
                seen.add(token)
                terms.append(token)
    return f"site:{TARGET_DOMAIN} {' '.join(terms)}"


def _assign_urls_to_queries(
    urls: List[str], queries: List[Dict[str, Any]]
) -> Dict[str, List[str]]:
    """Distribuye URLs a queries por _sitemap_score.
    URLs sin match en ninguna query se asignan a todas (relevancia temática general).
    """
    result: Dict[str, List[str]] = {q["query_id"]: [] for q in queries[:MAX_QUERIES]}
    default_bucket: List[str] = []
    for url in urls:
        scores = {
            q["query_id"]: _sitemap_score(url, q.get("query_text", ""))
            for q in queries[:MAX_QUERIES]
        }
        if max(scores.values(), default=0) == 0:
            default_bucket.append(url)
        else:
            for qid, score in scores.items():
                if score > 0:
                    result[qid].append(url)
    # URLs sin match solo se asignan a queries que no tienen ningún otro resultado
    for qid in result:
        if not result[qid]:
            for url in default_bucket:
                result[qid].append(url)
    return result


def _find_sitemap_urls(queries: List[Dict[str, Any]], existing: set[str], n: int = 2) -> List[str]:
    """Returns up to n*len(queries) sitemap URLs most relevant to the query set, deduped."""
    sitemap = _load_sitemap()
    if not sitemap:
        return []

    combined_text = " ".join(q.get("query_text", "") for q in queries)
    scored = [(url, _sitemap_score(url, combined_text)) for url in sitemap if url not in existing]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [url for url, score in scored[:n * len(queries)] if score > 0]


def _fetch_page_content(url: str) -> str:
    """Scrapea una URL y devuelve el texto limpio."""
    try:
        import requests
        from bs4 import BeautifulSoup

        headers = {"User-Agent": os.getenv("USER_AGENT", "GEO-Optimizer/1.0")}
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        content = "\n".join(lines)
        return content[:MAX_PAGE_CHARS] + ("…" if len(content) > MAX_PAGE_CHARS else "")
    except Exception as e:
        return f"[Error al cargar {url}: {e}]"


def _build_queries_context(
    queries: List[Dict[str, Any]],
    search_urls_by_query: Optional[Dict[str, List[str]]] = None,
    competitor_snippets_by_query: Optional[Dict[str, List[Dict[str, str]]]] = None,
) -> str:
    parts = []
    search_urls_by_query = search_urls_by_query or {}
    competitor_snippets_by_query = competitor_snippets_by_query or {}
    for q in queries[:MAX_QUERIES]:
        qid = q["query_id"]
        part = f"Query {qid}: {q['query_text']}\n"
        part += f"  Motivo de pérdida: {q['reason']}\n"

        # Competidores del RAG experimental (tienen excerpt completo)
        for i, c in enumerate(q.get("competitors_cited", [])[:2], 1):
            part += f"  Competidor {i} citado: {c['url']}\n"
            part += f"    Fragmento: \"{c['excerpt'][:200]}\"\n"

        # Snippets de Google (Serper) cuando no hay datos del RAG experimental
        if not q.get("competitors_cited"):
            serper_snippets = competitor_snippets_by_query.get(qid, [])
            if serper_snippets:
                part += "  Competidores encontrados via búsqueda real (Google):\n"
                for s in serper_snippets[:3]:
                    part += f"    {s['url']}\n"
                    part += f"    Snippet: \"{s['snippet'][:200]}\"\n"

        rag_urls = [u for u in q.get("relevant_urls", []) if TARGET_DOMAIN in u]
        search_urls = search_urls_by_query.get(qid, [])

        if rag_urls:
            part += f"  URLs recuperadas por RAG judge: {', '.join(rag_urls[:3])}\n"
        if search_urls:
            part += f"  URLs encontradas por búsqueda real (Google): {', '.join(search_urls[:3])}\n"
            gap = [u for u in search_urls if u not in rag_urls]
            if gap:
                part += f"  ⚠ GAP DE RETRIEVAL: {', '.join(gap)} — aparece en búsqueda real pero el RAG judge no la recuperó\n"

        parts.append(part)

    # Nota solo si no hay NINGUNA evidencia de competidores (ni RAG ni Serper)
    has_competitor_data = any(
        q.get("competitors_cited") or competitor_snippets_by_query.get(q["query_id"])
        for q in queries[:MAX_QUERIES]
    )
    if not has_competitor_data:
        parts.append(
            "NOTA: No hay fragmentos de competidores disponibles para estas queries. "
            "Genera recomendaciones basándote en las 6 palancas GEO aplicadas al CONTENIDO ACTUAL de programamos.es. "
            "El campo `evidence` debe ser un fragmento del CONTENIDO ACTUAL que muestre la brecha a mejorar "
            "(texto que falta, estadísticas ausentes, estructura mejorable, etc.), no de un competidor."
        )

    return "\n".join(parts)


def _collect_relevant_urls(
    queries: List[Dict[str, Any]],
    search_urls_by_query: Optional[Dict[str, List[str]]] = None,
) -> List[str]:
    # 1 URL por query para mantener cobertura constante independientemente del batch size
    max_urls = len(queries[:MAX_QUERIES])

    seen: set[str] = set()
    urls: List[str] = []
    for q in queries:
        for url in q.get("relevant_urls", []):
            if url not in seen and TARGET_DOMAIN in url:
                seen.add(url)
                urls.append(url)

    search_found_any = False
    if search_urls_by_query:
        for search_urls in search_urls_by_query.values():
            for url in search_urls:
                if url not in seen and TARGET_DOMAIN in url:
                    seen.add(url)
                    urls.append(url)
                    search_found_any = True

    # El sitemap siempre complementa (no solo como fallback):
    # añade las páginas mejor rankeadas por keyword del sitemap que la búsqueda no encontró.
    # n=2 si la búsqueda ya trajo resultados, n=4 si no trajo nada.
    extra = _find_sitemap_urls(queries, existing=seen, n=1 if search_found_any else 4)
    urls.extend(extra)

    return urls[:max_urls]


def _assess_page(url: str, queries: List[Dict[str, Any]]) -> str:
    """Devuelve warnings a inyectar en pages_context. Vacío si no hay problemas."""
    from datetime import datetime, timezone

    warnings_list: List[str] = []

    lastmod = _SITEMAP_LASTMOD.get(url, "")
    if lastmod:
        try:
            dt = datetime.fromisoformat(lastmod.replace("Z", "+00:00"))
            age_years = (datetime.now(timezone.utc) - dt).days / 365
            if age_years > 3:
                warnings_list.append(
                    f"⚠ CONTENIDO ANTIGUO: esta página tiene ~{int(age_years)} años "
                    f"(lastmod: {lastmod}). Evalúa si conviene optimizarla o recomendar "
                    "crear contenido nuevo más específico."
                )
        except Exception:
            pass

    path = url.replace(f"https://{TARGET_DOMAIN}", "").replace("-", " ").replace("/", " ").lower()
    path_tokens = set(t for t in path.split() if len(t) > 3)
    query_tokens = set(
        w.lower() for q in queries for w in q.get("query_text", "").split() if len(w) > 3
    )
    if path_tokens and query_tokens and not (path_tokens & query_tokens):
        warnings_list.append(
            "⚠ POSIBLE TOPIC MISMATCH: la URL de esta página no comparte términos con las queries. "
            "Verifica si es el vehículo correcto antes de proponer mejoras de contenido."
        )

    return "\n".join(warnings_list)


def _build_pages_context(urls: List[str], queries: List[Dict[str, Any]]) -> str:
    if not urls:
        return "(No se encontraron URLs relevantes de programamos.es en estas queries.)"
    parts = []
    for url in urls:
        assessment = _assess_page(url, queries)
        content = _fetch_page_content(url)
        block = f"URL: {url}\n"
        if assessment:
            block += f"{assessment}\n"
        block += content
        parts.append(block)
    return "\n\n---\n\n".join(parts)


_CRITIC_TOOL: Dict[str, Any] = {
    "name": "critic_output",
    "description": "Revisa las recomendaciones GEO y marca cada una como pass/warn/fail.",
    "input_schema": {
        "type": "object",
        "properties": {
            "reviews": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer"},
                        "verdict": {"type": "string", "enum": ["pass", "warn", "fail"]},
                        "reason": {"type": "string"},
                    },
                    "required": ["index", "verdict", "reason"],
                },
            }
        },
        "required": ["reviews"],
    },
}

_CROSS_MODE_ALIASES = {
    "both": "both_modes",
    "experimental": "experimental_only",
    "live": "live_only",
}

_LEVER_ALIASES = {
    "citation": "citation_readiness",
    "authority": "authority_injection",
    "perplexity": "low_perplexity",
    "scannability": "machine_scannability",
    "machine": "machine_scannability",
    "clarity": "semantic_clarity",
    "semantic": "semantic_clarity",
    "caption": "caption_injection",
}

_VALID_LEVERS = {"citation_readiness", "authority_injection", "low_perplexity", "machine_scannability", "semantic_clarity", "caption_injection"}
_VALID_IMPACTS = {"alto", "medio", "bajo"}
_VALID_EFFORTS = {"xs", "s", "m", "l"}
_VALID_CROSS_MODES = {"experimental_only", "live_only", "both_modes", "unknown"}

_FIELD_ALIASES: Dict[str, List[str]] = {
    "where": ["location", "url", "page", "page_url", "target_url", "where_to_apply"],
    "why": ["reason", "explanation", "rationale", "justification"],
    "target_query_ids": ["queries", "query_ids", "affected_queries", "target_queries"],
    "evidence": ["competitor_evidence", "competitor_fragment", "fragment", "quote"],
}


def _coerce_enum(key: str, value: str) -> str:
    """Normaliza valores de enum: lowercase, espacios/guiones → underscore, alias conocidos."""
    v = value.lower().replace(" ", "_").replace("-", "_")
    if key == "cross_mode_signal":
        v = _CROSS_MODE_ALIASES.get(v, v)
    elif key == "lever":
        v = _LEVER_ALIASES.get(v, v)
    return v


def _coerce_recommendation(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Valida una recomendación individual con coerción máxima; None solo si faltan campos clave."""
    try:
        raw = dict(raw)

        # Resolver aliases de nombres de campo
        for canonical, aliases in _FIELD_ALIASES.items():
            if canonical not in raw:
                for alias in aliases:
                    if alias in raw:
                        raw[canonical] = raw[alias]
                        break

        # target_query_ids: string CSV → lista, filtrar None por si Claude incluye nulls
        tqids = raw.get("target_query_ids")
        if not tqids:
            raw["target_query_ids"] = ["unknown"]
        elif isinstance(tqids, str):
            raw["target_query_ids"] = [s.strip() for s in tqids.split(",") if s.strip()] or ["unknown"]
        elif isinstance(tqids, list):
            raw["target_query_ids"] = [str(s) for s in tqids if s is not None] or ["unknown"]

        # Normalizar enums con aliases
        for key in ("lever", "impact", "effort", "cross_mode_signal"):
            if isinstance(raw.get(key), str):
                raw[key] = _coerce_enum(key, raw[key])

        # Enums required: si el valor no es válido, usar default en vez de fallar
        if raw.get("lever") not in _VALID_LEVERS:
            raw["lever"] = "semantic_clarity"
        if raw.get("impact") not in _VALID_IMPACTS:
            raw["impact"] = "medio"

        # Enums opcionales: si el valor no es válido, eliminar (quedan None)
        for key, valid_set in (("effort", _VALID_EFFORTS), ("cross_mode_signal", _VALID_CROSS_MODES)):
            if key in raw and raw[key] not in valid_set:
                del raw[key]

        # confidence: clamp a [0,1] si está fuera de rango
        if isinstance(raw.get("confidence"), (int, float)):
            raw["confidence"] = max(0.0, min(1.0, float(raw["confidence"])))

        # Campos string requeridos: placeholder si faltan
        for field_name in ("title", "where", "why", "evidence"):
            if not raw.get(field_name):
                raw[field_name] = "(no disponible)"

        from src.optimizer.schema import RecommendationL1
        return RecommendationL1(**raw).model_dump()
    except Exception as e:
        logger.warning("_coerce_recommendation falló — %s: %s | keys=%s", type(e).__name__, e, list(raw.keys()) if isinstance(raw, dict) else "?")
        return None


class GEOOptimizer:
    _COMPETITORS_PATH = PROJECT_ROOT / "data" / "frozen_competitors.json"

    def __init__(self):
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("ANTHROPIC_API_KEY no está configurada.")
        self._prompt_config = get_prompt("geo_optimizer")
        self._competitor_domains_list = self._load_competitor_domains()
        self._competitor_domains = set(self._competitor_domains_list)

    @classmethod
    def _load_competitor_domains(cls) -> List[str]:
        """Carga los dominios del set congelado de competidores (Discovery)."""
        try:
            with open(cls._COMPETITORS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(
                "No se pudo cargar %s (%s); el filtrado de snippets Serper quedará vacío.",
                cls._COMPETITORS_PATH, e,
            )
            return []
        return [d.lower() for d in data.get("top_competitors", [])]

    def _url_is_known_competitor(self, url: str) -> bool:
        """Devuelve True si el dominio de la URL está en el set de competidores congelados."""
        if not self._competitor_domains:
            return False
        try:
            netloc = urlparse(url).netloc.lower()
        except Exception:
            return False
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return any(netloc == d or netloc.endswith("." + d) for d in self._competitor_domains)

    def _search_query(self, query_text: str) -> List[str]:
        """Busca en Google vía Serper API y devuelve URLs de TARGET_DOMAIN."""
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key:
            return []
        import requests as _req
        r = _req.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": f"site:{TARGET_DOMAIN} {query_text}", "num": 10, "gl": "es", "hl": "es"},
            timeout=10,
        )
        r.raise_for_status()
        urls: List[str] = []
        for item in r.json().get("organic", []):
            link = item.get("link", "")
            if TARGET_DOMAIN in link and link not in urls:
                urls.append(link)
        return urls

    def _search_competitor_snippets(self, query_text: str) -> List[Dict[str, str]]:
        """Busca en Google restringiendo a los competidores del set congelado y devuelve hasta 3 snippets.

        La query se construye como ``{query} (site:dom1 OR site:dom2 OR ...)`` con los dominios
        de ``top_competitors`` del Discovery, para que Google priorice resultados de esos sitios.
        Adicionalmente se aplica un filtro defensivo sobre los resultados.
        """
        api_key = os.getenv("SERPER_API_KEY")
        if not api_key or not self._competitor_domains_list:
            return []
        site_clause = " OR ".join(f"site:{d}" for d in self._competitor_domains_list)
        scoped_query = f"{query_text} ({site_clause})"
        import requests as _req
        r = _req.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": scoped_query, "num": 10, "gl": "es", "hl": "es"},
            timeout=10,
        )
        r.raise_for_status()
        results: List[Dict[str, str]] = []
        for item in r.json().get("organic", []):
            url = item.get("link", "")
            if TARGET_DOMAIN in url:
                continue
            if not self._url_is_known_competitor(url):
                continue
            snippet = item.get("snippet", "")
            if snippet:
                results.append({"url": url, "title": item.get("title", ""), "snippet": snippet})
            if len(results) >= 3:
                break
        return results

    async def _discover_urls_via_search(
        self, queries: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Búsqueda por query vía Serper (sin rate limit de Gemini).
        Cada query busca exactamente sus páginas relevantes en Google.
        """
        result: Dict[str, List[str]] = {}
        for q in queries[:MAX_QUERIES]:
            qid = q["query_id"]
            try:
                result[qid] = await asyncio.to_thread(self._search_query, q["query_text"])
            except Exception:
                result[qid] = []
        return result

    async def _discover_competitor_snippets(
        self, queries: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """Snippets de competidores via Serper (sin site: prefix). Paralelo a _discover_urls_via_search."""
        result: Dict[str, List[Dict[str, str]]] = {}
        for q in queries[:MAX_QUERIES]:
            qid = q["query_id"]
            try:
                result[qid] = await asyncio.to_thread(
                    self._search_competitor_snippets, q["query_text"]
                )
            except Exception:
                result[qid] = []
        return result

    def _critic_pass(
        self,
        recommendations: List[Dict[str, Any]],
        queries_context: str,
        pages_context: str,
    ) -> List[Dict[str, Any]]:
        """Filtra con Haiku las recomendaciones con evidencia claramente fabricada.
        Guardia: si eliminaría >50% de las recomendaciones, devuelve todo (contexto insuficiente).
        """
        if not recommendations:
            return recommendations
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        recs_text = "\n".join(
            f"[{i}] lever={r.get('lever')} | evidence='{r.get('evidence', '')[:150]}'"
            f" | where={r.get('where', '')[:100]}"
            for i, r in enumerate(recommendations)
        )
        critic_system = (
            "Eres un revisor crítico de recomendaciones GEO. Solo marca como 'fail' evidencia "
            "CLARAMENTE inventada: afirmaciones sociales sin fuente ('docentes españoles han identificado...'), "
            "datos numéricos de plataformas externas (usuarios, fechas, porcentajes) que no aparezcan "
            "en el contexto, o citas textuales entrecomilladas que no existen en el contexto.\n"
            "- pass: evidencia presente o plausible como substring del contexto.\n"
            "- warn: evidencia no localizable exactamente pero no claramente inventada.\n"
            "- fail: solo para fabricación obvia. En caso de duda, usa warn, nunca fail."
        )
        critic_user = (
            f"CONTEXTO DE QUERIES:\n{queries_context[:4000]}\n\n"
            f"CONTENIDO DE PÁGINAS:\n{pages_context[:4000]}\n\n"
            f"RECOMENDACIONES A REVISAR:\n{recs_text}"
        )
        try:
            response = client.messages.create(
                model=_CRITIC_MODEL,
                max_tokens=1024,
                system=critic_system,
                messages=[{"role": "user", "content": critic_user}],
                tools=[_CRITIC_TOOL],
                tool_choice={"type": "tool", "name": "critic_output"},
            )
            for block in response.content:
                if block.type == "tool_use":
                    reviews = {r["index"]: r for r in block.input.get("reviews", [])}
                    filtered = [
                        rec for i, rec in enumerate(recommendations)
                        if reviews.get(i, {}).get("verdict", "pass") != "fail"
                    ]
                    # Guardia: si el critic eliminaría más del 50%, el contexto era insuficiente
                    if len(filtered) < len(recommendations) / 2:
                        return recommendations
                    return filtered
        except Exception:
            pass
        return recommendations  # safe fallback: si el critic falla, devolver todo

    def _call_claude(self, user_message: str) -> Dict[str, Any]:
        """Análisis con Claude Sonnet via tool use — structured output nativo, sin parsing frágil."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY no está configurada.")
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=_CLAUDE_MODEL,
            max_tokens=self._prompt_config.get("max_tokens", 8192),
            system=self._prompt_config["system"],
            messages=[{"role": "user", "content": user_message}],
            tools=[_CLAUDE_TOOL],
            tool_choice={"type": "tool", "name": "geo_optimizer_output"},
        )
        for block in response.content:
            if block.type == "tool_use":
                return block.input  # type: ignore[return-value]
        raise RuntimeError(
            f"Claude no devolvió tool_use. stop_reason={response.stop_reason}, "
            f"content_types={[b.type for b in response.content]}"
        )

    async def analyze(
        self,
        queries: List[Dict[str, Any]],
        run_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Búsqueda de URLs propias y snippets de competidores en paralelo
        search_urls_by_query, competitor_snippets_by_query = await asyncio.gather(
            self._discover_urls_via_search(queries),
            self._discover_competitor_snippets(queries),
        )

        queries_context = _build_queries_context(
            queries, search_urls_by_query, competitor_snippets_by_query
        )
        relevant_urls = _collect_relevant_urls(queries, search_urls_by_query)
        pages_context = _build_pages_context(relevant_urls, queries)

        user_message = self._prompt_config["user_template"].format(
            queries_context=queries_context,
            pages_context=pages_context,
        )

        tool_result = await asyncio.to_thread(self._call_claude, user_message)

        # Tool use devuelve dict con el schema exacto — validar con Pydantic
        try:
            result = GEOOptimizerOutput(**tool_result).model_dump()
        except (ValidationError, Exception) as top_err:
            # Coerción leniente si algún campo no encaja exactamente
            logger.warning("GEOOptimizerOutput validation error: %s: %s", type(top_err).__name__, top_err)
            recs_raw = tool_result.get("recommendations_l1", [])
            recs = [r for raw in recs_raw if (r := _coerce_recommendation(raw)) is not None]
            result = {"recommendations_l1": recs, "prompt_l2": tool_result.get("prompt_l2", "")}
            if not recs and recs_raw:
                result["_parse_error"] = (
                    f"El agente optimizer devolvió recomendaciones pero no pasaron la validación de schema "
                    f"({type(top_err).__name__}: {str(top_err)[:120]})."
                )

        # Critic pass: filtra recomendaciones con evidencia fabricada
        result["recommendations_l1"] = await asyncio.to_thread(
            self._critic_pass,
            result["recommendations_l1"],
            queries_context,
            pages_context,
        )

        result["run_id"] = run_id
        result["query_ids"] = [q["query_id"] for q in queries]
        result["prompt_version"] = self._prompt_config["version"]
        result["model"] = _CLAUDE_MODEL
        return result
