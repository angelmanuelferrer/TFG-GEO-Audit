"""Gestión de jobs async: lanzar pipelines GEO desde el dashboard.

Almacena el estado en SQLite (jobs.db) y ejecuta los scripts como subprocesos
en un hilo de fondo. No bloquea el event-loop de FastAPI.

Tipos de job:
  experimental — scripts/run_experimental.py [--block R1|R2|R3|R4]
  live         — collect_metrics/collect_geo_live.py --engines ... --tier ...
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.settings import PROJECT_ROOT, settings

_DB = settings.jobs_db_path

# ── Helpers DB ────────────────────────────────────────────────────────────────

def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(str(_DB), check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


_REQUIRED_COLUMNS = {"job_id", "type", "status", "params", "output", "run_id", "created_at", "updated_at"}


def init_db() -> None:
    _DB.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id     TEXT PRIMARY KEY,
                type       TEXT NOT NULL,
                status     TEXT NOT NULL,
                params     TEXT NOT NULL,
                output     TEXT NOT NULL DEFAULT '',
                run_id     TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        # Si la tabla existía con un schema antiguo, recrearla
        cols = {row[1] for row in c.execute("PRAGMA table_info(jobs)")}
        if not _REQUIRED_COLUMNS.issubset(cols):
            c.execute("DROP TABLE jobs")
            c.execute("""
                CREATE TABLE jobs (
                    job_id     TEXT PRIMARY KEY,
                    type       TEXT NOT NULL,
                    status     TEXT NOT NULL,
                    params     TEXT NOT NULL,
                    output     TEXT NOT NULL DEFAULT '',
                    run_id     TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
        c.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row(row: sqlite3.Row) -> Dict[str, Any]:
    d = dict(row)
    d["params"] = json.loads(d["params"])
    return d


def _update(job_id: str, **kw) -> None:
    kw["updated_at"] = _now()
    clause = ", ".join(f"{k} = ?" for k in kw)
    with _conn() as c:
        c.execute(f"UPDATE jobs SET {clause} WHERE job_id = ?", [*kw.values(), job_id])
        c.commit()


# ── API pública ───────────────────────────────────────────────────────────────


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()
    return _row(row) if row else None


def list_jobs(limit: int = 30) -> List[Dict[str, Any]]:
    with _conn() as c:
        rows = c.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row(r) for r in rows]


def _any_running(job_type: str) -> bool:
    with _conn() as c:
        row = c.execute(
            "SELECT 1 FROM jobs WHERE type = ? AND status IN ('pending','running')",
            (job_type,),
        ).fetchone()
    return row is not None


# ── Runner ────────────────────────────────────────────────────────────────────

_RUN_ID_RE = re.compile(r"(run_\d{8}_\d{6}|LIVE-\d{4}-W\d{2})")


def _run(job_id: str, cmd: List[str]) -> None:
    def target() -> None:
        _update(job_id, status="running")
        lines: List[str] = []
        detected: Optional[str] = None

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(PROJECT_ROOT),
            )
            assert proc.stdout
            for line in proc.stdout:
                lines.append(line)
                if detected is None:
                    m = _RUN_ID_RE.search(line)
                    if m:
                        detected = m.group(1)
                if len(lines) % 5 == 0:
                    _update(job_id, output="".join(lines))

            proc.wait()
            final = "".join(lines)
            if proc.returncode == 0:
                _update(job_id, status="done", output=final, run_id=detected)
            else:
                _update(job_id, status="error", output=final)

        except Exception as exc:
            _update(job_id, status="error", output=f"Error al lanzar proceso: {exc}")

    threading.Thread(target=target, daemon=True).start()


def _create(job_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    job_id = str(uuid.uuid4())
    now = _now()
    with _conn() as c:
        c.execute(
            "INSERT INTO jobs (job_id,type,status,params,output,run_id,created_at,updated_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (job_id, job_type, "pending", json.dumps(params), "", None, now, now),
        )
        c.commit()
    return get_job(job_id)  # type: ignore[return-value]


# ── Entrypoints ───────────────────────────────────────────────────────────────


def launch_experimental(block: Optional[str] = None) -> Dict[str, Any]:
    """Lanza scripts/run_experimental.py en background."""
    if _any_running("experimental"):
        raise RuntimeError("Ya hay un run experimental en curso.")

    job = _create("experimental", {"block": block})
    cmd = [sys.executable, str(PROJECT_ROOT / "scripts" / "run_experimental.py")]
    if block:
        cmd += ["--block", block]
    _run(job["job_id"], cmd)
    return job


def launch_live(engines: List[str], tier: str) -> Dict[str, Any]:
    """Lanza collect_metrics/collect_geo_live.py en background."""
    if _any_running("live"):
        raise RuntimeError("Ya hay una evaluación live en curso.")

    job = _create("live", {"engines": engines, "tier": tier})
    cmd = [
        sys.executable,
        str(PROJECT_ROOT / "collect_metrics" / "collect_geo_live.py"),
        "--engines", *engines,
        "--tier", tier,
    ]
    _run(job["job_id"], cmd)
    return job
