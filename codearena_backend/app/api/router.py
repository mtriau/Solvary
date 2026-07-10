from fastapi import APIRouter

from app.api.v1 import routes_auth, routes_health, routes_users

api_router = APIRouter()

api_router.include_router(routes_health.router)
api_router.include_router(routes_auth.router)
api_router.include_router(routes_users.router)
