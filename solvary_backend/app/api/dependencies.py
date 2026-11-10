from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.exceptions import ForbiddenException
from app.models.user import User
from app.repositories import mock_registry
from app.repositories.doc_repository import DocRepository
from app.repositories.interview_repository import (
    InterviewSessionRepository,
    InterviewStageRepository,
    InterviewTemplateRepository,
)
from app.repositories.problem_repository import ProblemRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.submission_repository import SubmissionRepository
from app.repositories.testcase_repository import TestCaseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workspace_repository import (
    FileRepository,
    MemberRepository,
    WorkspaceRepository,
)
from app.services.assist_service import AssistService
from app.services.auth_service import AuthService
from app.services.collaboration.manager import get_collab_manager
from app.services.drill_service import DrillService
from app.services.interview_service import InterviewService
from app.services.llm_service import get_llm_service
from app.services.problem_service import ProblemService
from app.services.queue.runtime import ExecutionRuntime, get_runtime
from app.services.stats_service import StatsService
from app.services.submission_service import SubmissionService
from app.services.user_service import UserService
from app.services.workspace_service import WorkspaceService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# ── DB session dependency ─────────────────────────────────────────


async def get_db(settings: Annotated[Settings, Depends(get_settings)]):
    """Yields a DB session when using real persistence, None for mock mode."""
    if settings.use_mock_db:
        yield None
    else:
        from app.db.engine import get_db_session

        async for session in get_db_session():
            yield session


# ── Repository providers ──────────────────────────────────────────


def get_user_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> UserRepository:
    if settings.use_mock_db:
        return mock_registry.mock_user_repo
    from app.repositories.sqlalchemy_user_repository import SQLAlchemyUserRepository

    assert db is not None
    return SQLAlchemyUserRepository(db)


def get_problem_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> ProblemRepository:
    if settings.use_mock_db:
        return mock_registry.mock_problem_repo
    from app.repositories.sqlalchemy_problem_repository import SQLAlchemyProblemRepository

    assert db is not None
    return SQLAlchemyProblemRepository(db)


def get_testcase_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> TestCaseRepository:
    if settings.use_mock_db:
        return mock_registry.mock_testcase_repo
    from app.repositories.sqlalchemy_testcase_repository import SQLAlchemyTestCaseRepository

    assert db is not None
    return SQLAlchemyTestCaseRepository(db)


def get_submission_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> SubmissionRepository:
    if settings.use_mock_db:
        return mock_registry.mock_submission_repo
    from app.repositories.sqlalchemy_submission_repository import (
        SQLAlchemySubmissionRepository,
    )

    assert db is not None
    return SQLAlchemySubmissionRepository(db)


def get_workspace_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> WorkspaceRepository:
    if settings.use_mock_db:
        return mock_registry.mock_workspace_repo
    from app.repositories.sqlalchemy_workspace_repository import (
        SQLAlchemyWorkspaceRepository,
    )

    assert db is not None
    return SQLAlchemyWorkspaceRepository(db)


def get_member_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> MemberRepository:
    if settings.use_mock_db:
        return mock_registry.mock_member_repo
    from app.repositories.sqlalchemy_workspace_repository import (
        SQLAlchemyMemberRepository,
    )

    assert db is not None
    return SQLAlchemyMemberRepository(db)


def get_file_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> FileRepository:
    if settings.use_mock_db:
        return mock_registry.mock_file_repo
    from app.repositories.sqlalchemy_workspace_repository import (
        SQLAlchemyFileRepository,
    )

    assert db is not None
    return SQLAlchemyFileRepository(db)


# ── Service providers ─────────────────────────────────────────────


def get_refresh_token_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> RefreshTokenRepository:
    if settings.use_mock_db:
        return mock_registry.mock_refresh_token_repo
    from app.repositories.sqlalchemy_refresh_token_repository import (
        SQLAlchemyRefreshTokenRepository,
    )

    assert db is not None
    return SQLAlchemyRefreshTokenRepository(db)


def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    refresh_repo: Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> AuthService:
    return AuthService(user_repo, refresh_repo, settings)


def get_user_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> UserService:
    return UserService(user_repo)


def get_problem_service(
    problem_repo: Annotated[ProblemRepository, Depends(get_problem_repository)],
    testcase_repo: Annotated[TestCaseRepository, Depends(get_testcase_repository)],
) -> ProblemService:
    return ProblemService(problem_repo, testcase_repo)


def get_doc_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> DocRepository:
    if settings.use_mock_db:
        return mock_registry.mock_doc_repo
    from app.repositories.sqlalchemy_doc_repository import SQLAlchemyDocRepository

    assert db is not None
    return SQLAlchemyDocRepository(db)


