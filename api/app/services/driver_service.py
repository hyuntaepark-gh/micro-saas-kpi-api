from typing import Any, Dict, List, Optional, Tuple


def _to_dict(x: Any) -> Dict[str, Any]:
    """
    Normalize Pydantic model / dict into plain dict.
    Supports Pydantic v1 (.dict) and v2 (.model_dump).
    """
    if x is None:
        return {}
    if isinstance(x, dict):
        return x
    # Pydantic v2
    if hasattr(x, "model_dump"):
        try:
            return x.model_dump()
        except Exception:
            pass
    # Pydantic v1
    if hasattr(x, "dict"):
        try:
            return x.dict()
        except Exception:
            pass
    # fallback
    return {}


def _pct_change(prev: Optional[float], curr: Optional[float]) -> Optional[float]:
    if prev is None or curr is None:
        return None
    try:
        prev_f = float(prev)
        curr_f = float(curr)
        if prev_f == 0:
            return None
        return (curr_f - prev_f) / prev_f * 100.0
    except Exception:
        return None


def _extract_latest_two_months(outputs: List[Any]) -> Tuple[Optional[str], Optional[str], Dict[str, Optional[float]], Dict[str, Optional[float]]]:
    """
    Extract latest & previous month KPI values from multi-metric legacy outputs.
    Returns:
      latest_month, previous_month, latest_vals, prev_vals
    """
    latest_month = None
    previous_month = None

    # We expect each legacy output to have:
    # res["result"]["data"] = [{"month": "...", "revenue":..., "orders":..., "customers":..., "aov":...}, ...]
    # and is ordered by month desc with LIMIT 3.
    # We'll take month0 as latest, month1 as previous.
    latest_vals = {"revenue": None, "orders": None, "customers": None, "aov": None}
    prev_vals = {"revenue": None, "orders": None, "customers": None, "aov": None}

    # Find any output that includes a "data" list with month values
    for item in outputs:
        d = _to_dict(item)
        # legacy AskResponse shape: {"question":..., "parsed":..., "result":{...}}
        result = _to_dict(d.get("result"))
        rows = result.get("data") or []
        if not isinstance(rows, list) or len(rows) < 2:
            continue

        row0 = _to_dict(rows[0])
        row1 = _to_dict(rows[1])

        # capture months once
        if latest_month is None:
            latest_month = row0.get("month")
        if previous_month is None:
            previous_month = row1.get("month")

        # fill any known metrics if present
        for k in ["revenue", "orders", "customers", "aov"]:
            if latest_vals[k] is None and row0.get(k) is not None:
                latest_vals[k] = row0.get(k)
            if prev_vals[k] is None and row1.get(k) is not None:
                prev_vals[k] = row1.get(k)

    return latest_month, previous_month, latest_vals, prev_vals


def build_driver_summary(outputs: List[Any]) -> Dict[str, Any]:
    """
    Build rule-based driver decomposition summary from multi-metric fallback outputs.
    Adds:
      - changes_pct
      - main_driver (orders or aov)
      - executive_takeaway
      - executive_summary (one-liner)
    """
    latest_month, previous_month, latest_vals, prev_vals = _extract_latest_two_months(outputs)

    rev_pct = _pct_change(prev_vals["revenue"], latest_vals["revenue"])
    ord_pct = _pct_change(prev_vals["orders"], latest_vals["orders"])
    aov_pct = _pct_change(prev_vals["aov"], latest_vals["aov"])
    cus_pct = _pct_change(prev_vals["customers"], latest_vals["customers"])

    # Need at least rev + (orders or aov) to compute a meaningful driver
    if rev_pct is None or (ord_pct is None and aov_pct is None):
        return {
            "status": "insufficient_data",
            "message": "Need at least 2 months of KPI data for revenue/orders/aov to compute drivers.",
            "latest_month": latest_month,
            "previous_month": previous_month,
            "changes_pct": {
                "revenue": rev_pct,
                "orders": ord_pct,
                "aov": aov_pct,
                "customers": cus_pct,
            },
        }

    # Decide main driver by absolute magnitude among orders vs aov
    main_driver = None
    if ord_pct is not None and aov_pct is not None:
        main_driver = "orders" if abs(ord_pct) >= abs(aov_pct) else "aov"
    elif ord_pct is not None:
        main_driver = "orders"
    else:
        main_driver = "aov"

    executive_takeaway = (
        "Revenue change is mainly driven by Orders."
        if main_driver == "orders"
        else "Revenue change is mainly driven by AOV."
    )

    # Step 2: executive_summary one-liner
    driver_label = "orders" if main_driver == "orders" else "AOV"
    executive_summary = (
        f"Revenue changed {rev_pct:.1f}% MoM, driven primarily by {driver_label} "
        f"({(ord_pct if ord_pct is not None else 0.0):.1f}% / {(aov_pct if aov_pct is not None else 0.0):.1f}%)."
        if (rev_pct is not None and ord_pct is not None and aov_pct is not None and main_driver)
        else "Executive summary unavailable due to insufficient data."
    )

    return {
        "status": "ok",
        "latest_month": latest_month,
        "previous_month": previous_month,
        "changes_pct": {
            "revenue": rev_pct,
            "orders": ord_pct,
            "aov": aov_pct,
            "customers": cus_pct,
        },
        "main_driver": main_driver,
        "executive_takeaway": executive_takeaway,
        "executive_summary": executive_summary,
    }
