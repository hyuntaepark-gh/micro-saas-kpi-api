from fastapi import APIRouter, HTTPException

from api.app.services.job_store import get_job, list_jobs

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", summary="Get async job status/result")
def read_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Job not found"}})
    return job


@router.get("/jobs", summary="List recent async jobs")
def recent_jobs(limit: int = 20):
    return list_jobs(limit=limit)
