import os
from fastapi import Header, HTTPException

from api.app.utils.error_response import error_response


def require_api_key(x_api_key: str | None = Header(default=None)):
    """
    Simple API key auth:
    - Reads expected key from env: API_KEY
    - Client must send header: X-API-Key: <key>
    """
    expected = os.getenv("API_KEY")

    # If API_KEY is not set, auth is disabled (dev-friendly)
    if not expected:
        return True

    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=401,
            detail=error_response(
                code="UNAUTHORIZED",
                message="Invalid or missing X-API-Key",
                details={"hint": "Send header: X-API-Key: <API_KEY>"},
            ),
        )

    return True
