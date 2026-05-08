from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.charge import Charge
from app.models.charge_plan import ChargePlan, ChargePlanAssignment
from app.models.flat import Flat
from app.models.user import User, UserRole
from app.schemas.charge_plan import (
    ChargePlanAssignmentCreateRequest,
    ChargePlanAssignmentResponse,
    ChargePlanCreateRequest,
    ChargePlanGenerateRequest,
    ChargePlanGenerateResponse,
    ChargePlanResponse,
    ChargePlanUpdateRequest,
)

router = APIRouter(prefix="/charge-plans", tags=["charge-plans"])


@router.get("", response_model=list[ChargePlanResponse])
def list_charge_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    is_active: bool | None = Query(default=None),
) -> list[ChargePlanResponse]:
    query = db.query(ChargePlan).filter(
        ChargePlan.site_id == current_user.site_id,
        ChargePlan.deleted_at.is_(None),
    )
    if is_active is not None:
        query = query.filter(ChargePlan.is_active == is_active)

    items = query.order_by(ChargePlan.created_at.desc()).all()
    return [ChargePlanResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("", response_model=ChargePlanResponse, status_code=status.HTTP_201_CREATED)
def create_charge_plan(
    payload: ChargePlanCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> ChargePlanResponse:
    plan = ChargePlan(
        site_id=current_user.site_id,
        name=payload.name.strip(),
        charge_type=payload.charge_type.strip(),
        amount=payload.amount,
        frequency=payload.frequency,
        start_period=payload.start_period,
        end_period=payload.end_period,
        is_active=payload.is_active,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return ChargePlanResponse.model_validate(plan, from_attributes=True)


@router.get("/{plan_id}", response_model=ChargePlanResponse)
def get_charge_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> ChargePlanResponse:
    plan = (
        db.query(ChargePlan)
        .filter(
            ChargePlan.id == plan_id,
            ChargePlan.site_id == current_user.site_id,
            ChargePlan.deleted_at.is_(None),
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge plan not found")

    return ChargePlanResponse.model_validate(plan, from_attributes=True)


@router.patch("/{plan_id}", response_model=ChargePlanResponse)
def update_charge_plan(
    plan_id: str,
    payload: ChargePlanUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> ChargePlanResponse:
    plan = (
        db.query(ChargePlan)
        .filter(
            ChargePlan.id == plan_id,
            ChargePlan.site_id == current_user.site_id,
            ChargePlan.deleted_at.is_(None),
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge plan not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if isinstance(value, str):
            value = value.strip()
        setattr(plan, key, value)

    db.commit()
    db.refresh(plan)
    return ChargePlanResponse.model_validate(plan, from_attributes=True)


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_charge_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> None:
    plan = (
        db.query(ChargePlan)
        .filter(
            ChargePlan.id == plan_id,
            ChargePlan.site_id == current_user.site_id,
            ChargePlan.deleted_at.is_(None),
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge plan not found")

    plan.deleted_at = datetime.now(UTC)
    db.commit()


@router.get("/{plan_id}/assignments", response_model=list[ChargePlanAssignmentResponse])
def list_charge_plan_assignments(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> list[ChargePlanAssignmentResponse]:
    plan = (
        db.query(ChargePlan)
        .filter(
            ChargePlan.id == plan_id,
            ChargePlan.site_id == current_user.site_id,
            ChargePlan.deleted_at.is_(None),
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge plan not found")

    items = (
        db.query(ChargePlanAssignment)
        .filter(
            ChargePlanAssignment.charge_plan_id == plan_id,
            ChargePlanAssignment.site_id == current_user.site_id,
            ChargePlanAssignment.deleted_at.is_(None),
        )
        .order_by(ChargePlanAssignment.created_at.desc())
        .all()
    )
    return [ChargePlanAssignmentResponse.model_validate(item, from_attributes=True) for item in items]


@router.post("/{plan_id}/assignments", response_model=ChargePlanAssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_charge_plan_assignment(
    plan_id: str,
    payload: ChargePlanAssignmentCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> ChargePlanAssignmentResponse:
    plan = (
        db.query(ChargePlan)
        .filter(
            ChargePlan.id == plan_id,
            ChargePlan.site_id == current_user.site_id,
            ChargePlan.deleted_at.is_(None),
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge plan not found")

    flat = (
        db.query(Flat)
        .filter(
            Flat.id == payload.flat_id,
            Flat.site_id == current_user.site_id,
            Flat.deleted_at.is_(None),
        )
        .first()
    )
    if not flat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flat not found")

    item = ChargePlanAssignment(
        site_id=current_user.site_id,
        charge_plan_id=plan_id,
        flat_id=payload.flat_id,
    )
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Flat is already assigned to this plan",
        ) from None

    db.refresh(item)
    return ChargePlanAssignmentResponse.model_validate(item, from_attributes=True)


@router.post("/{plan_id}/generate", response_model=ChargePlanGenerateResponse)
def generate_charges_for_plan(
    plan_id: str,
    payload: ChargePlanGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> ChargePlanGenerateResponse:
    plan = (
        db.query(ChargePlan)
        .filter(
            ChargePlan.id == plan_id,
            ChargePlan.site_id == current_user.site_id,
            ChargePlan.deleted_at.is_(None),
        )
        .first()
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Charge plan not found")
    if not plan.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Charge plan is inactive")

    if payload.period < plan.start_period:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Period is before plan start_period")
    if plan.end_period and payload.period > plan.end_period:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Period is after plan end_period")

    assignments = (
        db.query(ChargePlanAssignment)
        .filter(
            ChargePlanAssignment.charge_plan_id == plan_id,
            ChargePlanAssignment.site_id == current_user.site_id,
            ChargePlanAssignment.deleted_at.is_(None),
        )
        .all()
    )

    created_charge_ids: list[str] = []
    skipped_count = 0
    for assignment in assignments:
        existing = (
            db.query(Charge)
            .filter(
                Charge.site_id == current_user.site_id,
                Charge.flat_id == assignment.flat_id,
                Charge.period == payload.period,
                Charge.charge_type == plan.charge_type,
                Charge.deleted_at.is_(None),
            )
            .first()
        )
        if existing:
            skipped_count += 1
            continue

        charge = Charge(
            site_id=current_user.site_id,
            flat_id=assignment.flat_id,
            charge_type=plan.charge_type,
            period=payload.period,
            amount=plan.amount,
            due_date=payload.due_date,
            status=payload.status,
        )
        db.add(charge)
        db.flush()
        created_charge_ids.append(charge.id)

    db.commit()

    return ChargePlanGenerateResponse(
        charge_plan_id=plan_id,
        period=payload.period,
        requested_assignments=len(assignments),
        created_count=len(created_charge_ids),
        skipped_count=skipped_count,
        created_charge_ids=created_charge_ids,
    )


@router.delete("/{plan_id}/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_charge_plan_assignment(
    plan_id: str,
    assignment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager, UserRole.accountant})),
) -> None:
    item = (
        db.query(ChargePlanAssignment)
        .filter(
            ChargePlanAssignment.id == assignment_id,
            ChargePlanAssignment.charge_plan_id == plan_id,
            ChargePlanAssignment.site_id == current_user.site_id,
            ChargePlanAssignment.deleted_at.is_(None),
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    item.deleted_at = datetime.now(UTC)
    db.commit()