def get_workspace_service(
    workspace_repo: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
    file_repo: Annotated[FileRepository, Depends(get_file_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    problem_repo: Annotated[ProblemRepository, Depends(get_problem_repository)],
    doc_repo: Annotated[DocRepository, Depends(get_doc_repository)],
) -> WorkspaceService:
    # doc_repo shares the request session — doc writes must join the request
    # transaction or they deadlock on SQLite's single-writer lock
    return WorkspaceService(
        workspace_repo,
        member_repo,
        file_repo,
        user_repo,
        problem_repo,
        get_collab_manager(),
        doc_repo,
    )


# ── Mock interviews ───────────────────────────────────────────────


def get_interview_template_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> InterviewTemplateRepository:
    if settings.use_mock_db:
        return mock_registry.mock_interview_template_repo
    from app.repositories.sqlalchemy_interview_repository import (
        SQLAlchemyInterviewTemplateRepository,
    )

    assert db is not None
    return SQLAlchemyInterviewTemplateRepository(db)


def get_interview_stage_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> InterviewStageRepository:
    if settings.use_mock_db:
        return mock_registry.mock_interview_stage_repo
    from app.repositories.sqlalchemy_interview_repository import (
        SQLAlchemyInterviewStageRepository,
    )

    assert db is not None
    return SQLAlchemyInterviewStageRepository(db)


def get_interview_session_repository(
    settings: Annotated[Settings, Depends(get_settings)],
    db: Annotated[AsyncSession | None, Depends(get_db)],
) -> InterviewSessionRepository:
    if settings.use_mock_db:
        return mock_registry.mock_interview_session_repo
    from app.repositories.sqlalchemy_interview_repository import (
        SQLAlchemyInterviewSessionRepository,
    )

    assert db is not None
    return SQLAlchemyInterviewSessionRepository(db)


def get_interview_service(
    template_repo: Annotated[
        InterviewTemplateRepository, Depends(get_interview_template_repository)
    ],
    stage_repo: Annotated[InterviewStageRepository, Depends(get_interview_stage_repository)],
    session_repo: Annotated[
        InterviewSessionRepository, Depends(get_interview_session_repository)
    ],
    problem_repo: Annotated[ProblemRepository, Depends(get_problem_repository)],
    testcase_repo: Annotated[TestCaseRepository, Depends(get_testcase_repository)],
    submission_repo: Annotated[SubmissionRepository, Depends(get_submission_repository)],
    workspace_service: Annotated[WorkspaceService, Depends(get_workspace_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> InterviewService:
    return InterviewService(
        template_repo,
        stage_repo,
        session_repo,
        problem_repo,
        testcase_repo,
        submission_repo,
        workspace_service,
        settings,
    )


def get_submission_service(
    submission_repo: Annotated[SubmissionRepository, Depends(get_submission_repository)],
    problem_repo: Annotated[ProblemRepository, Depends(get_problem_repository)],
    testcase_repo: Annotated[TestCaseRepository, Depends(get_testcase_repository)],
    workspace_repo: Annotated[WorkspaceRepository, Depends(get_workspace_repository)],
    member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
    runtime: Annotated[ExecutionRuntime, Depends(get_runtime)],
    settings: Annotated[Settings, Depends(get_settings)],
    interviews: Annotated[InterviewService, Depends(get_interview_service)],
) -> SubmissionService:
    return SubmissionService(
        submission_repo,
        problem_repo,
        testcase_repo,
        workspace_repo,
        member_repo,
        runtime,
        settings,
        interview_service=interviews,
    )


def get_assist_service(
    problem_repo: Annotated[ProblemRepository, Depends(get_problem_repository)],
    testcase_repo: Annotated[TestCaseRepository, Depends(get_testcase_repository)],
    settings: Annotated[Settings, Depends(get_settings)],
    interviews: Annotated[InterviewService, Depends(get_interview_service)],
) -> AssistService:
    return AssistService(
        problem_repo, testcase_repo, get_llm_service(), settings, interview_service=interviews
    )


def get_stats_service(
    submission_repo: Annotated[SubmissionRepository, Depends(get_submission_repository)],
    problem_repo: Annotated[ProblemRepository, Depends(get_problem_repository)],
    member_repo: Annotated[MemberRepository, Depends(get_member_repository)],
    session_repo: Annotated[
        InterviewSessionRepository, Depends(get_interview_session_repository)
    ],
    stage_repo: Annotated[InterviewStageRepository, Depends(get_interview_stage_repository)],
    template_repo: Annotated[
        InterviewTemplateRepository, Depends(get_interview_template_repository)
    ],
) -> StatsService:
    return StatsService(
        submission_repo, problem_repo, member_repo, session_repo, stage_repo, template_repo
    )


def get_drill_service(
    problem_repo: Annotated[ProblemRepository, Depends(get_problem_repository)],
    testcase_repo: Annotated[TestCaseRepository, Depends(get_testcase_repository)],
    submission_repo: Annotated[SubmissionRepository, Depends(get_submission_repository)],
) -> DrillService:
    return DrillService(problem_repo, testcase_repo, submission_repo)


# ── Auth dependencies ─────────────────────────────────────────────


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    return await auth_service.get_current_user(token)


async def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != "admin":
        raise ForbiddenException("Admin privileges required")
    return current_user


# ── Execution quota (§6.6) ────────────────────────────────────────


async def check_execution_quota(
    current_user: Annotated[User, Depends(get_current_user)],
    runtime: Annotated[ExecutionRuntime, Depends(get_runtime)],
) -> AsyncIterator[None]:
    """Reserves a concurrency slot. On success the worker releases it when
    the job ends; if the handler raises (validation, RBAC, body errors…) no
    job is ever enqueued, so the slot must be released here — otherwise two
    rejected requests lock the user out of judging until restart."""
    await runtime.quota.check_and_reserve(current_user.id)
    try:
        yield
    except Exception:
        await runtime.quota.release(current_user.id)
        raise
