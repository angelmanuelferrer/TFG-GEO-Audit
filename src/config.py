"""
Cargador centralizado de configuracion del sistema GEO-Audit.

Proporciona acceso a la configuracion del experimento y al set de queries
desde los ficheros JSON en config/.
"""

import json
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"


def _load_json(filepath: Path) -> dict:
    """Lee y parsea un fichero JSON, con errores descriptivos."""
    if not filepath.exists():
        raise FileNotFoundError(
            f"Fichero de configuracion no encontrado: {filepath}\n"
            f"Asegurate de que existe en {CONFIG_DIR}/"
        )
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Error parseando JSON en {filepath}: {e}") from e


def load_experiment_config() -> dict:
    """Carga la configuracion del experimento desde config/experiment_config.json.

    Contiene: modelo RAG, embeddings, chunking, retrieval, competidores,
    evaluacion live y sentiment.
    """
    return _load_json(CONFIG_DIR / "experiment_config.json")


def load_queries() -> dict:
    """Carga el set de queries desde config/queries.json.

    Soporta v1 (lista plana por categorias) y v2 (queries con IDs y rotacion).
    """
    return _load_json(CONFIG_DIR / "queries.json")


def get_all_queries() -> list[str]:
    """Devuelve todas las queries como lista plana de textos."""
    data = load_queries()

    # v2 format: queries dict with IDs
    if "queries" in data and isinstance(data["queries"], dict):
        return [q["text"] for q in data["queries"].values()]

    # v1 format: categories dict with lists
    queries = []
    for category in data["categories"].values():
        queries.extend(category)
    return queries


def get_core_queries() -> list[str]:
    """Devuelve las 20 queries core (se ejecutan siempre).

    Solo disponible en v2. En v1 devuelve todas las queries.
    """
    data = load_queries()

    if "rotation" in data and "queries" in data:
        core_ids = data["rotation"]["core"]
        return [data["queries"][qid]["text"] for qid in core_ids]

    # Fallback v1
    return get_all_queries()


def get_queries_for_run(block: Optional[str] = None) -> list[str]:
    """Devuelve las queries para un run: core 20 + bloque rotativo seleccionado.

    Parameters
    ----------
    block : str or None
        Bloque rotativo: "R1", "R2", "R3", "R4", or None (solo core).

    Returns
    -------
    list[str] — 20 queries si block=None, 40 si se especifica bloque.
    """
    data = load_queries()

    if "rotation" not in data or "queries" not in data:
        # v1 fallback
        return get_all_queries()

    rotation = data["rotation"]
    queries_db = data["queries"]

    # Core queries (siempre)
    core_ids = rotation["core"]
    result = [queries_db[qid]["text"] for qid in core_ids]

    # Bloque rotativo (opcional)
    if block is not None:
        if block not in rotation:
            valid = [k for k in rotation if k != "core"]
            raise ValueError(
                f"Bloque '{block}' no valido. Bloques disponibles: {valid}"
            )
        block_ids = rotation[block]
        result.extend([queries_db[qid]["text"] for qid in block_ids])

    return result


def get_discovery_queries() -> list[str]:
    """Devuelve solo queries informacionales + comparativas (sin navegacionales).

    Las navegacionales preguntan por el target (Programamos), no aportan
    competidores reales y distorsionan el ranking del discovery.
    """
    data = load_queries()

    # v2 format
    if "queries" in data and isinstance(data["queries"], dict):
        return [
            q["text"]
            for q in data["queries"].values()
            if q["category"] in ("informacional", "comparativa")
        ]

    # v1 format
    categories = data["categories"]
    return categories.get("informacional", []) + categories.get("comparativa", [])


def get_target_url() -> str:
    """Devuelve la URL objetivo del experimento."""
    return load_experiment_config()["target_url"]


def get_target_brand() -> str:
    """Devuelve la marca objetivo del experimento."""
    return load_experiment_config()["target_brand"]
