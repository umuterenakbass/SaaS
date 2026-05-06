from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.flat import Flat
from app.models.resident_flat_relation import ResidentFlatRelation
from app.models.user import User, UserRole
from app.schemas.resident_flat_relation import (
    ResidentRelationCreateRequest,
    ResidentRelationResponse,
    ResidentRelationUpdateRequest,
)

router = APIRouter(prefix="/resident-relations", tags=["resident-relations"])


def _end_or_max(value: date | None) -> date:
    return value or date.max


def _is_overlap(
    start_a: date,
    end_a: date | None,
    start_b: date,
    end_b: date | None,
) -> bool:
    return start_a <= _end_or_max(end_b) and start_b <= _end_or_max(end_a)


def _assert_relation_integrity(
    db: Session,
    current_site_id: str,
    user_id: str,
    flat_id: str,
) -> tuple[User, Flat]:
    user = (
        db.query(User)
        .filter(
            User.id == user_id,
            User.site_id == current_site_id,
            User.deleted_at.is_(None),
        )
        .first()
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    flat = (
        db.query(Flat)
        .filter(
            Flat.id == flat_id,
            Flat.site_id == current_site_id,
            Flat.deleted_at.is_(None),
        )
        .first()
    )
    if not flat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found")

    return user, flat


def _assert_no_overlap(
    db: Session,
    site_id: str,
    flat_id: str,
    start_date: date,
    end_date: date | None,
    exclude_relation_id: str | None = None,
) -> None:
    query = db.query(ResidentFlatRelation).filter(
        ResidentFlatRelation.site_id == site_id,
        ResidentFlatRelation.flat_id == flat_id,
        ResidentFlatRelation.deleted_at.is_(None),
    )

    if exclude_relation_id:
        query = query.filter(ResidentFlatRelation.id != exclude_relation_id)

    existing_relations = query.all()
    for relation in existing_relations:
        if _is_overlap(start_date, end_date, relation.start_date, relation.end_date):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Date range overlaps with an existing relation",
            )


@router.get("", response_model=list[ResidentRelationResponse])
def list_relations(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    flat_id: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
) -> list[ResidentRelationResponse]:
    query = db.query(ResidentFlatRelation).filter(
        ResidentFlatRelation.site_id == current_user.site_id,
        ResidentFlatRelation.deleted_at.is_(None),
    )

    if flat_id:
        query = query.filter(ResidentFlatRelation.flat_id == flat_id)
    if user_id:
        query = query.filter(ResidentFlatRelation.user_id == user_id)

    items = query.order_by(ResidentFlatRelation.created_at.desc()).all()
    return [ResidentRelationResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("", response_model=ResidentRelationResponse, status_code=status.HTTP_201_CREATED)
def create_relation(
    payload: ResidentRelationCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> ResidentRelationResponse:
    _assert_relation_integrity(
        db=db,
        current_site_id=current_user.site_id,
        user_id=payload.user_id,
        flat_id=payload.flat_id,
    )
    _assert_no_overlap(
        db=db,
        site_id=current_user.site_id,
        flat_id=payload.flat_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    relation = ResidentFlatRelation(
        site_id=current_user.site_id,
        user_id=payload.user_id,
        flat_id=payload.flat_id,
        relation_type=payload.relation_type,
        start_date=payload.start_date,
        end_date=payload.end_date,
        is_primary=payload.is_primary,
    )
    db.add(relation)
    db.commit()
    db.refresh(relation)
    return ResidentRelationResponse.model_validate(relation, from_attributes=True)


@router.get("/{relation_id}", response_model=ResidentRelationResponse)
def get_relation(
    relation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> ResidentRelationResponse:
    relation = (
        db.query(ResidentFlatRelation)
        .filter(
            ResidentFlatRelation.id == relation_id,
            ResidentFlatRelation.site_id == current_user.site_id,
            ResidentFlatRelation.deleted_at.is_(None),
        )
        .first()
    )
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")

    return ResidentRelationResponse.model_validate(relation, from_attributes=True)


@router.patch("/{relation_id}", response_model=ResidentRelationResponse)
def update_relation(
    relation_id: str,
    payload: ResidentRelationUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> ResidentRelationResponse:
    relation = (
        db.query(ResidentFlatRelation)
        .filter(
            ResidentFlatRelation.id == relation_id,
            ResidentFlatRelation.site_id == current_user.site_id,
            ResidentFlatRelation.deleted_at.is_(None),
        )
        .first()
    )
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")

    updates = payload.model_dump(exclude_unset=True)

    new_start = updates.get("start_date", relation.start_date)
    new_end = updates.get("end_date", relation.end_date)
    if new_end and new_end < new_start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid date range")

    _assert_no_overlap(
        db=db,
        site_id=current_user.site_id,
        flat_id=relation.flat_id,
        start_date=new_start,
        end_date=new_end,
        exclude_relation_id=relation_id,
    )

    for key, value in updates.items():
        setattr(relation, key, value)

    db.commit()
    db.refresh(relation)
    return ResidentRelationResponse.model_validate(relation, from_attributes=True)


@router.delete("/{relation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_relation(
    relation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> None:
    relation = (
        db.query(ResidentFlatRelation)
        .filter(
            ResidentFlatRelation.id == relation_id,
            ResidentFlatRelation.site_id == current_user.site_id,
            ResidentFlatRelation.deleted_at.is_(None),
        )
        .first()
    )
    if not relation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relation not found")

    relation.deleted_at = datetime.now(UTC)
    db.commit()
