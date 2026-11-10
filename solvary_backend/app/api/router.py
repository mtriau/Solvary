from fastapi import APIRouter

from app.api.v1 import (
    routes_assist,
    routes_auth,
    routes_drills,
    routes_execution,
    routes_health,
    routes_interviews,
    routes_problems,
    routes_stats,
    routes_submissions,
    routes_users,
    routes_workspaces,
)

api_router = APIRouter()

api_router.include_router(routes_health.router)
api_router.include_router(routes_auth.router)
api_router.include_router(routes_users.router)
api_router.include_router(routes_problems.router)
api_router.include_router(routes_submissions.router)
api_router.include_router(routes_stats.router)
api_router.include_router(routes_execution.router)
api_router.include_router(routes_workspaces.router)
api_router.include_router(routes_assist.router)
api_router.include_router(routes_interviews.router)
api_router.include_router(routes_drills.router)
