import uuid

from pycrdt import Map, Text

from app.core.exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.problem import Problem
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceFile, WorkspaceMember
from app.repositories.doc_repository import DocRepository
from app.repositories.problem_repository import ProblemRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import (
    FileRepository,
    MemberRepository,
    WorkspaceRepository,
)
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
from app.services.collaboration import doc_store
from app.services.collaboration.manager import CollaborationManager

_ROLE_RANK = {"viewer": 0, "editor": 1, "owner": 2}

_DEFAULT_FILENAMES = {"python": "main.py", "javascript": "main.js"}


class WorkspaceService:
    def __init__(
        self,
        workspace_repo: WorkspaceRepository,
        member_repo: MemberRepository,
        file_repo: FileRepository,
        user_repo: UserRepository,
        problem_repo: ProblemRepository,
        collab: CollaborationManager,
        doc_repo: DocRepository,
    ) -> None:
        self._workspaces = workspace_repo
        self._members = member_repo
        self._files = file_repo
        self._users = user_repo
        self._problems = problem_repo
        self._collab = collab
        self._doc_repo = doc_repo

    # ── RBAC ───────────────────────────────────────────────────────

    async def require_role(
        self, workspace_id: str, user: User, minimum: str
    ) -> tuple[Workspace, WorkspaceMember]:
        workspace = await self._workspaces.get_by_id(workspace_id)
        if not workspace:
            raise NotFoundException(f"Workspace {workspace_id} not found")
        member = await self._members.get_by_workspace_and_user(workspace_id, user.id)
        if member is None:
            raise ForbiddenException("Not a member of this workspace")
        if _ROLE_RANK[member.role] < _ROLE_RANK[minimum]:
            raise ForbiddenException(f"Requires {minimum} role")
        return workspace, member

    # ── workspaces ─────────────────────────────────────────────────

    async def create(self, user: User, data: WorkspaceCreate) -> WorkspaceResponse:
        problem: Problem | None = None
        if data.problem_id:
            problem = await self._problems.get_by_id(data.problem_id)
            if not problem:
                raise NotFoundException(f"Problem {data.problem_id} not found")

        name = data.name or (problem.title if problem else None)
        if not name:
            raise BadRequestException("Workspace name is required")

        workspace = Workspace(
            id=f"ws_{uuid.uuid4().hex[:8]}",
            name=name,
            owner_id=user.id,
            language=data.language,
            problem_id=problem.id if problem else None,
        )
        await self._workspaces.create(workspace)
        await self._members.create(
            WorkspaceMember(
                id=f"wsm_{uuid.uuid4().hex[:8]}",
                workspace_id=workspace.id,
                user_id=user.id,
                role="owner",
            )
        )

        # Default file + server-side doc birth (§7.4 — no first-client race)
        default_path = _DEFAULT_FILENAMES.get(data.language, "main.txt")
        file = WorkspaceFile(
            id=f"wsf_{uuid.uuid4().hex[:8]}",
            workspace_id=workspace.id,
            path=default_path,
            language=data.language,
        )
        await self._files.create(file)
        # Challenge attempts are seeded with the problem's starter code —
        # server-side, so there is no first-client seeding race (design 7.4)
        starter = problem.starter_code.get(data.language, "") if problem else ""
        await doc_store.birth(self._doc_repo, workspace.id, {file.id: starter})

        return self._to_response(workspace, "owner", problem)

    async def list_mine(self, user: User) -> list[WorkspaceResponse]:
        memberships = await self._members.list_by_user(user.id)
        out = []
        for m in sorted(memberships, key=lambda m: m.created_at, reverse=True):
            workspace = await self._workspaces.get_by_id(m.workspace_id)
            if workspace:
                out.append(self._to_response(workspace, m.role, await self._problem_of(workspace)))
        return out

    async def get(self, workspace_id: str, user: User) -> WorkspaceResponse:
        workspace, member = await self.require_role(workspace_id, user, "viewer")
        return self._to_response(workspace, member.role, await self._problem_of(workspace))

    async def update(
        self, workspace_id: str, user: User, data: WorkspaceUpdate
    ) -> WorkspaceResponse:
        workspace, member = await self.require_role(workspace_id, user, "editor")
        if data.name is not None:
            workspace.name = data.name
        if data.language is not None:
            workspace.language = data.language
        await self._workspaces.update(workspace)
        return self._to_response(workspace, member.role, await self._problem_of(workspace))

    async def delete(self, workspace_id: str, user: User) -> None:
        await self.require_role(workspace_id, user, "owner")
        await self._workspaces.delete(workspace_id)

    # ── members ────────────────────────────────────────────────────

    async def list_members(self, workspace_id: str, user: User) -> list[MemberResponse]:
        await self.require_role(workspace_id, user, "viewer")
        members = await self._members.list_by_workspace(workspace_id)
        out = []
        for m in members:
            u = await self._users.get_by_id(m.user_id)
            if u:
                out.append(
                    MemberResponse(
                        id=m.id,
                        user_id=u.id,
                        name=u.name,
                        email=u.email,
                        avatar_url=u.avatar_url,
                        role=m.role,
                    )
                )
        return out

    async def add_member(
        self, workspace_id: str, user: User, data: MemberAdd
    ) -> MemberResponse:
        await self.require_role(workspace_id, user, "owner")
        target = await self._users.get_by_email(data.email)
        if not target:
            raise NotFoundException(f"No user with email {data.email}")
        existing = await self._members.get_by_workspace_and_user(workspace_id, target.id)
        if existing:
            raise ConflictException("Already a member")
        member = WorkspaceMember(
            id=f"wsm_{uuid.uuid4().hex[:8]}",
            workspace_id=workspace_id,
            user_id=target.id,
            role=data.role,
        )
        await self._members.create(member)
        return MemberResponse(
            id=member.id,
            user_id=target.id,
            name=target.name,
            email=target.email,
            avatar_url=target.avatar_url,
            role=member.role,
        )

    async def remove_member(self, workspace_id: str, user: User, member_id: str) -> None:
        workspace, _ = await self.require_role(workspace_id, user, "owner")
        member = await self._members.get_by_id(member_id)
        if not member or member.workspace_id != workspace_id:
            raise NotFoundException("Member not found")
        if member.user_id == workspace.owner_id:
            raise BadRequestException("Cannot remove the owner")
        await self._members.delete(member_id)

    # ── files (metadata is REST-authoritative — §4/§7.1.6) ────────

    async def list_files(self, workspace_id: str, user: User) -> list[FileResponse]:
        await self.require_role(workspace_id, user, "viewer")
        files = await self._files.list_by_workspace(workspace_id)
        return [FileResponse(id=f.id, path=f.path, language=f.language) for f in files]

    async def create_file(
        self, workspace_id: str, user: User, data: FileCreate
    ) -> FileResponse:
        await self.require_role(workspace_id, user, "editor")
        if await self._files.get_by_workspace_and_path(workspace_id, data.path):
            raise ConflictException(f"File '{data.path}' already exists")

        file = WorkspaceFile(
            id=f"wsf_{uuid.uuid4().hex[:8]}",
            workspace_id=workspace_id,
            path=data.path,
            language=data.language,
        )
        await self._files.create(file)

        def add_text(doc):
            files_map = doc.get(doc_store.FILES_MAP, type=Map)
            with doc.transaction():
                files_map[file.id] = Text("")

        await self._collab.server_edit(workspace_id, add_text, repo=self._doc_repo)
        return FileResponse(id=file.id, path=file.path, language=file.language)

    async def rename_file(
        self, workspace_id: str, user: User, file_id: str, data: FileRename
    ) -> FileResponse:
        await self.require_role(workspace_id, user, "editor")
        file = await self._files.get_by_id(file_id)
        if not file or file.workspace_id != workspace_id:
            raise NotFoundException("File not found")
        if await self._files.get_by_workspace_and_path(workspace_id, data.path):
            raise ConflictException(f"File '{data.path}' already exists")

        # Metadata-only: CRDT content is keyed by file id, so concurrent
        # edits during the rename lose nothing (design §4)
        file.path = data.path
        await self._files.update(file)
        await self._collab.notify_files_changed(workspace_id)
        return FileResponse(id=file.id, path=file.path, language=file.language)

    async def delete_file(self, workspace_id: str, user: User, file_id: str) -> None:
        await self.require_role(workspace_id, user, "editor")
        file = await self._files.get_by_id(file_id)
        if not file or file.workspace_id != workspace_id:
            raise NotFoundException("File not found")
        files = await self._files.list_by_workspace(workspace_id)
        if len(files) <= 1:
            raise BadRequestException("A workspace needs at least one file")

        await self._files.delete(file_id)

        def remove_text(doc):
            files_map = doc.get(doc_store.FILES_MAP, type=Map)
            with doc.transaction():
                if file_id in files_map:
                    del files_map[file_id]

        await self._collab.server_edit(workspace_id, remove_text, repo=self._doc_repo)

    # ── mapping ────────────────────────────────────────────────────

    async def _problem_of(self, w: Workspace) -> Problem | None:
        return await self._problems.get_by_id(w.problem_id) if w.problem_id else None

    @staticmethod
    def _to_response(
        w: Workspace, my_role: str, problem: Problem | None = None
    ) -> WorkspaceResponse:
        return WorkspaceResponse(
            id=w.id,
            name=w.name,
            owner_id=w.owner_id,
            language=w.language,
            problem_id=w.problem_id,
            problem_slug=problem.slug if problem else None,
            problem_title=problem.title if problem else None,
            my_role=my_role,  # type: ignore[arg-type]
            created_at=w.created_at,
        )
