from fastapi import APIRouter

from api.app.services.insight_service import compute_latest_kpi_changes, detect_anomalies

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard", summary="Dashboard JSON (for frontend MVP)")
def dashboard():
    changes = compute_latest_kpi_changes()
    anomalies = detect_anomalies(changes) if changes.get("status") == "ok" else changes

    # frontend-friendly
    return {
        "status": "ok",
        "kpi": {
            "latest_changes": changes,
            "anomalies": anomalies,
        },
        "suggested_widgets": [
            {"type": "kpi_cards", "source": "kpi.latest_changes"},
            {"type": "alerts", "source": "kpi.anomalies.alerts"},
            {"type": "risk_badge", "source": "kpi.anomalies.risk"},
        ],
    }
