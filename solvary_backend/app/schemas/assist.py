from pydantic import BaseModel, Field


class AssistRequest(BaseModel):
    """`POST /v1/assist/explain` — everything optional except the question."""

    question: str = Field(min_length=1, max_length=2000)
    problem_id: str | None = None
    code: str | None = None
    language: str | None = None
    interview_session_id: str | None = Field(
        default=None,
        description="Review a finished mock interview: authorizes its (private) problems",
    )
    verdict: str | None = Field(
        default=None,
        max_length=500,
        description="Free-text summary of the latest verdict, e.g. 'wrong_answer on test 3'",
    )
