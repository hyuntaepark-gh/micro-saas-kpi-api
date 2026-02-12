from __future__ import annotations

from typing import Tuple, Optional, Dict, Any, List
from datetime import date

from ..db import get_conn

import os
from openai import OpenAI


# -----------------------------
# SQL Builder
# -----------------------------

def _range_to_limit(range_: str) -> Optional[int]:
    """
    Demo MVP: Use LIMIT over month DESC ordering.
    """
    if range_ == "last_2_months":
        return 2
    if range_ == "last_3_months":
        return 3
    if range_ == "last_6_months":
        return 6
    return None  # ytd / all


def build_metric_sql(metric: str, range_: str) -> str:
    """
    Build the *actual SQL* used for KPI retrieval.
    NOTE: We always fetch all KPI columns so downstream driver/risk logic can use them.
    Metric is used mainly for semantics (what we narrate), not for column selection.
    """
    limit = _range_to_limit(range_)

    base = """
SELECT month, revenue, orders, customers, aov
FROM kpi_monthly
ORDER BY month DESC
""".strip()

    if limit:
        base += f"\nLIMIT {limit};"
    else:
        base += ";"

    return base


def fetch_metric_rows(sql: str) -> List[Dict[str, Any]]:
    conn = get_conn(dict_cursor=True)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    # We ordered DESC, but for narrative it’s nicer ASC
    return list(reversed(rows))


# -----------------------------
# Rule-based Narrative
# -----------------------------

def build_narrative(metric: str, rows: List[Dict[str, Any]], style: str = "executive") -> Tuple[str, str, str]:
    if not rows:
        return ("No data found.", "No risk signals.", "Insert KPI data first.")

    first = rows[0]
    last = rows[-1]

    def pct_change(a: Optional[float], b: Optional[float]) -> Optional[float]:
        if a in (None, 0):
            return None
        return (b - a) / a

    metric_map = {
        "revenue": "revenue",
        "orders": "orders",
        "customers": "customers",
        "aov": "aov",
    }
    col = metric_map.get(metric, "revenue")

    start = float(first[col])
    end = float(last[col])
    chg = end - start
    chg_pct = pct_change(start, end)

    direction = "increased" if chg > 0 else "decreased" if chg < 0 else "was flat"

    if chg_pct is None:
        headline = f"{metric.upper()} {direction} from {first['month']} to {last['month']}."
    else:
        headline = f"{metric.upper()} {direction} from {first['month']} to {last['month']} ({chg_pct*100:.1f}%)."

    risk = "No major risk signals detected."
    recommendation = "Keep monitoring trends."

    if metric == "revenue":
        # check if revenue up but AOV down = discount risk
        aov_start, aov_end = float(first["aov"]), float(last["aov"])
        orders_start, orders_end = float(first["orders"]), float(last["orders"])
        aov_pct = pct_change(aov_start, aov_end)
        orders_pct = pct_change(orders_start, orders_end)

        if aov_pct is not None and aov_pct < -0.10:
            risk = "AOV dropped materially; revenue growth may be discount-driven."
            recommendation = "Audit discounts, review product mix, and protect margin."
        elif orders_pct is not None and orders_pct < -0.10:
            risk = "Orders dropped materially; demand or funnel may be weakening."
            recommendation = "Investigate acquisition, conversion funnel, and retention actions."
        else:
            recommendation = "Identify which lever moved most (orders vs AOV) and double-down on that driver."

    if style == "brief":
        narrative = headline
    elif style == "detailed":
        narrative = (
            f"{headline} "
            f"Start={start:.2f}, End={end:.2f}, Change={chg:.2f}. "
            f"Data points={len(rows)}."
        )
    else:
        narrative = f"{headline} Focus on the dominant driver and monitor downside risks."

    return (narrative, risk, recommendation)


# -----------------------------
# LLM Narrative (with fallback)
# -----------------------------

def _get_client() -> Optional[OpenAI]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    return OpenAI(api_key=key)


def build_llm_narrative(metric: str, rows: List[Dict[str, Any]], style: str = "executive") -> Tuple[str, str, str]:
    """
    LLM-powered narrative.
    Returns (narrative, risk, recommendation).
    Falls back to rule-based build_narrative() if LLM fails or API key missing.
    """
    if not rows:
        return ("No data found.", "No risk signals.", "Insert KPI data first.")

    client = _get_client()
    if client is None:
        return build_narrative(metric, rows, style=style)

    try:
        prompt = f"""
You are a senior analytics consultant. Write in {style} tone.

Metric: {metric}
Data (monthly rows, oldest -> newest):
{rows}

Return EXACTLY in this format:
INSIGHT: <one paragraph>
RISK: <one paragraph>
RECOMMENDATION: <one paragraph>
""".strip()

        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )

        text = (resp.choices[0].message.content or "").strip()

        def _pick(prefix: str) -> str:
            for line in text.splitlines():
                if line.upper().startswith(prefix):
                    return line.split(":", 1)[1].strip()
            return ""

        insight = _pick("INSIGHT")
        risk = _pick("RISK")
        rec = _pick("RECOMMENDATION")

        if not insight or not risk or not rec:
            return build_narrative(metric, rows, style=style)

        return (insight, risk, rec)

    except Exception:
        return build_narrative(metric, rows, style=style)


def analyze_metric(metric: str, range_: str, style: str = "executive") -> Dict[str, Any]:
    """
    This helper returns the final response shape INCLUDING debug SQL info.
    If your router/service already builds an `out` dict elsewhere,
    you can copy just the out["debug"] block.
    """
    used_table = "kpi_monthly"
    used_sql = build_metric_sql(metric=metric, range_=range_)
    rows = fetch_metric_rows(used_sql)

    insight, risk, rec = build_llm_narrative(metric, rows, style=style)

    out: Dict[str, Any] = {
        "metric": metric,
        "range": range_,
        "style": style,
        "table": used_table,
        "data": rows,
        "narrative": insight,
        "risk": risk,
        "recommendation": rec,
    }

    out["debug"] = {
        "sql": used_sql,
        "row_count": len(rows),
        "table": used_table,
    }

    return out
