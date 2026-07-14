from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_problem_service, require_admin
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.problems import (
    ProblemCreate,
    ProblemDetail,
    ProblemSummary,
    ProblemUpdate,
    TestCaseAdmin,
    TestCaseCreate,
)
from app.services.problem_service import ProblemService

router = APIRouter(prefix="/v1/problems", tags=["problems"])


@router.get("", response_model=PaginatedResponse[ProblemSummary])
async def list_problems(
    service: Annotated[ProblemService, Depends(get_problem_service)],
    difficulty: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> PaginatedResponse[ProblemSummary]:
    return await service.list_problems(
        difficulty=difficulty, tag=tag, q=q, cursor=cursor, limit=limit
    )


@router.get("/{slug}", response_model=ProblemDetail)
async def get_problem(
    slug: str,
    service: Annotated[ProblemService, Depends(get_problem_service)],
) -> ProblemDetail:
    return await service.get_by_slug(slug)


@router.post("", response_model=ProblemDetail, status_code=201)
async def create_problem(
    data: ProblemCreate,
    admin: Annotated[User, Depends(require_admin)],
    service: Annotated[ProblemService, Depends(get_problem_service)],
) -> ProblemDetail:
    return await service.create(data, admin)


@router.patch("/{problem_id}", response_model=ProblemDetail)
async def update_problem(
    problem_id: str,
    data: ProblemUpdate,
    _admin: Annotated[User, Depends(require_admin)],
    service: Annotated[ProblemService, Depends(get_problem_service)],
) -> ProblemDetail:
    return await service.update(problem_id, data)


@router.get("/{problem_id}/testcases", response_model=list[TestCaseAdmin])
async def list_testcases(
    problem_id: str,
    _admin: Annotated[User, Depends(require_admin)],
    service: Annotated[ProblemService, Depends(get_problem_service)],
) -> list[TestCaseAdmin]:
    return await service.list_testcases(problem_id)


@router.post("/{problem_id}/testcases", response_model=TestCaseAdmin, status_code=201)
async def add_testcase(
    problem_id: str,
    data: TestCaseCreate,
    _admin: Annotated[User, Depends(require_admin)],
    service: Annotated[ProblemService, Depends(get_problem_service)],
) -> TestCaseAdmin:
    return await service.add_testcase(problem_id, data)
