import time
from typing import Optional

from fastapi import APIRouter, Body, BackgroundTasks
from pydantic import BaseModel, Field, ConfigDict

from api.app.schemas import AskRequest
from api.app.services.agent import ask_agent
from api.app.services.ask_service import parse_question
from api.app.services.analyze_service import (
    build_metric_sql,
    fetch_metric_rows,
    build_narrative,
    build_llm_narrative,
)
from api.app.services.driver_service import build_driver_summary
from api.app.services.decision_service import build_decision_signals
from api.app.services.report_formatter import build_final_report
from api.app.services.agent_log_service import insert_agent_log, fetch_agent_history
from api.app.utils.request_id import new_request_id

from api.app.services.insight_service import (
    compute_latest_kpi_changes,
    detect_anomalies,
    simulate_kpi_what_if,
)

# Async job store
from api.app.services.job_store import (
    create_job,
    set_job_running,
    set_job_result,
    set_job_error,
)

router = APIRouter(tags=["agent"])


# =========================
# Request Models (Pydantic v2 style)
# =========================
class AgentQueryJSON(BaseModel):
    question: str
    model_config = ConfigDict(
        json_schema_extra={"example": {"question": "Why did revenue drop last month?"}}
    )


class InsightRequest(BaseModel):
    thresholds: Optional[dict[str, float]] = Field(
        default=None,
        description="Optional absolute pct-change thresholds (e.g., {'revenue':0.2})",
    )


class SimulationRequest(BaseModel):
    orders_delta_pct: float = Field(default=0.0, description="e.g. 0.10 means +10% orders")
    aov_delta_pct: float = Field(default=0.0, description="e.g. -0.05 means -5% AOV")
    customers_delta_pct: float = Field(default=0.0, description="Informational only")


# =========================
# Internal helper: run agent with robust fallback
# =========================
def _run_agent_with_fallback(question: str) -> dict:
    """
    Tries OpenAI agent first; if quota/error happens, falls back to legacy KPI analysis.
    Always returns a consistent payload with mode + final_report.
    """
    q = (question or "").strip()

    # 1) Try LLM agent (may fail due to quota)
    try:
        res = ask_agent(q)
        return {"mode": "agent_llm", "result": res}
    except Exception:
        pass

    # 2) Rule-based multi-metric fallback for generic "why/performance/drop"
    q_lower = q.lower()
    multi_keywords = ["performance", "business", "overall", "drop", "why"]
    if any(k in q_lower for k in multi_keywords):
        metrics = ["revenue", "orders", "customers", "aov"]
        outputs = []
        for m in metrics:
            legacy_payload = AskRequest(question=f"{m} last_3_months executive", style="executive")
            outputs.append(_ask_legacy_core(legacy_payload))

        driver_summary = build_driver_summary(outputs)
        decision = build_decision_signals(driver_summary)

        final_report = build_final_report(
            {
                "mode": "multi_metric_fallback",
                "style": "executive",
                "driver_summary": driver_summary,
                "decision": decision,
                "metrics": metrics,
            }
        )

        return {
            "mode": "multi_metric_fallback",
            "metrics": metrics,
            "driver_summary": driver_summary,
            "decision": decision,
            "final_report": final_report,
            "results": outputs,
        }

    # 3) Single-metric fallback by parsing question (legacy)
    legacy_payload = AskRequest(question=q, style="executive")
    legacy = _ask_legacy_core(legacy_payload)
    final_report = build_final_report({"mode": "fallback_legacy", "legacy": legacy})

    return {
        "mode": "fallback_legacy",
        "legacy": legacy,
        "final_report": final_report,
    }


