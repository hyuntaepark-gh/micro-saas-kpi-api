from fastapi import APIRouter

router = APIRouter(tags=["meta"])

SUPPORTED_METRICS = ["revenue", "orders", "customers", "aov"]
SUPPORTED_RANGES = ["last_2_months", "last_3_months", "last_6_months", "ytd"]
SUPPORTED_STYLES = ["basic", "executive"]


@router.get("/version")
def version():
    return {
        "service": "micro-saas-kpi-api",
        "version": "1.0.0",
        "api": "v1",
    }


@router.get("/meta")
def meta():
    return {
        "capabilities": {
            "metrics": SUPPORTED_METRICS,
            "ranges": SUPPORTED_RANGES,
            "styles": SUPPORTED_STYLES,
        },
        "endpoints": [
            {"method": "POST", "path": "/v1/seed-demo", "desc": "Insert demo KPI data (supports reset)"},
            {"method": "POST", "path": "/v1/agent/query", "desc": "Main agent endpoint (JSON). LLM primary, fallback analytics."},
            {"method": "POST", "path": "/v1/ask-executive", "desc": "Executive report only (final_report)"},
            {"method": "GET", "path": "/v1/agent/history", "desc": "Agent query logs"},
            {"method": "GET", "path": "/v1/meta", "desc": "API capabilities + examples"},
            {"method": "GET", "path": "/v1/version", "desc": "Version info"},
        ],
        "example_questions": [
            "Why did revenue drop last month?",
            "Explain overall performance in the last 3 months.",
            "What should we do next to reduce risk?",
        ],
        "example_calls": {
            "seed_demo": {"method": "POST", "path": "/v1/seed-demo?months=6&reset=true"},
            "agent_query": {"method": "POST", "path": "/v1/agent/query", "json": {"question": "Why did revenue drop last month?"}},
            "executive": {"method": "POST", "path": "/v1/ask-executive", "json": {"question": "Summarize performance and risks."}},
        },
    }
