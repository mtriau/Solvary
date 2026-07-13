"""Persistence for the CRDT document: latest snapshot + append log of updates
(design §4 DocSnapshot/DocUpdate). Any instance may persist and compact —
Yjs updates are commutative, merges idempotent."""

from abc import ABC, abstractmethod

from app.models.doc import DocSnapshot, DocUpdate


class DocRepository(ABC):
    @abstractmethod
    async def latest_snapshot(self, workspace_id: str) -> DocSnapshot | None: ...

    @abstractmethod
    async def save_snapshot(self, snapshot: DocSnapshot) -> DocSnapshot: ...

    @abstractmethod
    async def updates_after(self, workspace_id: str, seq: int) -> list[DocUpdate]:
        """Updates with seq > given, ordered ascending."""
        ...

    @abstractmethod
    async def append_update(self, update: DocUpdate) -> DocUpdate: ...

    @abstractmethod
    async def delete_updates_upto(self, workspace_id: str, seq: int) -> int: ...

    @abstractmethod
    async def max_seq(self, workspace_id: str) -> int: ...


class MockDocRepository(DocRepository):
    def __init__(self) -> None:
        self._snapshots: list[DocSnapshot] = []
        self._updates: list[DocUpdate] = []

    async def latest_snapshot(self, workspace_id: str) -> DocSnapshot | None:
        candidates = [s for s in self._snapshots if s.workspace_id == workspace_id]
        return max(candidates, key=lambda s: s.update_seq, default=None)

    async def save_snapshot(self, snapshot: DocSnapshot) -> DocSnapshot:
        self._snapshots.append(snapshot)
        return snapshot

    async def updates_after(self, workspace_id: str, seq: int) -> list[DocUpdate]:
        return sorted(
            (
                u
                for u in self._updates
                if u.workspace_id == workspace_id and u.seq > seq
            ),
            key=lambda u: u.seq,
        )

    async def append_update(self, update: DocUpdate) -> DocUpdate:
        self._updates.append(update)
        return update

    async def delete_updates_upto(self, workspace_id: str, seq: int) -> int:
        before = len(self._updates)
        self._updates = [
            u
            for u in self._updates
            if not (u.workspace_id == workspace_id and u.seq <= seq)
        ]
        return before - len(self._updates)

    async def max_seq(self, workspace_id: str) -> int:
        return max(
            (u.seq for u in self._updates if u.workspace_id == workspace_id),
            default=0,
        )
