from fastapi import APIRouter

from app.api.v1 import (
    routes_auth,
    routes_execution,
    routes_health,
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
