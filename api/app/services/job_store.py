from __future__ import annotations

import threading
import time
import uuid
from typing import Any, Dict, Optional


_LOCK = threading.Lock()
_JOBS: Dict[str, Dict[str, Any]] = {}


def new_job_id() -> str:
    return uuid.uuid4().hex


def create_job(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload: { "type": "...", "input": {...} }
    """
    job_id = new_job_id()
    now = int(time.time())
    job = {
        "job_id": job_id,
        "status": "PENDING",  # PENDING | RUNNING | SUCCEEDED | FAILED
        "created_at": now,
        "updated_at": now,
        "payload": payload,
        "result": None,
        "error": None,
    }
    with _LOCK:
        _JOBS[job_id] = job
    return job


def set_job_running(job_id: str) -> None:
    with _LOCK:
        if job_id in _JOBS:
            _JOBS[job_id]["status"] = "RUNNING"
            _JOBS[job_id]["updated_at"] = int(time.time())


def set_job_result(job_id: str, result: Any) -> None:
    with _LOCK:
        if job_id in _JOBS:
            _JOBS[job_id]["status"] = "SUCCEEDED"
            _JOBS[job_id]["result"] = result
            _JOBS[job_id]["updated_at"] = int(time.time())


def set_job_error(job_id: str, error: str) -> None:
    with _LOCK:
        if job_id in _JOBS:
            _JOBS[job_id]["status"] = "FAILED"
            _JOBS[job_id]["error"] = error
            _JOBS[job_id]["updated_at"] = int(time.time())


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _LOCK:
        return _JOBS.get(job_id)


def list_jobs(limit: int = 20) -> Dict[str, Any]:
    with _LOCK:
        jobs = list(_JOBS.values())
    jobs.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return {"data": jobs[: max(1, min(limit, 200))]}
