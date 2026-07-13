"""Workspace REST tests: CRUD + table-driven RBAC (design §9)."""

import uuid

import pytest
from httpx import AsyncClient

from app.services.collaboration.manager import reset_collab_manager


@pytest.fixture(autouse=True)
def fresh_collab_manager():
    reset_collab_manager()
    yield
    reset_collab_manager()


async def _register(client: AsyncClient, name: str) -> tuple[str, dict]:
    email = f"{name}-{uuid.uuid4().hex[:8]}@test.dev"
    r = await client.post(
        "/api/auth/register",
        json={"name": name, "email": email, "password": "pw123456"},
    )
    assert r.status_code == 201, r.text
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _make_workspace(client, headers, name="Test WS") -> dict:
    r = await client.post(
        "/api/v1/workspaces", json={"name": name, "language": "python"}, headers=headers
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _add_member(client, owner_headers, ws_id, email, role) -> dict:
    r = await client.post(
        f"/api/v1/workspaces/{ws_id}/members",
        json={"email": email, "role": role},
        headers=owner_headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


async def test_create_workspace_seeds_default_file_and_owner(client: AsyncClient):
    _, headers = await _register(client, "owner")
    ws = await _make_workspace(client, headers)
    assert ws["my_role"] == "owner"

    r = await client.get(f"/api/v1/workspaces/{ws['id']}/files", headers=headers)
    files = r.json()
    assert [f["path"] for f in files] == ["main.py"]

    r = await client.get(f"/api/v1/workspaces/{ws['id']}/members", headers=headers)
    assert [m["role"] for m in r.json()] == ["owner"]


async def test_list_mine_only(client: AsyncClient):
    _, h1 = await _register(client, "u1")
    _, h2 = await _register(client, "u2")
    ws = await _make_workspace(client, h1, "mine")

    r = await client.get("/api/v1/workspaces", headers=h2)
    assert all(w["id"] != ws["id"] for w in r.json())


async def test_rbac_matrix(client: AsyncClient):
    """Table-driven: role × action → expected status."""
    _, owner_h = await _register(client, "owner")
    editor_email, editor_h = await _register(client, "editor")
    viewer_email, viewer_h = await _register(client, "viewer")
    _, outsider_h = await _register(client, "outsider")

    ws = await _make_workspace(client, owner_h)
    ws_id = ws["id"]
    await _add_member(client, owner_h, ws_id, editor_email, "editor")
    await _add_member(client, owner_h, ws_id, viewer_email, "viewer")

    async def get_ws(h):
        return await client.get(f"/api/v1/workspaces/{ws_id}", headers=h)

    async def create_file(h):
        return await client.post(
            f"/api/v1/workspaces/{ws_id}/files",
            json={"path": f"f-{uuid.uuid4().hex[:6]}.py"},
            headers=h,
        )

    async def rename_ws(h):
        return await client.patch(
            f"/api/v1/workspaces/{ws_id}", json={"name": "renamed"}, headers=h
        )

    async def add_mem(h):
        return await client.post(
            f"/api/v1/workspaces/{ws_id}/members",
            json={"email": f"x-{uuid.uuid4().hex[:6]}@test.dev", "role": "viewer"},
            headers=h,
        )

    async def delete_ws(h):
        return await client.delete(f"/api/v1/workspaces/{ws_id}", headers=h)

    cases = [
        (get_ws, owner_h, 200), (get_ws, editor_h, 200),
        (get_ws, viewer_h, 200), (get_ws, outsider_h, 403),
        (create_file, editor_h, 201), (create_file, viewer_h, 403),
        (create_file, outsider_h, 403),
        (rename_ws, editor_h, 200), (rename_ws, viewer_h, 403),
        (add_mem, editor_h, 403), (add_mem, viewer_h, 403),
        # 404 because the target email doesn't exist — but RBAC passed
        (add_mem, owner_h, 404),
        (delete_ws, editor_h, 403), (delete_ws, viewer_h, 403),
        (delete_ws, owner_h, 204),
    ]
    for action, headers, expected in cases:
        r = await action(headers)
        assert r.status_code == expected, (
            f"{action.__name__} expected {expected}, got {r.status_code}: {r.text}"
        )


async def test_rename_is_metadata_only_and_delete_guards_last_file(client: AsyncClient):
    _, headers = await _register(client, "owner")
    ws = await _make_workspace(client, headers)
    ws_id = ws["id"]

    r = await client.get(f"/api/v1/workspaces/{ws_id}/files", headers=headers)
    file_id = r.json()[0]["id"]

    # Rename: same id, new path
    r = await client.patch(
        f"/api/v1/workspaces/{ws_id}/files/{file_id}",
        json={"path": "solution.py"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["id"] == file_id
    assert r.json()["path"] == "solution.py"

    # Deleting the only file is refused
    r = await client.delete(
        f"/api/v1/workspaces/{ws_id}/files/{file_id}", headers=headers
    )
    assert r.status_code == 400

    # Duplicate path on create is refused
    r = await client.post(
        f"/api/v1/workspaces/{ws_id}/files",
        json={"path": "solution.py"},
        headers=headers,
    )
    assert r.status_code == 409
