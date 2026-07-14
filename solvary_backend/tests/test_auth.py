import uuid

import pytest
from httpx import AsyncClient


def _unique_email() -> str:
    return f"test_{uuid.uuid4().hex[:8]}@solvary.dev"


@pytest.mark.asyncio
async def test_register_login_me_roundtrip(client: AsyncClient):
    email = _unique_email()

    # Register
    resp = await client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "password123"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user"]["email"] == email
    assert body["user"]["role"] == "user"

    # Login
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    # Authenticated /users/me
    resp = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["email"] == email


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    email = _unique_email()
    await client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": "password123"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrong-password"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient):
    resp = await client.get("/api/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email_conflicts(client: AsyncClient):
    email = _unique_email()
    payload = {"name": "Test User", "email": email, "password": "password123"}
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    resp = await client.post("/api/auth/register", json=payload)
    assert resp.status_code == 409
