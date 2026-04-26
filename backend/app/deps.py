from __future__ import annotations

from fastapi import Header, HTTPException, status

from app.settings import settings


def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Valida X-API-Key si DASHBOARD_API_KEY está configurada.
    En modo dev (sin la var de entorno) no valida nada.
    """
    if not settings.dashboard_api_key:
        return  # modo dev: sin auth
    if x_api_key != settings.dashboard_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key inválida o ausente",
        )
