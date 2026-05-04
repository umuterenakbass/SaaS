from fastapi import APIRouter, Depends

from app.core.deps import require_roles, require_tenant_context
from app.models.user import User, UserRole

router = APIRouter(prefix="/tenant", tags=["tenant"])


@router.get("/context")
def tenant_context(
    current_user: User = Depends(require_tenant_context),
) -> dict[str, str]:
    return {
        "site_id": current_user.site_id,
        "user_id": current_user.id,
        "role": current_user.role.value,
    }


@router.get("/admin-area")
def admin_area(
    current_user: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> dict[str, str]:
    return {
        "message": "Authorized tenant admin area",
        "user_id": current_user.id,
        "role": current_user.role.value,
    }