def _ask_legacy_core(payload: AskRequest) -> dict:
    """
    Core legacy path (no FastAPI response models) – returns plain dict.
    """
    parsed = parse_question(payload.question, style=payload.style)

    sql = build_metric_sql(metric=parsed["metric"], range_=parsed["range"])
    rows = fetch_metric_rows(sql)

    try:
        narrative, risk, recommendation = build_llm_narrative(
            parsed["metric"],
            rows,
            style=parsed["style"],
        )
    except Exception:
        narrative, risk, recommendation = build_narrative(
            parsed["metric"],
            rows,
            style=parsed["style"],
        )

    return {
        "question": payload.question,
        "parsed": parsed,
        "result": {
            "metric": parsed["metric"],
            "range": parsed["range"],
            "style": parsed["style"],
            "sql": sql,
            "data": rows,
            "narrative": narrative,
            "risk": risk,
            "recommendation": recommendation,
        },
    }


# =========================
#  Product-grade debug trace (no chain-of-thought)
# =========================
def _build_debug_trace(question: str) -> dict:
    """
    Product-grade debug trace.
    - Does NOT expose chain-of-thought.
    - Shows which mode was used and what artifacts were produced.
    """
    q = (question or "").strip()
    trace = {
        "question": q,
        "steps": [],
        "mode": None,
    }

    # 1) Try LLM agent
    try:
        t0 = time.time()
        res = ask_agent(q)
        trace["steps"].append(
            {
                "name": "ask_agent",
                "status": "ok",
                "latency_ms": int((time.time() - t0) * 1000),
            }
        )
        trace["mode"] = "agent_llm"
        trace["artifacts"] = {
            "agent_result_keys": list(res.keys()) if isinstance(res, dict) else type(res).__name__
        }
        return trace
    except Exception as e:
        trace["steps"].append({"name": "ask_agent", "status": "failed", "error": str(e)[:200]})

    # 2) Decide fallback
    q_lower = q.lower()
    multi_keywords = ["performance", "business", "overall", "drop", "why"]
    if any(k in q_lower for k in multi_keywords):
        trace["mode"] = "multi_metric_fallback"
        trace["steps"].append({"name": "fallback_decision", "status": "ok", "reason": "multi_keywords_match"})
        return trace

    trace["mode"] = "fallback_legacy"
    trace["steps"].append({"name": "fallback_decision", "status": "ok", "reason": "single_metric_parse"})
    return trace


# =========================
#  Async job runner
# =========================
def _run_job(job_id: str, question: str):
    try:
        set_job_running(job_id)
        result = _run_agent_with_fallback(question)
        set_job_result(job_id, result)
    except Exception as e:
        set_job_error(job_id, str(e))


# =========================
# v1 Endpoints
# =========================
@router.post("/ask-text", summary="Ask (text/plain)")
def ask_text(question: str = Body(..., media_type="text/plain")):
    """
    Text/plain convenience endpoint.
    """
    request_id = new_request_id()
    t0 = time.time()

    payload = _run_agent_with_fallback(question)
    latency_ms = int((time.time() - t0) * 1000)

    # best-effort agent logging
    try:
        insert_agent_log(
            {
                "request_id": request_id,
                "question": question,
                "mode": payload.get("mode"),
                "status": "ok",
                "latency_ms": latency_ms,
            }
        )
    except Exception:
        pass

    payload.update({"request_id": request_id, "latency_ms": latency_ms})
    return payload


@router.post("/agent/query", summary="Agent Query (JSON)")
def agent_query(payload: AgentQueryJSON):
    request_id = new_request_id()
    t0 = time.time()

    result = _run_agent_with_fallback(payload.question)
    latency_ms = int((time.time() - t0) * 1000)

    try:
        insert_agent_log(
            {
                "request_id": request_id,
                "question": payload.question,
                "mode": result.get("mode"),
                "status": "ok",
                "latency_ms": latency_ms,
            }
        )
    except Exception:
        pass

    result.update({"request_id": request_id, "latency_ms": latency_ms})
    return result


