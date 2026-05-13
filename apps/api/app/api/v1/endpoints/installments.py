from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.installment_plan import InstallmentItem, InstallmentPlan, InstallmentStatus
from app.models.user import User, UserRole
from app.schemas.installment import (
    InstallmentItemPayOut,
    InstallmentPlanCreate,
    InstallmentPlanOut,
    InstallmentItemOut,
)

router = APIRouter(prefix="/installments", tags=["installments"])

_MANAGER = require_roles({UserRole.admin, UserRole.manager})


def _plan_to_out(plan: InstallmentPlan) -> InstallmentPlanOut:
    return InstallmentPlanOut(
        id=plan.id,
        site_id=plan.site_id,
        flat_id=plan.flat_id,
        charge_id=plan.charge_id,
        title=plan.title,
        total_amount=plan.total_amount,
        installment_count=plan.installment_count,
        is_active=plan.is_active,
        items=[
            InstallmentItemOut(
                id=i.id,
                installment_no=i.installment_no,
                amount=i.amount,
                due_date=i.due_date.isoformat(),
                status=i.status,
                paid_at=i.paid_at.isoformat() if i.paid_at else None,
            )
            for i in sorted(plan.items, key=lambda x: x.installment_no)
        ],
    )


# ── LIST ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=list[InstallmentPlanOut])
def list_installment_plans(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MANAGER),
) -> list[InstallmentPlanOut]:
    plans = (
        db.query(InstallmentPlan)
        .filter(
            InstallmentPlan.site_id == current_user.site_id,
            InstallmentPlan.deleted_at.is_(None),
        )
        .order_by(InstallmentPlan.created_at.desc())
        .all()
    )
    return [_plan_to_out(p) for p in plans]


# ── CREATE ────────────────────────────────────────────────────────────────────

@router.post("", response_model=InstallmentPlanOut, status_code=status.HTTP_201_CREATED)
def create_installment_plan(
    payload: InstallmentPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MANAGER),
) -> InstallmentPlanOut:
    import uuid

    plan = InstallmentPlan(
        id=str(uuid.uuid4()),
        site_id=current_user.site_id,
        flat_id=payload.flat_id,
        charge_id=payload.charge_id,
        title=payload.title,
        total_amount=payload.total_amount,
        installment_count=payload.installment_count,
        is_active=True,
    )
    db.add(plan)
    db.flush()  # plan.id hazır olsun

    # Taksit tutarlarını hesapla (son taksit kalan tutar)
    base = (payload.total_amount / payload.installment_count).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    total_assigned = base * (payload.installment_count - 1)
    last_amount = payload.total_amount - total_assigned

    for i in range(payload.installment_count):
        due = date(
            payload.first_due_date.year + (payload.first_due_date.month + i - 1) // 12,
            (payload.first_due_date.month + i - 1) % 12 + 1,
            payload.first_due_date.day,
        )
        amount = last_amount if i == payload.installment_count - 1 else base
        item = InstallmentItem(
            id=str(uuid.uuid4()),
            site_id=current_user.site_id,
            plan_id=plan.id,
            installment_no=i + 1,
            amount=amount,
            due_date=due,
            status=InstallmentStatus.pending,
        )
        db.add(item)

    db.commit()
    db.refresh(plan)
    return _plan_to_out(plan)


# ── GET ONE ───────────────────────────────────────────────────────────────────

@router.get("/{plan_id}", response_model=InstallmentPlanOut)
def get_installment_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MANAGER),
) -> InstallmentPlanOut:
    plan = db.query(InstallmentPlan).filter(
        InstallmentPlan.id == plan_id,
        InstallmentPlan.site_id == current_user.site_id,
        InstallmentPlan.deleted_at.is_(None),
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan bulunamadı.")
    return _plan_to_out(plan)


# ── PAY ITEM ─────────────────────────────────────────────────────────────────

@router.patch("/{plan_id}/items/{item_id}/pay", response_model=InstallmentItemPayOut)
def pay_installment_item(
    plan_id: str,
    item_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MANAGER),
) -> InstallmentItemPayOut:
    item = (
        db.query(InstallmentItem)
        .join(InstallmentPlan)
        .filter(
            InstallmentItem.id == item_id,
            InstallmentItem.plan_id == plan_id,
            InstallmentPlan.site_id == current_user.site_id,
            InstallmentItem.deleted_at.is_(None),
        )
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Taksit kalemi bulunamadı.")
    if item.status == InstallmentStatus.paid:
        raise HTTPException(status_code=409, detail="Bu taksit zaten ödendi.")

    today = date.today()
    item.status = InstallmentStatus.paid
    item.paid_at = today
    db.commit()
    db.refresh(item)

    return InstallmentItemPayOut(
        id=item.id,
        installment_no=item.installment_no,
        amount=item.amount,
        due_date=item.due_date.isoformat(),
        status=item.status,
        paid_at=item.paid_at.isoformat(),
    )


# ── DELETE (soft) ─────────────────────────────────────────────────────────────

@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_installment_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_MANAGER),
) -> None:
    from datetime import datetime, UTC
    plan = db.query(InstallmentPlan).filter(
        InstallmentPlan.id == plan_id,
        InstallmentPlan.site_id == current_user.site_id,
        InstallmentPlan.deleted_at.is_(None),
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan bulunamadı.")
    plan.deleted_at = datetime.now(UTC)
    db.commit()
