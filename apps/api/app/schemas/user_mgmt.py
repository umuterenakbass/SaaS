from __future__ import annotations

from pydantic import BaseModel, EmailStr, field_validator

from app.models.user import UserRole


class UserCreateRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: UserRole

    @field_validator("role")
    @classmethod
    def role_not_admin(cls, v: UserRole) -> UserRole:
        if v == UserRole.admin:
            raise ValueError("Cannot create another admin via this endpoint")
        return v


class UserUpdateRequest(BaseModel):
    full_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator("role")
    @classmethod
    def role_not_admin(cls, v: UserRole | None) -> UserRole | None:
        if v == UserRole.admin:
            raise ValueError("Cannot assign admin role via this endpoint")
        return v


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    site_id: str

    model_config = {"from_attributes": True}
