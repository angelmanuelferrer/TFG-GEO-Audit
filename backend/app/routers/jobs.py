from __future__ import annotations

from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator

from app.deps import verify_api_key
from app.services import job_runner

router = APIRouter()


# ── Schemas de request ────────────────────────────────────────────────────────


class LaunchExperimentalParams(BaseModel):
    block: Optional[Literal["R1", "R2", "R3", "R4"]] = None


class LaunchLiveParams(BaseModel):
    engines: List[Literal["gemini", "claude", "openai"]] = ["gemini", "claude", "openai"]
    tier: Literal["core", "light", "medium", "full"] = "core"

    @field_validator("engines")
    @classmethod
    def at_least_one_engine(cls, v: list) -> list:
        if not v:
            raise ValueError("Se requiere al menos un motor.")
        return v


class JobRequest(BaseModel):
    type: Literal["experimental", "live"]
    params: dict = {}


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("", dependencies=[Depends(verify_api_key)], status_code=201)
def create_job(body: JobRequest):
    try:
        if body.type == "experimental":
            p = LaunchExperimentalParams(**body.params)
            return job_runner.launch_experimental(block=p.block)
        else:
            p = LaunchLiveParams(**body.params)
            return job_runner.launch_live(engines=p.engines, tier=p.tier)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("", dependencies=[Depends(verify_api_key)])
def list_jobs():
    jobs = job_runner.list_jobs()
    return {"items": jobs, "total": len(jobs)}


@router.get("/{job_id}", dependencies=[Depends(verify_api_key)])
def get_job(job_id: str):
    job = job_runner.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' no encontrado")
    return job
