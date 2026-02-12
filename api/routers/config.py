import os
from fastapi import APIRouter

from api.app.db import get_conn

router = APIRouter(tags=["meta"])

def _db_ok() -> bool:
    try:
        conn = get_conn()
        conn.close()
        return True
    except Exception:
        return False

@router.get("/config")
def config_status():
    # Do NOT expose secrets; only show whether configured.
    openai_key = os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_APIKEY")
    cors_origins = os.getenv("CORS_ORIGINS", "*")

    return {
        "openai_configured": bool(openai_key),
        "db_ok": _db_ok(),
        "cors_origins": cors_origins,
        "env": os.getenv("APP_ENV", "dev"),
    }
