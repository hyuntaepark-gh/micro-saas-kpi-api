# api/routers/seed_demo.py

from datetime import date
from typing import List

from fastapi import APIRouter

from api.app.services.kpi_service import upsert_kpi
from api.app.db import get_conn

router = APIRouter(tags=["seed-demo"])


def _month_start(d: date) -> date:
    """Return the first day of the given date's month."""
    return date(d.year, d.month, 1)


def _add_months(d: date, months: int) -> date:
    """Add months to a date (month-anchored to day=1)."""
    y = d.year + (d.month - 1 + months) // 12
    m = (d.month - 1 + months) % 12 + 1
    return date(y, m, 1)


def _delete_kpi_months(months: List[date]) -> int:
    """
    Delete KPI rows for the provided month list.

    Assumes a table named `kpi_monthly` with a column `month` (DATE).
    If your table name differs, change the SQL here.
    """
    if not months:
        return 0

    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM kpi_monthly WHERE month = ANY(%s);",
                (months,),
            )
        conn.commit()
        return len(months)
    finally:
        conn.close()

@router.post("/seed-demo")
def seed_demo(months: int = 6, reset: bool = False, scenario: str = "revenue_drop"):
    """
    Inserts demo KPI data with a simulated scenario in the last month.

    Usage:
      POST /v1/seed-demo?months=6&reset=true&scenario=revenue_drop
      scenario options: revenue_drop | orders_drop | aov_drop
    """
    if months < 2:
        months = 2
    if months > 24:
        months = 24

    scenario = (scenario or "revenue_drop").lower().strip()
    if scenario not in {"revenue_drop", "orders_drop", "aov_drop"}:
        scenario = "revenue_drop"

    today = date.today()
    start_month = _month_start(_add_months(today, -months + 1))
    month_list = [_add_months(start_month, i) for i in range(months)]

    deleted = 0
    if reset:
        deleted = _delete_kpi_months(month_list)

    base_revenue = 100000.0
    base_orders = 1200
    base_customers = 800

    inserted = 0
    for idx, m in enumerate(month_list):
        revenue = base_revenue * (1.0 + 0.03 * idx)
        orders = int(base_orders * (1.0 + 0.02 * idx))
        customers = int(base_customers * (1.0 + 0.015 * idx))

        # Apply scenario on last month only
        if idx == len(month_list) - 1:
            if scenario == "revenue_drop":
                revenue = revenue * 0.80
            elif scenario == "orders_drop":
                orders = int(orders * 0.80)
            elif scenario == "aov_drop":
                # keep orders steady, reduce revenue to lower AOV
                revenue = revenue * 0.85

        aov = revenue / max(orders, 1)

        upsert_kpi(
            month=m,
            revenue=float(round(revenue, 2)),
            orders=int(orders),
            customers=int(customers),
            aov=float(round(aov, 2)),
        )
        inserted += 1

    return {
        "status": "ok",
        "months_inserted": inserted,
        "months_range": [month_list[0].isoformat(), month_list[-1].isoformat()],
        "reset": reset,
        "rows_deleted": deleted,
        "scenario": scenario,
    }
