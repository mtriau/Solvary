"""
Google OIDC ID-token verification — no extra dependencies: `python-jose`
(already used for our own JWTs) verifies RS256 against Google's published
JWKS, fetched via httpx and cached.

The frontend uses Google Identity Services ("Sign in with Google" button),
which yields an ID token (the `credential`); we verify signature, issuer,
audience, expiry, and require a verified email.
"""

import time

import httpx
from jose import JWTError, jwt

from app.core.exceptions import UnauthorizedException

GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUERS = ("https://accounts.google.com", "accounts.google.com")
_JWKS_TTL_S = 3600

_jwks_cache: dict | None = None
_jwks_fetched_at: float = 0.0


async def _get_jwks() -> dict:
    global _jwks_cache, _jwks_fetched_at
    if _jwks_cache is None or time.monotonic() - _jwks_fetched_at > _JWKS_TTL_S:
        async with httpx.AsyncClient() as client:
            response = await client.get(GOOGLE_JWKS_URL, timeout=10.0)
            response.raise_for_status()
            _jwks_cache = response.json()
            _jwks_fetched_at = time.monotonic()
    return _jwks_cache


def _reset_jwks_cache() -> None:
    """Test hook."""
    global _jwks_cache, _jwks_fetched_at
    _jwks_cache = None
    _jwks_fetched_at = 0.0


async def verify_google_id_token(credential: str, client_id: str) -> dict:
    """Validate a Google ID token; returns its claims.

    Raises UnauthorizedException on any failure — including unverified
    email addresses, which must never auto-link to an existing account.
    """
    jwks = await _get_jwks()
    try:
        header = jwt.get_unverified_header(credential)
        key = next(
            (k for k in jwks.get("keys", []) if k.get("kid") == header.get("kid")),
            None,
        )
        if key is None:
            raise UnauthorizedException("Unknown Google signing key")
        claims = jwt.decode(
            credential,
            key,
            algorithms=["RS256"],
            audience=client_id,
        )
    except JWTError as e:
        raise UnauthorizedException(f"Invalid Google credential: {e}") from e

    if claims.get("iss") not in GOOGLE_ISSUERS:
        raise UnauthorizedException("Invalid Google token issuer")
    if not claims.get("sub") or not claims.get("email"):
        raise UnauthorizedException("Google token missing subject or email")
    if not claims.get("email_verified"):
        raise UnauthorizedException("Google account email is not verified")
    return claims
