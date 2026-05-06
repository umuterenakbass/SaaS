from pydantic import BaseModel, Field

from app.models.flat import FlatStatus


class FlatCreateRequest(BaseModel):
    block_id: str
    unit_no: str = Field(min_length=1, max_length=50)
    floor: int = 0
    status: FlatStatus = FlatStatus.active


class FlatUpdateRequest(BaseModel):
    unit_no: str | None = Field(default=None, min_length=1, max_length=50)
    floor: int | None = None
    status: FlatStatus | None = None


class FlatResponse(BaseModel):
    id: str
    site_id: str
    block_id: str
    unit_no: str
    floor: int
    status: FlatStatus
