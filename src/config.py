"""
Cargador centralizado de configuracion del sistema GEO-Audit.

Proporciona acceso a la configuracion del experimento y al set de queries
desde los ficheros JSON en config/.
"""

import json
from pathlib import Path

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
    """Carga el set fijo de queries desde config/queries.json.

    Devuelve dict con 'total', 'categories' (informacional, comparativa,
    navegacional) y metadatos de version.
    """
    return _load_json(CONFIG_DIR / "queries.json")


def get_all_queries() -> list[str]:
    """Devuelve las 15 queries como lista plana."""
    data = load_queries()
    queries = []
    for category in data["categories"].values():
        queries.extend(category)
    return queries


def get_discovery_queries() -> list[str]:
    """Devuelve solo queries informacionales + comparativas (sin navegacionales).

    Las navegacionales preguntan por el target (Programamos), no aportan
    competidores reales y distorsionan el ranking del discovery.
    """
    data = load_queries()
    categories = data["categories"]
    return categories.get("informacional", []) + categories.get("comparativa", [])


def get_target_url() -> str:
    """Devuelve la URL objetivo del experimento."""
    return load_experiment_config()["target_url"]


def get_target_brand() -> str:
    """Devuelve la marca objetivo del experimento."""
    return load_experiment_config()["target_brand"]
