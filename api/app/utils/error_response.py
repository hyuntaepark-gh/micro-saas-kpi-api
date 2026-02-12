from typing import Any, Optional, Dict


def error_response(code: str, message: str, details: Optional[Any] = None) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"error": {"code": code, "message": message}}
    if details is not None:
        payload["error"]["details"] = details
    return payload
