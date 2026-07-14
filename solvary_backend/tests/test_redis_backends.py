"""Redis backend tests — auto-skip when no Redis is reachable on
localhost:6379 (CI provides one as a service container; locally:
`docker run -d -p 6379:6379 redis:7`).

The cross-instance test is the important one: two CollaborationManager
objects (simulating two backend replicas) sharing only Redis + the DB,
with clients attached to different "instances" seeing each other's edits.
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest

from app.config import get_settings
from app.models.submission import Submission
from app.repositories.doc_repository import MockDocRepository
from app.services.collaboration import doc_store, sync
from app.services.collaboration.backplane import RedisBackplane
from app.services.collaboration.manager import CollaborationManager
from app.services.execution.base import ExecCase, ExecJob
from app.services.queue.broker import RedisEventBroker
from app.services.queue.job_queue import RedisJobQueue, job_from_json, job_to_json
from app.services.queue.quota import RateLimitedException, RedisQuotaTracker
from tests.test_collab_manager import FakeSocket, _connect


def _redis_available() -> bool:
    import socket

    try:
        with socket.create_connection(("localhost", 6379), timeout=1):
            return True
    except OSError:
        return False


pytestmark = [
    pytest.mark.redis,
    pytest.mark.skipif(not _redis_available(), reason="Redis not reachable"),
]


# ── job queue ──────────────────────────────────────────────────────


def test_job_serialization_roundtrip():
    job = ExecJob(
        id="sub_x",
        user_id="user_y",
        language="python",
        code="print(1)",
        mode="judge",
        cases=[ExecCase(ordinal=1, stdin="a\n", expected_stdout="b\n", is_sample=True)],
        time_limit_s=4.0,
        memory_kb=1000,
    )
    restored = job_from_json(job_to_json(job))
    assert restored == job


async def test_redis_queue_roundtrip():
    queue = RedisJobQueue()
    job = ExecJob(
        id=f"sub_{uuid.uuid4().hex[:8]}",
        user_id="user_q",
        language="python",
        code="x",
        mode="run",
        stdin="in",
        time_limit_s=1.0,
        memory_kb=1,
    )
    await queue.enqueue(job)
    out = await asyncio.wait_for(queue.dequeue(), timeout=5)
    assert out == job


# ── event broker (streams) ─────────────────────────────────────────


async def test_redis_broker_replay_then_follow():
    broker = RedisEventBroker()
    job_id = f"sub_{uuid.uuid4().hex[:8]}"

    # Events published BEFORE subscribing are replayed
    await broker.publish(job_id, {"kind": "queued"})
    await broker.publish(job_id, {"kind": "case_result", "ordinal": 1})

    async def collect():
        return [e async for e in broker.subscribe(job_id)]

    task = asyncio.create_task(collect())
    await asyncio.sleep(0.3)  # subscriber is mid-follow now
    await broker.publish(job_id, {"kind": "verdict", "verdict": "accepted"})
    events = await asyncio.wait_for(task, timeout=5)

    assert [e["kind"] for e in events] == ["queued", "case_result", "verdict"]
    assert await broker.is_done(job_id)
    assert await broker.known(job_id)


# ── quota: reserve on one instance, release on another ────────────


async def test_redis_quota_cross_instance():
    user = f"user_{uuid.uuid4().hex[:8]}"
    instance_a = RedisQuotaTracker(rate_per_min=100, max_concurrent=2)
    instance_b = RedisQuotaTracker(rate_per_min=100, max_concurrent=2)

    await instance_a.check_and_reserve(user)
    await instance_a.check_and_reserve(user)
    with pytest.raises(RateLimitedException):
        await instance_a.check_and_reserve(user)

    # The worker on ANOTHER instance releases — the user is unblocked
    await instance_b.release(user)
    await instance_b.check_and_reserve(user)
    await instance_b.release(user)
    await instance_b.release(user)


# ── collab across two "instances" ──────────────────────────────────


async def test_collab_relays_across_instances():
    settings = get_settings()
    shared_repo = MockDocRepository()  # stands in for the shared DB

    @asynccontextmanager
    async def provider():
        yield shared_repo

    bp_a, bp_b = RedisBackplane(), RedisBackplane()
    manager_a = CollaborationManager(provider, settings, bp_a)
    manager_b = CollaborationManager(provider, settings, bp_b)

    ws_id = f"ws_{uuid.uuid4().hex[:8]}"
    await doc_store.birth(shared_repo, ws_id, {"wsf_1": "shared\n"})

    sock_a, sock_b = FakeSocket(), FakeSocket()
    task_a = await _connect(manager_a, ws_id, sock_a, "user_a", "owner")
    task_b = await _connect(manager_b, ws_id, sock_b, "user_b", "editor")
    await asyncio.sleep(0.3)  # let subscriptions settle

    # Client on instance A edits; client on instance B receives it
    from pycrdt import Doc, Map

    doc = Doc()
    doc.get("files", type=Map)
    doc.apply_update((await shared_repo.latest_snapshot(ws_id)).state)
    text = doc.get("files", type=Map)["wsf_1"]
    before = doc.get_state()
    text.insert(len(str(text)), "from A\n")
    sock_a.push(sync.encode_sync_update(doc.get_update(before)))

    for _ in range(30):
        await asyncio.sleep(0.1)
        if any(
            sub == sync.SYNC_UPDATE for sub, _ in sock_b.frames(sync.MESSAGE_SYNC)
        ):
            break
    else:
        raise AssertionError("update never crossed instances")

    # files_changed on A reaches B's sockets too
    await manager_a.notify_files_changed(ws_id)
    for _ in range(30):
        await asyncio.sleep(0.1)
        if sock_b.frames(sync.MESSAGE_FILES_CHANGED):
            break
    else:
        raise AssertionError("files_changed never crossed instances")

    for sock, task in [(sock_a, task_a), (sock_b, task_b)]:
        sock.close()
        with pytest.raises(ConnectionError):
            await task
    await bp_a.stop()
    await bp_b.stop()


# ── reaper (backend-agnostic, tested here for the runtime path) ───


async def test_reaper_marks_stale_submissions(judge_runtime):
    from app.db.engine import async_session_factory
    from app.repositories.sqlalchemy_submission_repository import (
        SQLAlchemySubmissionRepository,
    )

    stale_id = f"sub_{uuid.uuid4().hex[:8]}"
    async with async_session_factory() as session:
        repo = SQLAlchemySubmissionRepository(session)
        await repo.create(
            Submission(
                id=stale_id,
                user_id="user_reap",
                problem_id="prob_reap",
                language="python",
                code="x",
                verdict="running",
                created_at=datetime.now(UTC) - timedelta(minutes=30),
                updated_at=datetime.now(UTC) - timedelta(minutes=30),
            )
        )
        await session.commit()

    reaped = await judge_runtime.reap_stale_jobs()
    assert reaped >= 1

    async with async_session_factory() as session:
        repo = SQLAlchemySubmissionRepository(session)
        submission = await repo.get_by_id(stale_id)
        assert submission.verdict == "internal_error"
