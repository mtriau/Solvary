"""Auth hardening tests: refresh rotation/revocation, rate limiting,
Google OIDC login (verifier faked at the service seam), passwordless guard."""

import uuid

import pytest
from httpx import AsyncClient

REFRESH_COOKIE = "solvary_refresh"


async def _register(client: AsyncClient, name: str = "Auth Tester") -> tuple[str, dict]:
    email = f"auth-{uuid.uuid4().hex[:8]}@test.dev"
    r = await client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": "pw123456"},
    )
    assert r.status_code == 201, r.text
    return email, r.json()


# ── refresh-token lifecycle ────────────────────────────────────────


async def test_login_sets_httponly_refresh_cookie(client: AsyncClient):
    email, _ = await _register(client)
    r = await client.post(
        "/api/auth/login", json={"email": email, "password": "pw123456"}
    )
    assert r.status_code == 200
    set_cookie = r.headers.get("set-cookie", "")
    assert REFRESH_COOKIE in set_cookie
    assert "HttpOnly" in set_cookie
    assert "Path=/api/auth" in set_cookie


async def test_refresh_rotates_and_revokes_old_token(client: AsyncClient):
    await _register(client)
    old_refresh = client.cookies.get(REFRESH_COOKIE, path="/api/auth")
    assert old_refresh

    # Refresh: new access token works, cookie rotated
    r = await client.post("/api/auth/refresh")
    assert r.status_code == 200, r.text
    new_access = r.json()["access_token"]
    new_refresh = client.cookies.get(REFRESH_COOKIE, path="/api/auth")
    assert new_refresh and new_refresh != old_refresh

    me = await client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert me.status_code == 200

    # Replay the OLD (rotated-out) token → rejected
    client.cookies.delete(REFRESH_COOKIE, path="/api/auth")
    client.cookies.set(REFRESH_COOKIE, old_refresh, domain="test", path="/api/auth")
    r = await client.post("/api/auth/refresh")
    assert r.status_code == 401


async def test_logout_revokes_refresh_token(client: AsyncClient):
    await _register(client)
    refresh_before = client.cookies.get(REFRESH_COOKIE, path="/api/auth")

    r = await client.post("/api/auth/logout")
    assert r.status_code == 204

    client.cookies.set(
        REFRESH_COOKIE, refresh_before, domain="test", path="/api/auth"
    )
    r = await client.post("/api/auth/refresh")
    assert r.status_code == 401


async def test_refresh_without_cookie_401(client: AsyncClient):
    client.cookies.clear()
    r = await client.post("/api/auth/refresh")
    assert r.status_code == 401


# ── rate limiting ──────────────────────────────────────────────────


async def test_login_rate_limited_per_email(client: AsyncClient):
    email = f"bruteforce-{uuid.uuid4().hex[:6]}@test.dev"
    for i in range(10):
        r = await client.post(
            "/api/auth/login", json={"email": email, "password": "wrong"}
        )
        assert r.status_code == 401, f"attempt {i}: {r.status_code}"
    r = await client.post(
        "/api/auth/login", json={"email": email, "password": "wrong"}
    )
    assert r.status_code == 429


# ── Google OIDC ────────────────────────────────────────────────────


def _fake_verifier(claims: dict):
    async def verify(credential: str, client_id: str) -> dict:
        assert client_id == "test-google-client-id"
        return claims

    return verify


async def test_google_login_creates_passwordless_user(client: AsyncClient, monkeypatch):
    email = f"g-{uuid.uuid4().hex[:8]}@gauth.test.dev"
    sub = f"sub-{uuid.uuid4().hex}"
    monkeypatch.setattr(
        "app.services.auth_service.verify_google_id_token",
        _fake_verifier(
            {"sub": sub, "email": email, "email_verified": True, "name": "G User"}
        ),
    )

    r = await client.post("/api/auth/google", json={"credential": "fake"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user"]["email"] == email
    assert REFRESH_COOKIE in r.headers.get("set-cookie", "")

    # Password login for a Google-only account is cleanly rejected
    r = await client.post(
        "/api/auth/login", json={"email": email, "password": "anything"}
    )
    assert r.status_code == 401
    assert "Google" in r.json()["detail"]

    # Second Google login: same user, no duplicate
    r = await client.post("/api/auth/google", json={"credential": "fake"})
    assert r.status_code == 200
    assert r.json()["user"]["id"] == body["user"]["id"]


async def test_google_login_links_existing_local_account(client: AsyncClient, monkeypatch):
    email, registered = await _register(client, "Linkable")
    monkeypatch.setattr(
        "app.services.auth_service.verify_google_id_token",
        _fake_verifier(
            {"sub": f"sub-{uuid.uuid4().hex}", "email": email, "email_verified": True}
        ),
    )

    r = await client.post("/api/auth/google", json={"credential": "fake"})
    assert r.status_code == 200
    assert r.json()["user"]["id"] == registered["user"]["id"]

    # Local password still works after linking
    r = await client.post(
        "/api/auth/login", json={"email": email, "password": "pw123456"}
    )
    assert r.status_code == 200


async def test_google_verifier_rejections(client: AsyncClient, monkeypatch):
    """The real verifier rejects unverified emails — simulate its raise."""
    from app.core.exceptions import UnauthorizedException

    async def rejecting(credential: str, client_id: str) -> dict:
        raise UnauthorizedException("Google account email is not verified")

    monkeypatch.setattr(
        "app.services.auth_service.verify_google_id_token", rejecting
    )
    r = await client.post("/api/auth/google", json={"credential": "fake"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_google_disabled_without_client_id(client: AsyncClient, monkeypatch):
    from app.config import get_settings

    settings = get_settings()
    monkeypatch.setattr(settings, "google_client_id", "")
    r = await client.post("/api/auth/google", json={"credential": "fake"})
    assert r.status_code == 401
