"""
Server-side CRDT document lifecycle (design §7.4, decision #13):

  1. birth    — create the initial snapshot at workspace creation, seeding
                starter content server-side (first-client-seeds has a
                duplication race — two simultaneous joiners each insert)
  2. load     — latest snapshot + pending update log → live Doc
  3. compact  — fold the update log into a fresh snapshot

The Yjs doc holds ONE structure: Map "files" keyed by WorkspaceFile.id
(never path — rename must preserve content identity), values are Y.Text.
"""

import uuid

from pycrdt import Doc, Map, Text

from app.models.doc import DocSnapshot, DocUpdate
from app.repositories.doc_repository import DocRepository

FILES_MAP = "files"


def new_doc() -> Doc:
    doc = Doc()
    doc.get(FILES_MAP, type=Map)
    return doc


async def birth(
    repo: DocRepository, workspace_id: str, initial_files: dict[str, str]
) -> None:
    """Create the workspace's initial snapshot: {file_id: content}."""
    doc = new_doc()
    files = doc.get(FILES_MAP, type=Map)
    with doc.transaction():
        for file_id, content in initial_files.items():
            files[file_id] = Text(content)
    await repo.save_snapshot(
        DocSnapshot(
            id=f"snap_{uuid.uuid4().hex[:8]}",
            workspace_id=workspace_id,
            state=doc.get_update(),
            update_seq=0,
        )
    )


async def load(repo: DocRepository, workspace_id: str) -> tuple[Doc, int]:
    """Materialize the doc: snapshot + pending updates. Returns (doc, seq)."""
    doc = new_doc()
    snapshot = await repo.latest_snapshot(workspace_id)
    seq = 0
    if snapshot:
        doc.apply_update(snapshot.state)
        seq = snapshot.update_seq
    for update in await repo.updates_after(workspace_id, seq):
        doc.apply_update(update.payload)
        seq = update.seq
    return doc, seq


async def append(repo: DocRepository, workspace_id: str, seq: int, payload: bytes) -> None:
    await repo.append_update(
        DocUpdate(
            id=f"upd_{uuid.uuid4().hex[:8]}",
            workspace_id=workspace_id,
            seq=seq,
            payload=payload,
        )
    )


async def compact(repo: DocRepository, workspace_id: str, doc: Doc, seq: int) -> None:
    """Fold the update log into a new snapshot; safe from any instance —
    Yjs merges are commutative and idempotent."""
    await repo.save_snapshot(
        DocSnapshot(
            id=f"snap_{uuid.uuid4().hex[:8]}",
            workspace_id=workspace_id,
            state=doc.get_update(),
            update_seq=seq,
        )
    )
    await repo.delete_updates_upto(workspace_id, seq)
