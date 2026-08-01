from __future__ import annotations

import hmac
import json
import os
import urllib.request

from fastapi import Header, HTTPException, status


def _get_oidc_config() -> dict | None:
    """Return OIDC configuration if the environment is set, or None."""
    issuer = os.getenv("SP_OIDC_ISSUER", "").strip()
    if not issuer:
        return None
    return {
        "issuer": issuer.rstrip("/"),
        "client_id": os.getenv("SP_OIDC_CLIENT_ID", "").strip(),
        "audience": os.getenv("SP_OIDC_AUDIENCE", "").strip(),
    }


def _fetch_oidc_jwks(issuer: str) -> dict:
    """Fetch JWKS keys from the OIDC issuer's .well-known endpoint."""
    config_url = f"{issuer}/.well-known/openid-configuration"
    with urllib.request.urlopen(config_url, timeout=10) as resp:
        config = json.loads(resp.read())
    jwks_url = config["jwks_uri"]
    with urllib.request.urlopen(jwks_url, timeout=10) as resp:
        return json.loads(resp.read())


def _verify_oidc_token(token: str, config: dict) -> dict | None:
    """Verify a JWT against the OIDC issuer and return claims, or None if invalid."""
    try:
        from jose import jwt

        jwks = _fetch_oidc_jwks(config["issuer"])
        return jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=config["audience"] or None,
            issuer=config["issuer"],
            options={"verify_exp": True, "verify_aud": bool(config["audience"])},
        )
    except Exception:
        return None


def verify_api_key(authorization: str | None = Header(default=None)) -> None:
    environment = os.getenv("SP_ENV", "development").strip().casefold()
    expected = os.getenv("SP_API_KEY", "").strip()
    oidc_config = _get_oidc_config()

    # ── No auth configured ──
    if not expected and not oidc_config:
        if environment in {"production", "prod"}:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SP_API_KEY or SP_OIDC_ISSUER must be configured in production.",
            )
        return

    # ── Missing header ──
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

    # ── OIDC path: try JWT verification first ──
    if oidc_config:
        claims = _verify_oidc_token(supplied, oidc_config)
        if claims is not None:
            return  # OIDC verification succeeded

    # ── API Key fallback ──
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token (OIDC verification failed and no API key configured).",
        )

    if not hmac.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token.",
        )
