from datetime import date, datetime

from pydantic import BaseModel

from app.schemas.problems import Difficulty


class TotalsStats(BaseModel):
    solved: int          # distinct problems with an accepted submission
    total_problems: int  # public problems available
    submissions: int
    accepted_submissions: int
    acceptance_rate: float  # 0..1; 0 when no submissions
    current_streak_days: int
    longest_streak_days: int


class DifficultyStat(BaseModel):
    difficulty: Difficulty
    solved: int
    total: int


class LanguageStat(BaseModel):
    language: str
    submissions: int
    solved: int  # distinct problems accepted in this language


class HeatmapDay(BaseModel):
    day: date
    count: int  # submissions that day


class Badge(BaseModel):
    id: str
    name: str
    description: str
    icon: str  # emoji
    earned: bool


class RecentSubmission(BaseModel):
    id: str
    problem_slug: str
    problem_title: str
    difficulty: Difficulty
    language: str
    verdict: str
    runtime_ms: int | None
    created_at: datetime


class StatsResponse(BaseModel):
    totals: TotalsStats
    by_difficulty: list[DifficultyStat]
    by_language: list[LanguageStat]
    heatmap: list[HeatmapDay]  # oldest → newest, includes zero days
    badges: list[Badge]
    recent: list[RecentSubmission]
