from __future__ import annotations

import hmac
import os

from fastapi import Header, HTTPException, status


def verify_api_key(authorization: str | None = Header(default=None)) -> None:
    environment = os.getenv("SP_ENV", "development").strip().casefold()
    expected = os.getenv("SP_API_KEY", "").strip()
    if not expected:
        if environment in {"production", "prod"}:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SP_API_KEY must be configured in production.",
            )
        return

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    scheme, separator, supplied = authorization.partition(" ")
    if not separator or scheme.casefold() != "bearer" or not supplied:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token.",
        )

    if not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        )
