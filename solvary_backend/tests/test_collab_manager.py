"""CollaborationManager tests with fake sockets + real pycrdt client docs —
relay, viewer enforcement, awareness, persistence (design §9)."""

import asyncio
from contextlib import asynccontextmanager

import pytest
from pycrdt import Doc, Map, Text

from app.config import get_settings
from app.repositories.doc_repository import MockDocRepository
from app.services.collaboration import doc_store, sync
from app.services.collaboration.backplane import InMemoryBackplane
from app.services.collaboration.manager import CollaborationManager


class FakeSocket:
    def __init__(self) -> None:
        self.inbox: asyncio.Queue = asyncio.Queue()
        self.sent: list[bytes] = []

    async def receive_bytes(self) -> bytes:
        frame = await self.inbox.get()
        if frame is None:
            raise ConnectionError("closed")
        return frame

    async def send_bytes(self, data: bytes) -> None:
        self.sent.append(data)

    def push(self, frame: bytes) -> None:
        self.inbox.put_nowait(frame)

    def close(self) -> None:
        self.inbox.put_nowait(None)

    def frames(self, msg_type: int) -> list[tuple[int | None, bytes]]:
        out = []
        for f in self.sent:
            t, sub, payload = sync.parse_message(f)
            if t == msg_type:
                out.append((sub, payload))
        return out


@pytest.fixture
def repo() -> MockDocRepository:
    return MockDocRepository()


@pytest.fixture
def manager(repo) -> CollaborationManager:
    @asynccontextmanager
    async def provider():
        yield repo

    return CollaborationManager(provider, get_settings(), InMemoryBackplane())


async def _connect(manager, ws_id, socket, user_id, role):
    task = asyncio.create_task(
        manager.handle_connection(socket, ws_id, user_id, f"user {user_id}", role)
    )
    await asyncio.sleep(0.02)  # let the handshake run
    return task


def _client_doc_from_step(socket: FakeSocket) -> Doc:
    """Build a client doc from the server's sync frames sent so far."""
    doc = Doc()
    doc.get(doc_store.FILES_MAP, type=Map)
    for sub, payload in socket.frames(sync.MESSAGE_SYNC):
        if sub in (sync.SYNC_STEP2, sync.SYNC_UPDATE):
            doc.apply_update(payload)
    return doc


async def test_join_sync_and_relay(manager, repo):
    await doc_store.birth(repo, "ws_1", {"wsf_a": "hello\n"})

    sock_a, sock_b = FakeSocket(), FakeSocket()
    task_a = await _connect(manager, "ws_1", sock_a, "user_a", "owner")
    task_b = await _connect(manager, "ws_1", sock_b, "user_b", "editor")

    # Handshake: server sends step1 with its state vector
    assert sock_a.frames(sync.MESSAGE_SYNC)[0][0] == sync.SYNC_STEP1

    # A requests state (client-side step1) → server answers step2 with content
    sock_a.push(sync.encode_sync_step1(Doc().get_state()))
    await asyncio.sleep(0.02)
    doc_a = _client_doc_from_step(sock_a)
    files_a = doc_a.get(doc_store.FILES_MAP, type=Map)
    assert str(files_a["wsf_a"]) == "hello\n"

    # A edits locally and sends the update → B receives it, server persists it
    files_a["wsf_a"].insert(6, "world\n")
    update = doc_a.get_update(Doc().get_state())
    sock_a.push(sync.encode_sync_update(update))
    await asyncio.sleep(0.02)

    relayed = sock_b.frames(sync.MESSAGE_SYNC)
    assert any(sub == sync.SYNC_UPDATE for sub, _ in relayed)
    assert await repo.max_seq("ws_1") == 1

    # Server doc reflects the edit (fresh join sees merged content)
    sock_c = FakeSocket()
    task_c = await _connect(manager, "ws_1", sock_c, "user_c", "viewer")
    sock_c.push(sync.encode_sync_step1(Doc().get_state()))
    await asyncio.sleep(0.02)
    doc_c = _client_doc_from_step(sock_c)
    assert str(doc_c.get(doc_store.FILES_MAP, type=Map)["wsf_a"]) == "hello\nworld\n"

    for sock, task in [(sock_a, task_a), (sock_b, task_b), (sock_c, task_c)]:
        sock.close()
        with pytest.raises(ConnectionError):
            await task


async def test_viewer_updates_dropped_and_resynced(manager, repo):
    await doc_store.birth(repo, "ws_2", {"wsf_x": "original"})

    editor_sock, viewer_sock = FakeSocket(), FakeSocket()
    task_e = await _connect(manager, "ws_2", editor_sock, "user_e", "editor")
    task_v = await _connect(manager, "ws_2", viewer_sock, "user_v", "viewer")
    handshake_count = len(viewer_sock.sent)

    # Viewer crafts a rogue edit and sends it
    rogue = Doc()
    rogue.get(doc_store.FILES_MAP, type=Map)["wsf_x"] = Text("hacked")
    viewer_sock.push(sync.encode_sync_update(rogue.get_update()))
    await asyncio.sleep(0.02)

    # Not persisted, not relayed to the editor
    assert await repo.max_seq("ws_2") == 0
    assert not any(
        sub == sync.SYNC_UPDATE for sub, _ in editor_sock.frames(sync.MESSAGE_SYNC)
    )
    # Viewer got a resync (step1 + step2 beyond the handshake)
    resync = [
        sync.parse_message(f)[1] for f in viewer_sock.sent[handshake_count:]
    ]
    assert sync.SYNC_STEP1 in resync
    assert sync.SYNC_STEP2 in resync

    for sock, task in [(editor_sock, task_e), (viewer_sock, task_v)]:
        sock.close()
        with pytest.raises(ConnectionError):
            await task


