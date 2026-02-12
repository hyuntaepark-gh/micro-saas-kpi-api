# api/routers/kpi.py

import os
import re
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text

# Deterministic parsing (NO LLM SQL generation)
from api.app.services.ask_service import parse_question
from api.app.services.analyze_service import build_metric_sql

router = APIRouter(prefix="/kpi", tags=["kpi"])


# ----------------------------
# Database configuration
# ----------------------------
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

# Default Docker connection
if not DATABASE_URL:
    DATABASE_URL = "postgresql+psycopg://admin:admin123@postgres:5432/analytics"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


# ----------------------------
# Request / Response Models
# ----------------------------
class KPIQueryRequest(BaseModel):
    question: str = Field(..., examples=["Why did revenue drop?"])
    max_rows: int = 200
    style: Optional[str] = Field(default="executive")


class RiskVisual(BaseModel):
    badge_color: str
    arrow: str


class KPIQueryResponse(BaseModel):
    ok: bool
    question: str
    parsed: Dict[str, str]
    sql: str
    rows: List[Dict[str, Any]]
    risk_score: float
    risk_visual: RiskVisual
    notes: Optional[List[str]] = None


# ----------------------------
# Risk Score Logic (Demo Heuristic)
# ----------------------------
def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def compute_risk_score(rows: List[Dict[str, Any]]) -> float:
    """
    Demo risk scoring:
    - Prefer return_rate / late_rate if available
    - Otherwise fallback to revenue volatility
    """

    if not rows:
        return 0.0

    keys = set().union(*[r.keys() for r in rows])

    # Risk based on return_rate / late_rate
    if "return_rate" in keys or "late_rate" in keys:
        rr = []
        lr = []

        for r in rows:
            if "return_rate" in r and r["return_rate"] is not None:
                rr.append(float(r["return_rate"]))
            if "late_rate" in r and r["late_rate"] is not None:
                lr.append(float(r["late_rate"]))

        rr_avg = sum(rr) / len(rr) if rr else 0.0
        lr_avg = sum(lr) / len(lr) if lr else 0.0

        score = (rr_avg * 100 * 0.6) + (lr_avg * 100 * 0.4)
        return clamp(score, 0, 100)

    # Revenue volatility fallback
    if "revenue" in keys:
        rev = [float(r["revenue"]) for r in rows if r.get("revenue") is not None]
        if len(rev) >= 3:
            mean = sum(rev) / len(rev)
            if mean > 0:
                var = sum((x - mean) ** 2 for x in rev) / (len(rev) - 1)
                std = var ** 0.5
                cv = std / mean
                score = (cv - 0.05) / (0.35 - 0.05) * 100
                return clamp(score, 0, 100)

    return 25.0


# ----------------------------
# Risk Visual Helper
# ----------------------------
def risk_visual_from_score(score: float, rows: List[Dict[str, Any]]) -> RiskVisual:

    if score < 33:
        color = "green"
    elif score < 66:
        color = "yellow"
    else:
        color = "red"

    arrow = "→"

    if rows:
        keys = set().union(*[r.keys() for r in rows])

        metric = None
        if "revenue" in keys:
            metric = "revenue"
        elif "return_rate" in keys:
            metric = "return_rate"
        elif "late_rate" in keys:
            metric = "late_rate"

        if metric:
            vals = [r.get(metric) for r in rows if r.get(metric) is not None]
            if len(vals) >= 2:
                prev = float(vals[-2])
                last = float(vals[-1])

                if last > prev:
                    arrow = "↑"
                elif last < prev:
                    arrow = "↓"

    return RiskVisual(badge_color=color, arrow=arrow)


# ----------------------------
# SQL Safety Guard
# ----------------------------
FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create)\b", re.IGNORECASE
)


def assert_safe_sql(sql: str) -> None:
    s = sql.strip().strip(";")

    if not s.lower().startswith("select"):
        raise HTTPException(status_code=400, detail="Only SELECT statements allowed.")

    if FORBIDDEN.search(s):
        raise HTTPException(status_code=400, detail="Unsafe SQL detected.")

    if ";" in s:
        raise HTTPException(status_code=400, detail="Multiple statements not allowed.")


# ----------------------------
# KPI Query Endpoint
# ----------------------------
@router.post("/query", response_model=KPIQueryResponse)
def query_kpi(req: KPIQueryRequest):
    """
    Full pipeline:
    question -> parse -> deterministic SQL -> DB -> risk scoring
    """

    # 1️⃣ Parse user question (NO LLM SQL)
    parsed = parse_question(req.question, style=req.style)

    metric = parsed["metric"]
    range_ = parsed["range"]
    style = parsed["style"]

    # 2️⃣ Build SAFE SQL
    sql = build_metric_sql(metric=metric, range_=range_)
    assert_safe_sql(sql)

    # 3️⃣ Execute query
    with engine.begin() as conn:
        result = conn.execute(text(sql))
        fetched = result.fetchmany(req.max_rows)
        cols = result.keys()
        rows = [dict(zip(cols, r)) for r in fetched]

    # 4️⃣ Risk scoring
    score = float(compute_risk_score(rows))
    visual = risk_visual_from_score(score, rows)

    # 5️⃣ Final response
    return KPIQueryResponse(
        ok=True,
        question=req.question,
        parsed=parsed,
        sql=sql,
        rows=rows,
        risk_score=round(score, 2),
        risk_visual=visual,
        notes=[
            "Deterministic SQL builder (no LLM usage).",
            "Risk score is heuristic (demo purpose).",
            "Only SELECT statements allowed.",
        ],
    )
