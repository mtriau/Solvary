"""M4: challenge attempt = workspace + bound problem + shared judge."""

import uuid

import pytest
from httpx import AsyncClient

from app.services.collaboration.manager import reset_collab_manager

ADMIN = {"email": "admin@codearena.dev", "password": "admin123"}


@pytest.fixture(autouse=True)
def fresh_collab_manager():
    reset_collab_manager()
    yield
    reset_collab_manager()


async def _login(client, email, password) -> dict:
    r = await client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _register(client, name) -> tuple[str, dict]:
    email = f"{name}-{uuid.uuid4().hex[:8]}@test.dev"
    r = await client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": "pw123456"}
    )
    return email, {"Authorization": f"Bearer {r.json()['access_token']}"}


async def _make_attempt_problem(client, admin_h) -> dict:
    """A problem with starter code + one sample test, unique per call."""
    slug = f"m4-{uuid.uuid4().hex[:8]}"
    r = await client.post(
        "/api/v1/problems",
        json={
            "slug": slug,
            "title": "M4 Attempt Problem",
            "difficulty": "easy",
            "statement_md": "Echo the input.",
            "starter_code": {"python": "# starter for m4\n", "javascript": "// starter\n"},
        },
        headers=admin_h,
    )
    assert r.status_code == 201, r.text
    problem = r.json()
    r = await client.post(
        f"/api/v1/problems/{problem['id']}/testcases",
        json={"ordinal": 1, "stdin": "x\n", "expected_stdout": "x\n", "is_sample": True},
        headers=admin_h,
    )
    assert r.status_code == 201, r.text
    return problem


async def test_attempt_workspace_binds_problem_and_seeds_starter(client: AsyncClient):
    admin_h = await _login(client, **ADMIN)
    problem = await _make_attempt_problem(client, admin_h)

    r = await client.post(
        "/api/v1/workspaces",
        json={"problem_id": problem["id"], "language": "python"},
        headers=admin_h,
    )
    assert r.status_code == 201, r.text
    ws = r.json()
    # Name defaults to the problem title; problem info embedded
    assert ws["name"] == "M4 Attempt Problem"
    assert ws["problem_id"] == problem["id"]
    assert ws["problem_slug"] == problem["slug"]
    assert ws["problem_title"] == "M4 Attempt Problem"

    # The doc snapshot was seeded server-side with the starter code
    from pycrdt import Map

    from app.db.engine import async_session_factory
    from app.repositories.sqlalchemy_doc_repository import SQLAlchemyDocRepository
    from app.services.collaboration import doc_store

    async with async_session_factory() as session:
        doc, _seq = await doc_store.load(SQLAlchemyDocRepository(session), ws["id"])
    files_map = doc.get(doc_store.FILES_MAP, type=Map)
    contents = [str(files_map[k]) for k in files_map.keys()]
    assert contents == ["# starter for m4\n"]


async def test_attempt_workspace_unknown_problem_404(client: AsyncClient):
    admin_h = await _login(client, **ADMIN)
    r = await client.post(
        "/api/v1/workspaces",
        json={"problem_id": "prob_nope", "language": "python"},
        headers=admin_h,
    )
    assert r.status_code == 404


async def test_workspace_submission_rbac_and_shared_visibility(client: AsyncClient):
    admin_h = await _login(client, **ADMIN)
    problem = await _make_attempt_problem(client, admin_h)

    _, owner_h = await _register(client, "pilot")
    editor_email, editor_h = await _register(client, "copilot")
    viewer_email, viewer_h = await _register(client, "observer")
    _, outsider_h = await _register(client, "outsider")

    r = await client.post(
        "/api/v1/workspaces",
        json={"problem_id": problem["id"], "language": "python"},
        headers=owner_h,
    )
    ws = r.json()
    for email, role in [(editor_email, "editor"), (viewer_email, "viewer")]:
        r = await client.post(
            f"/api/v1/workspaces/{ws['id']}/members",
            json={"email": email, "role": role},
            headers=owner_h,
        )
        assert r.status_code == 201

    sub_payload = {
        "problem_id": problem["id"],
        "language": "python",
        "code": "print(input())",
        "workspace_id": ws["id"],
    }

    # editor can submit; viewer and outsider cannot
    r = await client.post("/api/v1/submissions", json=sub_payload, headers=editor_h)
    assert r.status_code == 201, r.text
    sub_id = r.json()["id"]
    r = await client.post("/api/v1/submissions", json=sub_payload, headers=viewer_h)
    assert r.status_code == 403
    r = await client.post("/api/v1/submissions", json=sub_payload, headers=outsider_h)
    assert r.status_code == 403

    # problem mismatch is a 400
    other = await _make_attempt_problem(client, admin_h)
    r = await client.post(
        "/api/v1/submissions",
        json={**sub_payload, "problem_id": other["id"]},
        headers=editor_h,
    )
    assert r.status_code == 400

    # every member (even the viewer) can see the editor's submission +
    # its verdict stream; the outsider cannot
    for headers, expected in [(owner_h, 200), (viewer_h, 200), (outsider_h, 403)]:
        r = await client.get(f"/api/v1/submissions/{sub_id}", headers=headers)
        assert r.status_code == expected

    # the shared workspace history lists it for members only
    r = await client.get(
        f"/api/v1/submissions?workspace_id={ws['id']}", headers=viewer_h
    )
    assert r.status_code == 200
    assert any(s["id"] == sub_id for s in r.json()["items"])
    r = await client.get(
        f"/api/v1/submissions?workspace_id={ws['id']}", headers=outsider_h
    )
    assert r.status_code == 403


async def test_plain_workspace_still_works(client: AsyncClient):
    """No problem bound: name required, empty seed, no problem fields."""
    _, headers = await _register(client, "plain")
    r = await client.post(
        "/api/v1/workspaces", json={"language": "python"}, headers=headers
    )
    assert r.status_code == 400  # no name, no problem

    r = await client.post(
        "/api/v1/workspaces", json={"name": "scratch", "language": "python"}, headers=headers
    )
    assert r.status_code == 201
    assert r.json()["problem_slug"] is None
