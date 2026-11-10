"""
CollaborationManager — WebSocket rooms speaking y-protocol (design §7).

The server is deliberately dumb about CONTENT (it relays opaque Yjs updates)
but authoritative about STRUCTURE: file create/rename/delete arrive via REST
(§7.1.6) and mutate the room's doc server-side through `server_edit`,
followed by a file-listing-changed frame so clients refetch metadata.

Viewer enforcement (§7.1.5): the client mounts readOnly (primary); the
server drops doc-update frames from viewers (safety net) and immediately
re-syncs the offender from server state. Awareness from viewers is relayed —
viewers have cursors.

Single-instance MVP: rooms live in this process. The Redis backplane
(design decision #4) slots in at the broadcast seam in phase 2.
"""

import asyncio
import logging
import uuid
from contextlib import suppress
from dataclasses import dataclass, field
from typing import Protocol

from pycrdt import Doc

from app.config import Settings
from app.services.collaboration import doc_store, sync
from app.services.collaboration.backplane import BaseBackplane

logger = logging.getLogger(__name__)


class SocketLike(Protocol):
    """The slice of a WebSocket the manager needs (testable without ASGI)."""

    async def receive_bytes(self) -> bytes: ...
    async def send_bytes(self, data: bytes) -> None: ...


@dataclass
class Connection:
    id: str
    socket: SocketLike
    user_id: str
    user_name: str
    role: str  # owner | editor | viewer
    last_awareness: bytes | None = None  # raw payload, replayed to late joiners


@dataclass
class Room:
    workspace_id: str
    doc: Doc
    seq: int  # highest persisted update seq
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    conns: dict[str, Connection] = field(default_factory=dict)
    updates_since_compact: int = 0