from typing import Any, Dict, List, Optional

def _pct_change(prev: Optional[float], curr: Optional[float]) -> Optional[float]:
    if prev is None or curr is None:
        return None
    try:
        prev_f = float(prev)
        curr_f = float(curr)
        if prev_f == 0:
            return None
        return (curr_f - prev_f) / prev_f * 100.0
    except Exception:
        return None


def build_driver_summary_from_rows(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Driver decomposition using the last two months from rows (oldest -> newest).
    Requires at least 2 rows and at least revenue + (orders or aov).
    """
    if not rows or len(rows) < 2:
        return {
            "status": "insufficient_data",
            "message": "Need at least 2 months of KPI rows to compute drivers.",
            "latest_month": None,
            "previous_month": None,
            "changes_pct": {"revenue": None, "orders": None, "aov": None, "customers": None},
        }

    prev = rows[-2]
    curr = rows[-1]

    latest_month = curr.get("month")
    previous_month = prev.get("month")

    rev_pct = _pct_change(prev.get("revenue"), curr.get("revenue"))
    ord_pct = _pct_change(prev.get("orders"), curr.get("orders"))
    aov_pct = _pct_change(prev.get("aov"), curr.get("aov"))
    cus_pct = _pct_change(prev.get("customers"), curr.get("customers"))

    if rev_pct is None or (ord_pct is None and aov_pct is None):
        return {
            "status": "insufficient_data",
            "message": "Need at least 2 months of KPI data for revenue/orders/aov to compute drivers.",
            "latest_month": latest_month,
            "previous_month": previous_month,
            "changes_pct": {"revenue": rev_pct, "orders": ord_pct, "aov": aov_pct, "customers": cus_pct},
        }

    # main driver = bigger absolute mover between orders vs aov
    if ord_pct is not None and aov_pct is not None:
        main_driver = "orders" if abs(ord_pct) >= abs(aov_pct) else "aov"
    elif ord_pct is not None:
        main_driver = "orders"
    else:
        main_driver = "aov"

    executive_takeaway = (
        "Revenue change is mainly driven by Orders."
        if main_driver == "orders"
        else "Revenue change is mainly driven by AOV."
    )

    # One-liner summary
    executive_summary = (
        f"Revenue changed {rev_pct:.1f}% MoM, driven primarily by "
        f"{'orders' if main_driver == 'orders' else 'AOV'} "
        f"({(ord_pct if ord_pct is not None else 0.0):.1f}% / {(aov_pct if aov_pct is not None else 0.0):.1f}%)."
    )

    return {
        "status": "ok",
        "latest_month": latest_month,
        "previous_month": previous_month,
        "changes_pct": {"revenue": rev_pct, "orders": ord_pct, "aov": aov_pct, "customers": cus_pct},
        "main_driver": main_driver,
        "executive_takeaway": executive_takeaway,
        "executive_summary": executive_summary,
    }
