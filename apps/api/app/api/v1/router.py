from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router

api_router_v1 = APIRouter()
api_router_v1.include_router(health_router, tags=["health"])