class CollaborationManager:
    def __init__(
        self, doc_repo_provider, settings: Settings, backplane: BaseBackplane
    ) -> None:
        self._doc_repo_provider = doc_repo_provider
        self._settings = settings
        self._backplane = backplane
        self._rooms: dict[str, Room] = {}
        self._rooms_lock = asyncio.Lock()

    # ── room lifecycle ─────────────────────────────────────────────

    async def _get_or_load_room(self, workspace_id: str) -> Room:
        async with self._rooms_lock:
            room = self._rooms.get(workspace_id)
            if room is None:
                async with self._doc_repo_provider() as repo:
                    doc, seq = await doc_store.load(repo, workspace_id)
                room = Room(workspace_id=workspace_id, doc=doc, seq=seq)
                self._rooms[workspace_id] = room

                async def on_remote(kind: str, payload: bytes, remote_seq: int) -> None:
                    await self._on_remote(room, kind, payload, remote_seq)

                await self._backplane.join(workspace_id, on_remote)
            return room

    async def _maybe_unload(self, room: Room) -> None:
        async with self._rooms_lock:
            if not room.conns and self._rooms.get(room.workspace_id) is room:
                if room.updates_since_compact > 0:
                    with suppress(Exception):
                        if await self._backplane.try_lock(
                            f"compact:{room.workspace_id}", 30
                        ):
                            async with self._doc_repo_provider() as repo:
                                await doc_store.compact(
                                    repo, room.workspace_id, room.doc, room.seq
                                )
                await self._backplane.leave(room.workspace_id)
                del self._rooms[room.workspace_id]

    # ── connection lifecycle ───────────────────────────────────────

    async def handle_connection(
        self,
        socket: SocketLike,
        workspace_id: str,
        user_id: str,
        user_name: str,
        role: str,
    ) -> None:
        """Run a connection to completion. Caller has already authenticated,
        authorized (membership) and accepted the socket."""
        room = await self._get_or_load_room(workspace_id)
        conn = Connection(
            id=f"conn_{uuid.uuid4().hex[:8]}",
            socket=socket,
            user_id=user_id,
            user_name=user_name,
            role=role,
        )
        async with room.lock:
            room.conns[conn.id] = conn
            # Handshake: our state vector (client answers with its diff),
            # then replay peers' cached awareness so cursors appear at once
            await self._send(conn, sync.encode_sync_step1(room.doc.get_state()))
            for other in room.conns.values():
                if other.id != conn.id and other.last_awareness:
                    await self._send(conn, sync.encode_awareness(other.last_awareness))

        try:
            while True:
                data = await socket.receive_bytes()
                await self._handle_message(room, conn, data)
        finally:
            async with room.lock:
                room.conns.pop(conn.id, None)
                if conn.last_awareness:
                    with suppress(Exception):
                        client_id, clock = sync.parse_awareness_client(conn.last_awareness)
                        await self._broadcast(
                            room,
                            sync.encode_awareness_removal(client_id, clock + 1),
                            exclude=conn.id,
                        )
            await self._maybe_unload(room)

    # ── message handling ───────────────────────────────────────────

    async def _handle_message(self, room: Room, conn: Connection, data: bytes) -> None:
        msg_type, subtype, payload = sync.parse_message(data)

        if msg_type == sync.MESSAGE_SYNC:
            if subtype == sync.SYNC_STEP1:
                # Client sent its state vector → answer with our diff
                async with room.lock:
                    diff = room.doc.get_update(payload)
                await self._send(conn, sync.encode_sync_step2(diff))
                return

            # SYNC_STEP2 / SYNC_UPDATE both carry a Yjs update.
            # Empty updates (b"\x00\x00") are benign handshake replies —
            # every client answers our step1 with step2, and a fresh
            # client's diff is empty. They must NOT hit the viewer
            # drop+resync path (resync sends step1 → client replies step2 →
            # infinite ping-pong) and aren't worth persisting for editors.
            if payload == b"\x00\x00":
                return

            if conn.role == "viewer":
                # Drop + resync (§7.1.5). The viewer's local fork never
                # propagates; a fresh step1 prompts it to reconcile.
                logger.warning(
                    "Dropped doc update from viewer %s in %s",
                    conn.user_id,
                    room.workspace_id,
                )
                async with room.lock:
                    await self._send(conn, sync.encode_sync_step1(room.doc.get_state()))
                    await self._send(conn, sync.encode_sync_step2(room.doc.get_update()))
                return

            async with room.lock:
                room.doc.apply_update(payload)
                seq = await self._backplane.next_seq(room.workspace_id, room.seq)
                room.seq = seq
                await self._broadcast(room, sync.encode_sync_update(payload), exclude=conn.id)
            await self._backplane.publish(room.workspace_id, "update", payload, seq)
            await self._persist_update(room, seq, payload)
            return

        if msg_type == sync.MESSAGE_AWARENESS:
            conn.last_awareness = payload
            # Echo awareness to the SENDER too (as the reference y-websocket
            # server does): y-websocket closes and reconnects a socket that has
            # received nothing for 30 s, and a solo editor's own 15 s awareness
            # renewals are the only traffic there is. Excluding the sender made
            # every single-user session reconnect once a minute (editor remount,
            # cursor jumping to the top). Applying your own awareness is a no-op.
            async with room.lock:
                await self._broadcast(room, sync.encode_awareness(payload))
            await self._backplane.publish(room.workspace_id, "awareness", payload)
            return

        logger.debug("Ignoring unknown message type %d", msg_type)

    # ── frames from other instances (Redis backplane) ─────────────

    async def _on_remote(self, room: Room, kind: str, payload: bytes, seq: int) -> None:
        """A frame produced on another instance: apply to our room doc
        (so late joiners here sync correctly) and forward to local sockets.
        Never persisted — the origin instance already did that."""
        if kind == "update":
            async with room.lock:
                room.doc.apply_update(payload)
                room.seq = max(room.seq, seq)
                await self._broadcast(room, sync.encode_sync_update(payload))
            return
        if kind == "awareness":
            async with room.lock:
                await self._broadcast(room, sync.encode_awareness(payload))
            return
        if kind == "files":
            async with room.lock:
                await self._broadcast(room, sync.encode_files_changed())

    # ── server-side structure edits (REST file ops, §7.1.6) ───────

    async def server_edit(self, workspace_id: str, edit_fn, repo=None) -> None:
        """Apply `edit_fn(doc)` to the workspace doc, persist, broadcast.
        Works whether or not the room is live.

        REST handlers MUST pass their request-scoped DocRepository as `repo`:
        the request session already holds the SQLite write lock (uncommitted
        workspace/file rows), so opening a second session here deadlocks
        until busy_timeout."""
        async with self._rooms_lock:
            room = self._rooms.get(workspace_id)

        if room is not None:
            async with room.lock:
                before = room.doc.get_state()
                edit_fn(room.doc)
                update = room.doc.get_update(before)
                seq = await self._backplane.next_seq(room.workspace_id, room.seq)
                room.seq = seq
                await self._broadcast(room, sync.encode_sync_update(update))
            await self._backplane.publish(workspace_id, "update", update, seq)
            if repo is not None:
                await doc_store.append(repo, workspace_id, seq, update)
                room.updates_since_compact += 1
            else:
                await self._persist_update(room, seq, update)
            await self.notify_files_changed(workspace_id)
            return

        # Room not live: edit against a materialized doc, append to the log
        if repo is not None:
            doc, seq = await doc_store.load(repo, workspace_id)
            before = doc.get_state()
            edit_fn(doc)
            update = doc.get_update(before)
            next_seq = await self._backplane.next_seq(workspace_id, seq)
            await doc_store.append(repo, workspace_id, next_seq, update)
            await self._backplane.publish(workspace_id, "update", update, next_seq)
            await self._backplane.publish(workspace_id, "files", b"")
            return
        async with self._doc_repo_provider() as repo_cm:
            doc, seq = await doc_store.load(repo_cm, workspace_id)
            before = doc.get_state()
            edit_fn(doc)
            update = doc.get_update(before)
            next_seq = await self._backplane.next_seq(workspace_id, seq)
            await doc_store.append(repo_cm, workspace_id, next_seq, update)
            await self._backplane.publish(workspace_id, "update", update, next_seq)
            await self._backplane.publish(workspace_id, "files", b"")

    async def notify_files_changed(self, workspace_id: str) -> None:
        """File metadata changed via REST → tell clients to refetch,
        on this instance and every other one."""
        async with self._rooms_lock:
            room = self._rooms.get(workspace_id)
        if room is not None:
            async with room.lock:
                await self._broadcast(room, sync.encode_files_changed())
        await self._backplane.publish(workspace_id, "files", b"")

    # ── plumbing ───────────────────────────────────────────────────

    async def _persist_update(self, room: Room, seq: int, payload: bytes) -> None:
        async with self._doc_repo_provider() as repo:
            await doc_store.append(repo, room.workspace_id, seq, payload)
        room.updates_since_compact += 1
        if room.updates_since_compact >= self._settings.ws_snapshot_interval_updates:
            room.updates_since_compact = 0
            if await self._backplane.try_lock(f"compact:{room.workspace_id}", 30):
                async with self._doc_repo_provider() as repo:
                    await doc_store.compact(repo, room.workspace_id, room.doc, room.seq)

    async def _broadcast(self, room: Room, frame: bytes, exclude: str | None = None) -> None:
        """Fan out to room members. (Phase 2: this seam becomes the Redis
        backplane for multi-instance.)"""
        for conn in list(room.conns.values()):
            if conn.id == exclude:
                continue
            await self._send(conn, frame)

    async def _send(self, conn: Connection, frame: bytes) -> None:
        try:
            await conn.socket.send_bytes(frame)
        except Exception:
            logger.debug("Send failed to %s (disconnecting)", conn.id)


# ── module singleton (same idiom as get_runtime) ──────────────────

_manager: CollaborationManager | None = None


def get_collab_manager() -> CollaborationManager:
    global _manager
    if _manager is None:
        from app.config import get_settings
        from app.services.collaboration.backplane import (
            InMemoryBackplane,
            RedisBackplane,
        )
        from app.services.collaboration.providers import make_doc_repo_provider

        settings = get_settings()
        backplane = (
            RedisBackplane()
            if settings.realtime_backplane == "redis"
            else InMemoryBackplane()
        )
        _manager = CollaborationManager(
            make_doc_repo_provider(settings), settings, backplane
        )
    return _manager


def reset_collab_manager() -> None:
    """Test hook: drop the singleton so each test gets a fresh manager."""
    global _manager
    _manager = None
