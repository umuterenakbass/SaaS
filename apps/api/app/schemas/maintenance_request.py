from __future__ import annotations

from app.models.maintenance_request import MaintenanceCategory, MaintenanceStatus
from pydantic import BaseModel


class MaintenanceRequestCreate(BaseModel):
    title: str
    description: str
    category: MaintenanceCategory = MaintenanceCategory.other
    flat_id: str | None = None


class MaintenanceRequestUpdate(BaseModel):
    status: MaintenanceStatus | None = None
    admin_note: str | None = None
    assigned_to: str | None = None
    category: MaintenanceCategory | None = None


class MaintenanceRequestResponse(BaseModel):
    id: str
    site_id: str
    flat_id: str | None
    reported_by: str | None
    assigned_to: str | None
    category: MaintenanceCategory
    status: MaintenanceStatus
    title: str
    description: str
    admin_note: str | None
    created_at: str
    # Türetilen alanlar
    flat_unit_no: str | None = None
    flat_block_name: str | None = None
    reporter_name: str | None = None

    model_config = {"from_attributes": True}
