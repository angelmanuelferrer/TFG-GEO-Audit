from __future__ import annotations

import json
import pathlib
from typing import Any, Dict, List, Optional

from app.settings import settings


def _seo_dir() -> pathlib.Path:
    return settings.data_dir / "seo"


def _load_json(path: pathlib.Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_seo_files() -> List[pathlib.Path]:
    base = _seo_dir()
    if not base.exists():
        return []
    files = sorted(
        [f for f in base.iterdir() if f.name.startswith("metrics_") and f.suffix == ".json"],
        key=lambda f: f.stem,
        reverse=True,
    )
    return files


def load_latest_seo() -> Optional[Dict[str, Any]]:
    files = list_seo_files()
    if not files:
        return None
    return _load_json(files[0])


def load_seo_history(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Carga todos los ficheros SEO, opcionalmente filtrados por rango de fecha.

    Las fechas son prefijos del campo 'fecha' (formato YYYY-MM-DD_HH-MM-SS).
    """
    result = []
    for f in reversed(list_seo_files()):  # cronológico ascendente
        data = _load_json(f)
        fecha = data.get("fecha", "")
        if from_date and fecha < from_date.replace("-", "").replace("T", "_")[:10]:
            continue
        if to_date and fecha[:10] > to_date[:10].replace("-", "")[:10]:
            continue
        result.append(data)
    return result
