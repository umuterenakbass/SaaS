from __future__ import annotations

from pydantic import BaseModel


class AnnouncementCreate(BaseModel):
    title: str
    body: str
    block_id: str | None = None
    is_pinned: bool = False
    is_published: bool = True


class AnnouncementUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    block_id: str | None = None
    is_pinned: bool | None = None
    is_published: bool | None = None


class AnnouncementResponse(BaseModel):
    id: str
    site_id: str
    created_by: str | None
    title: str
    body: str
    block_id: str | None
    is_pinned: bool
    is_published: bool
    created_at: str

    model_config = {"from_attributes": True}
