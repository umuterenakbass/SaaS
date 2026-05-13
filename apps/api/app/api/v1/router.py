from fastapi import APIRouter

from app.api.v1.endpoints.analytics import router as analytics_router
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.blocks import router as blocks_router
from app.api.v1.endpoints.charges import router as charges_router
from app.api.v1.endpoints.charge_plans import router as charge_plans_router
from app.api.v1.endpoints.flats import router as flats_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.installments import router as installments_router
from app.api.v1.endpoints.ledger import router as ledger_router
from app.api.v1.endpoints.notifications import router as notifications_router
from app.api.v1.endpoints.payment_allocations import router as payment_allocations_router
from app.api.v1.endpoints.payments import router as payments_router
from app.api.v1.endpoints.reports import router as reports_router
from app.api.v1.endpoints.resident_portal import router as resident_portal_router
from app.api.v1.endpoints.resident_relations import router as resident_relations_router
from app.api.v1.endpoints.scheduled_charges import router as scheduled_charges_router
from app.api.v1.endpoints.tenant import router as tenant_router
from app.api.v1.endpoints.user_mgmt import router as user_mgmt_router

api_router_v1 = APIRouter()
api_router_v1.include_router(health_router, tags=["health"])
api_router_v1.include_router(analytics_router)
api_router_v1.include_router(auth_router)
api_router_v1.include_router(tenant_router)
api_router_v1.include_router(blocks_router)
api_router_v1.include_router(charge_plans_router)
api_router_v1.include_router(flats_router)
api_router_v1.include_router(charges_router)
api_router_v1.include_router(installments_router)
api_router_v1.include_router(payments_router)
api_router_v1.include_router(payment_allocations_router)
api_router_v1.include_router(ledger_router)
api_router_v1.include_router(notifications_router)
api_router_v1.include_router(reports_router)
api_router_v1.include_router(resident_portal_router)
api_router_v1.include_router(resident_relations_router)
api_router_v1.include_router(scheduled_charges_router)
api_router_v1.include_router(user_mgmt_router)
