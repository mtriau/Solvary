from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class DocSnapshot:
    """Compacted binary CRDT state for a workspace (full doc as a Yjs update)."""

    id: str
    workspace_id: str
    state: bytes
    update_seq: int  # DocUpdates with seq <= this are folded in
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DocUpdate:
    """One raw Yjs update in the append log since the last snapshot."""

    id: str
    workspace_id: str
    seq: int
    payload: bytes
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
