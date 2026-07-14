"""
WebSocket endpoint for live collaboration (design §5, §7).

Auth: JWT via WebSocket subprotocol ONLY (query-string tokens land in access
logs — §7.2). The y-websocket client passes `protocols: [token]`; we validate
before accept() and echo the token back as the selected subprotocol.

DB access is a short-lived lookup, NOT a Depends(get_db) session — that would
stay open for the entire life of the connection and pin a pool slot per user.

Close codes: 4401 unauthenticated, 4403 not a member.
"""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import get_settings
from app.core.security import decode_access_token
from app.services.collaboration.manager import get_collab_manager
from app.services.collaboration.providers import make_auth_lookup

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/workspaces/{workspace_id}")
async def collaborate(websocket: WebSocket, workspace_id: str) -> None:
    subprotocols = websocket.scope.get("subprotocols") or []
    token = subprotocols[0] if subprotocols else None

    user_id = None
    if token:
        try:
            user_id = decode_access_token(token).get("sub")
        except ValueError:
            user_id = None

    # Accept BEFORE closing on auth failure — starlette turns close-before-
    # accept into a bare HTTP 403 handshake rejection, which erases the
    # 4401/4403 close codes clients rely on to distinguish the cause
    if not user_id:
        await websocket.accept(subprotocol=token)
        await websocket.close(code=4401, reason="Not authenticated")
        return

    lookup = make_auth_lookup(get_settings())
    user, member = await lookup(user_id, workspace_id)
    if user is None:
        await websocket.accept(subprotocol=token)
        await websocket.close(code=4401, reason="Not authenticated")
        return
    if member is None:
        await websocket.accept(subprotocol=token)
        await websocket.close(code=4403, reason="Not a workspace member")
        return

    await websocket.accept(subprotocol=token)
    try:
        await get_collab_manager().handle_connection(
            socket=websocket,
            workspace_id=workspace_id,
            user_id=user.id,
            user_name=user.name,
            role=member.role,
        )
    except WebSocketDisconnect:
        pass
    except Exception:
        logger.exception("Collaboration connection error in %s", workspace_id)
