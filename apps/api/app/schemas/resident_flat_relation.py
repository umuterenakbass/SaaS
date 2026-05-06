from datetime import date

from pydantic import BaseModel, model_validator

from app.models.resident_flat_relation import ResidentRelationType


class ResidentRelationCreateRequest(BaseModel):
    user_id: str
    flat_id: str
    relation_type: ResidentRelationType
    start_date: date
    end_date: date | None = None
    is_primary: bool = False

    @model_validator(mode="after")
    def validate_date_range(self) -> "ResidentRelationCreateRequest":
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        return self


class ResidentRelationUpdateRequest(BaseModel):
    relation_type: ResidentRelationType | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_primary: bool | None = None


class ResidentRelationResponse(BaseModel):
    id: str
    site_id: str
    user_id: str
    flat_id: str
    relation_type: ResidentRelationType
    start_date: date
    end_date: date | None
    is_primary: bool
