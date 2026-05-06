from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.block import Block
from app.models.flat import Flat
from app.models.user import User, UserRole
from app.schemas.flat import FlatCreateRequest, FlatResponse, FlatUpdateRequest

router = APIRouter(prefix="/flats", tags=["flats"])


@router.get("", response_model=list[FlatResponse])
def list_flats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    block_id: str | None = Query(default=None),
) -> list[FlatResponse]:
    query = db.query(Flat).filter(Flat.site_id == current_user.site_id, Flat.deleted_at.is_(None))
    if block_id:
        query = query.filter(Flat.block_id == block_id)

    flats = query.order_by(Flat.created_at.desc()).all()
    return [FlatResponse.model_validate(item, from_attributes=True) for item in flats]


@router.post("", response_model=FlatResponse, status_code=status.HTTP_201_CREATED)
def create_flat(
    payload: FlatCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> FlatResponse:
    block = (
        db.query(Block)
        .filter(
            Block.id == payload.block_id,
            Block.site_id == current_user.site_id,
            Block.deleted_at.is_(None),
        )
        .first()
    )
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")

    duplicate = (
        db.query(Flat)
        .filter(
            Flat.block_id == payload.block_id,
            Flat.unit_no == payload.unit_no,
            Flat.deleted_at.is_(None),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Flat unit already exists")

    flat = Flat(
        site_id=current_user.site_id,
        block_id=payload.block_id,
        unit_no=payload.unit_no.strip(),
        floor=payload.floor,
        status=payload.status,
    )
    db.add(flat)
    db.commit()
    db.refresh(flat)

    return FlatResponse.model_validate(flat, from_attributes=True)


@router.get("/{flat_id}", response_model=FlatResponse)
def get_flat(
    flat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> FlatResponse:
    flat = (
        db.query(Flat)
        .filter(
            Flat.id == flat_id,
            Flat.site_id == current_user.site_id,
            Flat.deleted_at.is_(None),
        )
        .first()
    )
    if not flat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found")

    return FlatResponse.model_validate(flat, from_attributes=True)


@router.patch("/{flat_id}", response_model=FlatResponse)
def update_flat(
    flat_id: str,
    payload: FlatUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> FlatResponse:
    flat = (
        db.query(Flat)
        .filter(
            Flat.id == flat_id,
            Flat.site_id == current_user.site_id,
            Flat.deleted_at.is_(None),
        )
        .first()
    )
    if not flat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found")

    updates = payload.model_dump(exclude_unset=True)
    if "unit_no" in updates:
        duplicate = (
            db.query(Flat)
            .filter(
                Flat.block_id == flat.block_id,
                Flat.unit_no == updates["unit_no"],
                Flat.id != flat_id,
                Flat.deleted_at.is_(None),
            )
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Flat unit already exists",
            )

    for key, value in updates.items():
        setattr(flat, key, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(flat)
    return FlatResponse.model_validate(flat, from_attributes=True)


@router.delete("/{flat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flat(
    flat_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> None:
    flat = (
        db.query(Flat)
        .filter(
            Flat.id == flat_id,
            Flat.site_id == current_user.site_id,
            Flat.deleted_at.is_(None),
        )
        .first()
    )
    if not flat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found")

    flat.deleted_at = datetime.now(UTC)
    db.commit()
