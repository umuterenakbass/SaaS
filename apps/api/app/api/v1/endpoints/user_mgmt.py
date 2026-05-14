from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user_mgmt import UserCreateRequest, UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["user-management"])

_admin_or_manager = require_roles({UserRole.admin, UserRole.manager})


@router.get("", response_model=list[UserResponse])
def list_users(
    current_user: User = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> list[UserResponse]:
    if current_user.role not in {UserRole.admin, UserRole.manager}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    users = (
        db.query(User)
        .filter(User.site_id == current_user.site_id, User.deleted_at.is_(None))
        .order_by(User.created_at)
        .all()
    )
    return [UserResponse.model_validate(u) for u in users]


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreateRequest,
    current_user: User = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> UserResponse:
    if current_user.role not in {UserRole.admin, UserRole.manager}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    existing = db.query(User).filter(User.email == payload.email, User.deleted_at.is_(None)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    user = User(
        site_id=current_user.site_id,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdateRequest,
    current_user: User = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> UserResponse:
    if current_user.role not in {UserRole.admin, UserRole.manager}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    user = (
        db.query(User)
        .filter(User.id == user_id, User.site_id == current_user.site_id, User.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify admin user")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: str,
    current_user: User = Depends(require_tenant_context),
    db: Session = Depends(get_db),
) -> None:
    if current_user.role not in {UserRole.admin, UserRole.manager}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    user = (
        db.query(User)
        .filter(User.id == user_id, User.site_id == current_user.site_id, User.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot delete admin user")

    import datetime
    user.deleted_at = datetime.datetime.now(datetime.UTC)
    db.commit()
