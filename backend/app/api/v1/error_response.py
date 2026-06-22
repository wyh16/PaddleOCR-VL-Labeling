from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse

from app.utils.ids import new_public_id


def build_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or {},
            },
            "request_id": new_public_id("req"),
        },
    )
