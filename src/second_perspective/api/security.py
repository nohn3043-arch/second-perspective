from __future__ import annotations

import hmac
import json
import os
import urllib.parse
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


def _safe_url(url: str, *, require_https: bool = True) -> urllib.parse.SplitResult:
    """Validate a URL before any outbound request.

    Mitigates SSRF: only http(s) schemes, no credentials/hostnames that point
    at internal/loopback/link-local ranges, and no embedded userinfo.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise ValueError(f"Unsupported URL scheme: {parts.scheme!r}")
    if require_https and parts.scheme != "https":
        raise ValueError("Only HTTPS endpoints are allowed for OIDC discovery.")
    if parts.username or parts.password:
        raise ValueError("URLs with embedded credentials are not allowed.")
    host = (parts.hostname or "").lower()
    if not host:
        raise ValueError("Missing host in URL.")
    if host in ("localhost", "0.0.0.0") or host.endswith(".local") or host.endswith(".internal"):
        raise ValueError(f"Refusing to fetch from internal host: {host!r}")
    # Block IP literals in reserved/loopback/link-local/private ranges.
    import ipaddress

    try:
        addr = ipaddress.ip_address(host)
        if not addr.is_global:
            raise ValueError(f"Refusing to fetch from non-public IP: {host!r}")
    except ValueError:
        # Not an IP literal (a DNS name) — acceptable; resolution happens at request time.
        pass
    return parts


def _fetch_json(url: str) -> dict:
    """Fetch a JSON document over HTTPS with SSRF guards and no redirects."""
    _safe_url(url, require_https=True)
    # allow_redirects=False: prevent an attacker-controlled issuer from
    # redirecting the request to an arbitrary/internal endpoint.
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10, cadefault=False) as resp:
        if resp.geturl() != url:
            raise ValueError("Redirects are not permitted for OIDC fetches.")
        return json.loads(resp.read())


def _fetch_oidc_jwks(issuer: str) -> dict:
    """Fetch JWKS keys from the OIDC issuer's .well-known endpoint.

    The jwks_uri is taken from the issuer's discovery document but is strictly
    constrained to the same host (and HTTPS) as the issuer to prevent an
    attacker-influenced discovery response from steering requests elsewhere.
    """
    config_url = f"{issuer}/.well-known/openid-configuration"
    config = _fetch_json(config_url)
    jwks_url = config["jwks_uri"]
    jwks_parts = _safe_url(jwks_url, require_https=True)
    issuer_host = urllib.parse.urlsplit(issuer).hostname or ""
    if jwks_parts.hostname.lower() != issuer_host.lower():
        raise ValueError(
            "jwks_uri host does not match the OIDC issuer host (possible SSRF)."
        )
    return _fetch_json(jwks_url)


def assert_auth_configured() -> None:
    """Fail fast at startup when production has no authentication configured.

    Previously production silently returned HTTP 503 on every request, which
    meant a misconfiguration left the service unusable rather than refusing to
    boot. We now hard-fail the process so the gap is caught during deployment.
    """
    environment = os.getenv("SP_ENV", "development").strip().casefold()
    if environment not in {"production", "prod"}:
        return
    expected = os.getenv("SP_API_KEY", "").strip()
    oidc_config = _get_oidc_config()
    if not expected and not oidc_config:
        raise RuntimeError(
            "Production requires SP_API_KEY or SP_OIDC_ISSUER to be set. "
            "Refusing to start without authentication."
        )


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
