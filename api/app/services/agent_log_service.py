from typing import Any, Dict, List, Optional
from datetime import datetime

from api.app.db import get_conn


def ensure_agent_log_table() -> None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_query_log (
                    id SERIAL PRIMARY KEY,
                    question TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    latency_ms INT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW()
                );
                """
            )
        conn.commit()
    finally:
        conn.close()


def insert_agent_log(
    *,
    question: str,
    mode: str,
    latency_ms: int,
    status: str,
    error: Optional[str] = None,
) -> None:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO agent_query_log (question, mode, latency_ms, status, error)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (question, mode, latency_ms, status, error),
            )
        conn.commit()
    finally:
        conn.close()


def fetch_agent_history(limit: int = 20) -> List[Dict[str, Any]]:
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, question, mode, latency_ms, status, error, created_at
                FROM agent_query_log
                ORDER BY id DESC
                LIMIT %s;
                """,
                (limit,),
            )
            rows = cur.fetchall()

        out = []
        for r in rows:
            out.append(
                {
                    "id": r[0],
                    "question": r[1],
                    "mode": r[2],
                    "latency_ms": r[3],
                    "status": r[4],
                    "error": r[5],
                    "created_at": r[6].isoformat() if hasattr(r[6], "isoformat") else str(r[6]),
                }
            )
        return out
    finally:
        conn.close()
