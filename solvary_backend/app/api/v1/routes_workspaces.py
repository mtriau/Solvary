from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_workspace_service
from app.models.user import User
from app.schemas.workspaces import (
    FileCreate,
    FileRename,
    FileResponse,
    MemberAdd,
    MemberResponse,
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceUpdate,
)
from app.services.workspace_service import WorkspaceService

router = APIRouter(prefix="/v1/workspaces", tags=["workspaces"])

CurrentUser = Annotated[User, Depends(get_current_user)]
Service = Annotated[WorkspaceService, Depends(get_workspace_service)]


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    data: WorkspaceCreate, user: CurrentUser, service: Service
) -> WorkspaceResponse:
    return await service.create(user, data)


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(user: CurrentUser, service: Service) -> list[WorkspaceResponse]:
    return await service.list_mine(user)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str, user: CurrentUser, service: Service
) -> WorkspaceResponse:
    return await service.get(workspace_id, user)


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str, data: WorkspaceUpdate, user: CurrentUser, service: Service
) -> WorkspaceResponse:
    return await service.update(workspace_id, user, data)


@router.delete("/{workspace_id}", status_code=204)
async def delete_workspace(workspace_id: str, user: CurrentUser, service: Service) -> None:
    await service.delete(workspace_id, user)


# ── members ────────────────────────────────────────────────────────


@router.get("/{workspace_id}/members", response_model=list[MemberResponse])
async def list_members(
    workspace_id: str, user: CurrentUser, service: Service
) -> list[MemberResponse]:
    return await service.list_members(workspace_id, user)


@router.post("/{workspace_id}/members", response_model=MemberResponse, status_code=201)
async def add_member(
    workspace_id: str, data: MemberAdd, user: CurrentUser, service: Service
) -> MemberResponse:
    return await service.add_member(workspace_id, user, data)


@router.delete("/{workspace_id}/members/{member_id}", status_code=204)
async def remove_member(
    workspace_id: str, member_id: str, user: CurrentUser, service: Service
) -> None:
    await service.remove_member(workspace_id, user, member_id)


# ── files (metadata only; content flows over the collab socket) ───


@router.get("/{workspace_id}/files", response_model=list[FileResponse])
async def list_files(
    workspace_id: str, user: CurrentUser, service: Service
) -> list[FileResponse]:
    return await service.list_files(workspace_id, user)


@router.post("/{workspace_id}/files", response_model=FileResponse, status_code=201)
async def create_file(
    workspace_id: str, data: FileCreate, user: CurrentUser, service: Service
) -> FileResponse:
    return await service.create_file(workspace_id, user, data)


@router.patch("/{workspace_id}/files/{file_id}", response_model=FileResponse)
async def rename_file(
    workspace_id: str, file_id: str, data: FileRename, user: CurrentUser, service: Service
) -> FileResponse:
    return await service.rename_file(workspace_id, user, file_id, data)


@router.delete("/{workspace_id}/files/{file_id}", status_code=204)
async def delete_file(
    workspace_id: str, file_id: str, user: CurrentUser, service: Service
) -> None:
    await service.delete_file(workspace_id, user, file_id)
