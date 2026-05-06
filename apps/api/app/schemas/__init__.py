from app.schemas.auth import CurrentUserResponse, LoginResponse, RegisterRequest
from app.schemas.block import BlockCreateRequest, BlockResponse, BlockUpdateRequest
from app.schemas.flat import FlatCreateRequest, FlatResponse, FlatUpdateRequest
from app.schemas.resident_flat_relation import (
	ResidentRelationCreateRequest,
	ResidentRelationResponse,
	ResidentRelationUpdateRequest,
)

__all__ = [
	"BlockCreateRequest",
	"BlockResponse",
	"BlockUpdateRequest",
	"CurrentUserResponse",
	"FlatCreateRequest",
	"FlatResponse",
	"FlatUpdateRequest",
	"LoginResponse",
	"ResidentRelationCreateRequest",
	"ResidentRelationResponse",
	"ResidentRelationUpdateRequest",
	"RegisterRequest",
]
