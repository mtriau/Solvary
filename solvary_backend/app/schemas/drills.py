from pydantic import BaseModel

from app.schemas.problems import ProblemDetail


class DrillSummary(BaseModel):
    id: str
    slug: str
    title: str
    topic: str
    order: int
    solved: bool
    attempts: int


class DrillTopic(BaseModel):
    slug: str
    title: str
    blurb: str
    drills: list[DrillSummary]
    solved: int
    total: int


class DrillList(BaseModel):
    topics: list[DrillTopic]
    solved: int
    total: int
    # first unsolved drill across all topics, for a "start practising" button
    next_slug: str | None


class DrillDetail(ProblemDetail):
    topic: str
    topic_title: str
    order: int
    position: int  # 1-based within the topic
    topic_total: int
    editorial_md: str | None  # the idiomatic solution + why; the UI gates it
    solved: bool
    attempts: int
    prev_slug: str | None
    next_slug: str | None  # next in topic order (then the next topic)
    next_unsolved_slug: str | None