async def test_viewer_empty_handshake_step2_does_not_resync_loop(manager, repo):
    """The y-protocol handshake makes EVERY client answer step1 with step2;
    a fresh viewer's diff is empty. Treating it as a mutation triggers
    drop → resync(step1) → step2 → … forever. Empty updates are no-ops."""
    await doc_store.birth(repo, "ws_loop", {"wsf_z": ""})

    viewer_sock = FakeSocket()
    task = await _connect(manager, "ws_loop", viewer_sock, "user_v", "viewer")
    before = len(viewer_sock.sent)

    # The handshake reply a real y-websocket viewer sends: an empty step2
    viewer_sock.push(sync.encode_sync_step2(b"\x00\x00"))
    await asyncio.sleep(0.05)

    # No resync sent back (no step1/step2 after the handshake), nothing persisted
    assert viewer_sock.sent[before:] == []
    assert await repo.max_seq("ws_loop") == 0

    viewer_sock.close()
    with pytest.raises(ConnectionError):
        await task


async def test_awareness_relay_replay_and_removal(manager, repo):
    await doc_store.birth(repo, "ws_3", {"wsf_y": ""})

    sock_a, sock_b = FakeSocket(), FakeSocket()
    task_a = await _connect(manager, "ws_3", sock_a, "user_a", "owner")
    task_b = await _connect(manager, "ws_3", sock_b, "user_b", "viewer")

    # A broadcasts awareness (client_id=777, clock=1) → B receives it
    payload = (
        sync.write_var_uint(1)
        + sync.write_var_uint(777)
        + sync.write_var_uint(1)
        + sync.write_var_string('{"user":{"name":"A"}}')
    )
    sock_a.push(sync.encode_awareness(payload))
    await asyncio.sleep(0.02)
    assert sock_b.frames(sync.MESSAGE_AWARENESS) == [(None, payload)]

    # Late joiner C gets A's cached awareness replayed at handshake
    sock_c = FakeSocket()
    task_c = await _connect(manager, "ws_3", sock_c, "user_c", "editor")
    assert (None, payload) in sock_c.frames(sync.MESSAGE_AWARENESS)

    # A disconnects → peers get a removal update (same client, clock+1, null)
    sock_a.close()
    with pytest.raises(ConnectionError):
        await task_a
    await asyncio.sleep(0.02)
    last_b = sock_b.frames(sync.MESSAGE_AWARENESS)[-1][1]
    client_id, clock = sync.parse_awareness_client(last_b)
    assert (client_id, clock) == (777, 2)

    for sock, task in [(sock_b, task_b), (sock_c, task_c)]:
        sock.close()
        with pytest.raises(ConnectionError):
            await task


async def test_server_edit_live_room_broadcasts_and_notifies(manager, repo):
    await doc_store.birth(repo, "ws_4", {"wsf_1": "a"})

    sock = FakeSocket()
    task = await _connect(manager, "ws_4", sock, "user_a", "owner")
    before = len(sock.sent)

    def add_file(doc):
        files = doc.get(doc_store.FILES_MAP, type=Map)
        with doc.transaction():
            files["wsf_2"] = Text("new file")

    await manager.server_edit("ws_4", add_file)
    await asyncio.sleep(0.02)

    tags = [sync.parse_message(f)[0] for f in sock.sent[before:]]
    assert sync.MESSAGE_SYNC in tags  # the content update
    assert sync.MESSAGE_FILES_CHANGED in tags  # the refetch signal
    assert await repo.max_seq("ws_4") == 1

    sock.close()
    with pytest.raises(ConnectionError):
        await task


async def test_server_edit_cold_room_persists(manager, repo):
    await doc_store.birth(repo, "ws_5", {"wsf_1": "x"})

    def add_file(doc):
        files = doc.get(doc_store.FILES_MAP, type=Map)
        with doc.transaction():
            files["wsf_2"] = Text("cold")

    await manager.server_edit("ws_5", add_file)

    doc, seq = await doc_store.load(repo, "ws_5")
    assert seq == 1
    assert str(doc.get(doc_store.FILES_MAP, type=Map)["wsf_2"]) == "cold"


async def test_compaction_folds_update_log(manager, repo):
    await doc_store.birth(repo, "ws_6", {"wsf_1": ""})
    manager._settings = get_settings().model_copy(
        update={"ws_snapshot_interval_updates": 3}
    )

    sock = FakeSocket()
    task = await _connect(manager, "ws_6", sock, "user_a", "owner")
    sock.push(sync.encode_sync_step1(Doc().get_state()))
    await asyncio.sleep(0.02)

    doc = _client_doc_from_step(sock)
    text = doc.get(doc_store.FILES_MAP, type=Map)["wsf_1"]
    for i in range(3):
        before = doc.get_state()
        text.insert(len(str(text)), f"line{i}\n")
        sock.push(sync.encode_sync_update(doc.get_update(before)))
        await asyncio.sleep(0.02)

    # 3 updates hit the interval → folded into a snapshot, log cleared
    snapshot = await repo.latest_snapshot("ws_6")
    assert snapshot is not None and snapshot.update_seq == 3
    assert await repo.updates_after("ws_6", 0) == []

    reloaded, seq = await doc_store.load(repo, "ws_6")
    assert seq == 3
    content = str(reloaded.get(doc_store.FILES_MAP, type=Map)["wsf_1"])
    assert content == "line0\nline1\nline2\n"

    sock.close()
    with pytest.raises(ConnectionError):
        await task
