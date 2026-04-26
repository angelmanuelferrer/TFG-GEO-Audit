from __future__ import annotations

import pathlib
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = pathlib.Path(__file__).parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Directorio raíz de datos del proyecto
    data_dir: pathlib.Path = PROJECT_ROOT / "data"

    # API key para autenticación (opcional; si está vacío, modo dev sin auth)
    dashboard_api_key: Optional[str] = None

    # CORS: dominios permitidos separados por coma
    allowed_origins: str = "http://localhost:5173,http://localhost:3000,http://localhost:8080"

    # Ruta de la base de datos SQLite de jobs
    jobs_db_path: pathlib.Path = PROJECT_ROOT / "backend" / "jobs.db"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
