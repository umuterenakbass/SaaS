from pydantic import BaseModel, Field


class BlockCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    code: str = Field(min_length=1, max_length=50)


class BlockUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)


class BlockResponse(BaseModel):
    id: str
    site_id: str
    name: str
    code: str