# /v1/agent/query-async
@router.post("/agent/query-async", summary="Agent Query Async (returns job_id)")
def agent_query_async(payload: AgentQueryJSON, background_tasks: BackgroundTasks):
    job = create_job({"type": "agent_query", "input": {"question": payload.question}})
    job_id = job["job_id"]

    background_tasks.add_task(_run_job, job_id, payload.question)

    return {
        "status": "accepted",
        "job_id": job_id,
        "poll": f"/v1/jobs/{job_id}",
    }


@router.post("/ask-executive", summary="Executive Report Only")
def ask_executive(payload: AgentQueryJSON):
    """
    Returns ONLY the executive final_report string (clean CFO-style output).
    """
    request_id = new_request_id()
    t0 = time.time()

    full = _run_agent_with_fallback(payload.question)
    latency_ms = int((time.time() - t0) * 1000)

    final_report = full.get("final_report")
    if final_report is None:
        final_report = full.get("result")

    try:
        insert_agent_log(
            {
                "request_id": request_id,
                "question": payload.question,
                "mode": full.get("mode"),
                "status": "ok",
                "latency_ms": latency_ms,
            }
        )
    except Exception:
        pass

    return {
        "request_id": request_id,
        "mode": full.get("mode"),
        "latency_ms": latency_ms,
        "final_report": final_report,
    }


@router.get("/agent/history", summary="Agent Query History")
def agent_history(limit: int = 20):
    return {"data": fetch_agent_history(limit=limit)}


# /v1/agent/debug
@router.post("/agent/debug", summary="Debug trace (no chain-of-thought)")
def agent_debug(payload: AgentQueryJSON):
    request_id = new_request_id()
    t0 = time.time()

    trace = _build_debug_trace(payload.question)
    latency_ms = int((time.time() - t0) * 1000)

    return {
        "request_id": request_id,
        "latency_ms": latency_ms,
        "trace": trace,
    }


# =========================
# Product-grade endpoints
# =========================
@router.get("/agent/explain", summary="Driver breakdown only (no LLM)")
def agent_explain():
    """
    Rule-based driver explanation using latest 2 months (no OpenAI calls).
    """
    changes = compute_latest_kpi_changes()
    if changes.get("status") != "ok":
        return changes

    months = changes["months"]
    base, target = months[0], months[1]

    def pct(prev, cur):
        return (cur - prev) / prev if (prev is not None and cur is not None and prev != 0) else None

    return {
        "status": "ok",
        "previous_month": base.get("month"),
        "current_month": target.get("month"),
        "revenue": {
            "previous": base.get("revenue"),
            "current": target.get("revenue"),
            "pct_change": pct(base.get("revenue"), target.get("revenue")),
        },
        "orders": {
            "previous": base.get("orders"),
            "current": target.get("orders"),
            "pct_change": pct(base.get("orders"), target.get("orders")),
        },
        "aov": {
            "previous": base.get("aov"),
            "current": target.get("aov"),
            "pct_change": pct(base.get("aov"), target.get("aov")),
        },
        "note": "Revenue change is primarily explained by Orders and AOV. Use /v1/ask-executive for formatted executive output.",
    }


@router.post("/agent/insight", summary="Auto anomaly detection on latest KPI changes")
def agent_insight(payload: InsightRequest):
    """
    Detect KPI anomalies on latest 2 months (rule-based thresholds).
    """
    changes = compute_latest_kpi_changes()
    return detect_anomalies(changes, thresholds=payload.thresholds)


@router.post("/agent/simulate", summary="What-if simulation (Orders/AOV -> Revenue)")
def agent_simulate(payload: SimulationRequest):
    """
    Quick what-if simulation:
      Revenue ~ Orders * AOV
    """
    changes = compute_latest_kpi_changes()
    scenario = {
        "orders_delta_pct": payload.orders_delta_pct,
        "aov_delta_pct": payload.aov_delta_pct,
        "customers_delta_pct": payload.customers_delta_pct,
    }
    return simulate_kpi_what_if(changes, scenario)
