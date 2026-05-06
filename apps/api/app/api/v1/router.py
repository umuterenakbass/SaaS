from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.blocks import router as blocks_router
from app.api.v1.endpoints.flats import router as flats_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.resident_relations import router as resident_relations_router
from app.api.v1.endpoints.tenant import router as tenant_router

api_router_v1 = APIRouter()
api_router_v1.include_router(health_router, tags=["health"])
api_router_v1.include_router(auth_router)
api_router_v1.include_router(tenant_router)
api_router_v1.include_router(blocks_router)
api_router_v1.include_router(flats_router)
api_router_v1.include_router(resident_relations_router)
