from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple

from api.app.services.report_service import fetch_latest_two_months


@dataclass
class KPIChange:
    metric: str
    previous: Optional[float]
    current: Optional[float]
    delta: Optional[float]
    pct_change: Optional[float]


def _safe_div(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b in (None, 0):
        return None
    return a / b


def _change(prev: Optional[float], cur: Optional[float]) -> Tuple[Optional[float], Optional[float]]:
    if prev is None or cur is None:
        return None, None
    delta = cur - prev
    pct = _safe_div(delta, prev)
    return delta, pct


def compute_latest_kpi_changes() -> Dict[str, Any]:
    """
    Returns:
      {
        "months": [{"month": "...", "revenue":..., ...}, ...],
        "changes": [{"metric":..., "previous":..., "current":..., "delta":..., "pct_change":...}, ...]
      }
    """
    rows = fetch_latest_two_months()
    if len(rows) < 2:
        return {
            "status": "insufficient_data",
            "message": "Need at least 2 months in kpi_monthly to compute changes.",
            "months": rows,
            "changes": [],
        }

    base, target = rows[0], rows[1]

    metrics = ["revenue", "orders", "customers", "aov"]
    changes: List[Dict[str, Any]] = []
    for m in metrics:
        prev = base.get(m)
        cur = target.get(m)
        delta, pct = _change(prev, cur)
        changes.append(
            {
                "metric": m,
                "previous": prev,
                "current": cur,
                "delta": delta,
                "pct_change": pct,
            }
        )

    return {"status": "ok", "months": rows, "changes": changes}


def detect_anomalies(
    changes_payload: Dict[str, Any],
    thresholds: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Simple anomaly detector (rule-based).
    thresholds: pct_change thresholds (absolute). Default:
      revenue: 0.15, orders: 0.12, customers: 0.10, aov: 0.08
    """
    if thresholds is None:
        thresholds = {"revenue": 0.15, "orders": 0.12, "customers": 0.10, "aov": 0.08}

    if changes_payload.get("status") != "ok":
        return changes_payload

    alerts = []
    for c in changes_payload.get("changes", []):
        metric = c["metric"]
        pct = c.get("pct_change")
        if pct is None:
            continue
        th = thresholds.get(metric, 0.10)
        if abs(pct) >= th:
            direction = "UP" if pct > 0 else "DOWN"
            alerts.append(
                {
                    "metric": metric,
                    "direction": direction,
                    "pct_change": pct,
                    "threshold": th,
                    "message": f"{metric} moved {direction} by {pct:.1%} (>= {th:.0%})",
                }
            )

    risk = "LOW"
    if any(a["metric"] == "revenue" and a["direction"] == "DOWN" for a in alerts):
        risk = "HIGH"
    elif len(alerts) >= 2:
        risk = "MEDIUM"

    return {
        "status": "ok",
        "months": changes_payload["months"],
        "changes": changes_payload["changes"],
        "alerts": alerts,
        "risk": risk,
    }


def simulate_kpi_what_if(
    changes_payload: Dict[str, Any],
    scenario: Dict[str, float],
) -> Dict[str, Any]:
    """
    Scenario keys (optional):
      - orders_delta_pct: e.g. 0.10 means +10% orders
      - aov_delta_pct: e.g. -0.05 means -5% AOV
      - customers_delta_pct: e.g. 0.03 means +3% customers (informational)
    Uses Revenue ~ Orders * AOV for quick simulation.
    """
    if changes_payload.get("status") != "ok":
        return changes_payload

    # current month values
    current = changes_payload["months"][1]
    cur_orders = current.get("orders")
    cur_aov = current.get("aov")
    cur_revenue = current.get("revenue")

    od = scenario.get("orders_delta_pct", 0.0)
    ad = scenario.get("aov_delta_pct", 0.0)

    sim_orders = (cur_orders * (1 + od)) if cur_orders is not None else None
    sim_aov = (cur_aov * (1 + ad)) if cur_aov is not None else None

    sim_revenue = None
    if sim_orders is not None and sim_aov is not None:
        sim_revenue = sim_orders * sim_aov

    impact = None
    if cur_revenue is not None and sim_revenue is not None:
        impact = sim_revenue - cur_revenue

    return {
        "status": "ok",
        "base": {
            "orders": cur_orders,
            "aov": cur_aov,
            "revenue": cur_revenue,
        },
        "scenario": scenario,
        "simulated": {
            "orders": sim_orders,
            "aov": sim_aov,
            "revenue": sim_revenue,
        },
        "impact": {
            "revenue_delta": impact,
            "revenue_delta_pct": (impact / cur_revenue) if (impact is not None and cur_revenue) else None,
        },
    }
