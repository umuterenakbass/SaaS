from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.session import get_db
from app.models.site import Site
from app.models.user import User, UserRole
from app.schemas.auth import CurrentUserResponse, LoginResponse, RegisterRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=CurrentUserResponse, status_code=status.HTTP_201_CREATED)
def register_admin(payload: RegisterRequest, db: Session = Depends(get_db)) -> CurrentUserResponse:
    existing = db.query(User).filter(User.email == payload.email, User.deleted_at.is_(None)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

    site = Site(name=payload.site_name.strip())
    admin_user = User(
        site_id=site.id,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=UserRole.admin,
        is_active=True,
    )

    db.add(site)
    db.flush()
    admin_user.site_id = site.id
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    return CurrentUserResponse.model_validate(admin_user, from_attributes=True)


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> LoginResponse:
    user = (
        db.query(User)
        .filter(User.email == form_data.username, User.deleted_at.is_(None))
        .first()
    )
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(subject=user.id, site_id=user.site_id, role=user.role.value)
    return LoginResponse(access_token=token)


@router.get("/me", response_model=CurrentUserResponse)
def me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse.model_validate(current_user, from_attributes=True)
