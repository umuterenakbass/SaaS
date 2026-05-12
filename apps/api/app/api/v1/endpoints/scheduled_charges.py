from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.charge import Charge
from app.models.flat import Flat
from app.models.scheduled_charge import ScheduledCharge
from app.models.user import User, UserRole
from app.schemas.bulk import (
    ScheduledChargeCreateRequest,
    ScheduledChargeResponse,
    ScheduledChargeRunResult,
    ScheduledChargeUpdateRequest,
)

router = APIRouter(prefix="/scheduled-charges", tags=["scheduled-charges"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(sc: ScheduledCharge) -> ScheduledChargeResponse:
    return ScheduledChargeResponse(
        id=sc.id,
        site_id=sc.site_id,
        charge_type=sc.charge_type,
        amount=sc.amount,
        day_of_month=sc.day_of_month,
        active=sc.active,
        created_at=sc.created_at.isoformat(),
        updated_at=sc.updated_at.isoformat(),
    )


def _run_scheduled(
    sc: ScheduledCharge, db: Session, site_id: str, period: str
) -> ScheduledChargeRunResult:
    """Verilen kural için ``period`` dönemi borcunu tüm aktif dairelere üretir."""
    year, month = int(period[:4]), int(period[5:7])
    due = date(year, month, min(sc.day_of_month, 28))

    flats = (
        db.query(Flat)
        .filter(
            Flat.site_id == site_id,
            Flat.deleted_at.is_(None),
            Flat.status == "active",
        )
        .all()
    )

    created = skipped = 0
    errors: list[str] = []

    for flat in flats:
        existing = (
            db.query(Charge)
            .filter(
                Charge.flat_id == flat.id,
                Charge.period == period,
                Charge.charge_type == sc.charge_type,
                Charge.deleted_at.is_(None),
            )
            .first()
        )
        if existing:
            skipped += 1
            continue

        charge = Charge(
            site_id=site_id,
            flat_id=flat.id,
            charge_type=sc.charge_type,
            period=period,
            amount=sc.amount,
            due_date=due,
        )
        db.add(charge)
        try:
            db.flush()
            created += 1
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            errors.append(f"flat_id={flat.id}: {exc}")

    db.commit()
    return ScheduledChargeRunResult(
        period=period, created=created, skipped=skipped, errors=errors
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=list[ScheduledChargeResponse])
def list_scheduled_charges(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> list[ScheduledChargeResponse]:
    rows = (
        db.query(ScheduledCharge)
        .filter(
            ScheduledCharge.site_id == current_user.site_id,
            ScheduledCharge.deleted_at.is_(None),
        )
        .order_by(ScheduledCharge.created_at.desc())
        .all()
    )
    return [_to_response(r) for r in rows]


@router.post("", response_model=ScheduledChargeResponse, status_code=status.HTTP_201_CREATED)
def create_scheduled_charge(
    payload: ScheduledChargeCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> ScheduledChargeResponse:
    sc = ScheduledCharge(
        site_id=current_user.site_id,
        charge_type=payload.charge_type.strip(),
        amount=payload.amount,
        day_of_month=payload.day_of_month,
        active=payload.active,
    )
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return _to_response(sc)


@router.get("/{sc_id}", response_model=ScheduledChargeResponse)
def get_scheduled_charge(
    sc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> ScheduledChargeResponse:
    sc = (
        db.query(ScheduledCharge)
        .filter(
            ScheduledCharge.id == sc_id,
            ScheduledCharge.site_id == current_user.site_id,
            ScheduledCharge.deleted_at.is_(None),
        )
        .first()
    )
    if not sc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled charge not found")
    return _to_response(sc)


@router.patch("/{sc_id}", response_model=ScheduledChargeResponse)
def update_scheduled_charge(
    sc_id: str,
    payload: ScheduledChargeUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> ScheduledChargeResponse:
    sc = (
        db.query(ScheduledCharge)
        .filter(
            ScheduledCharge.id == sc_id,
            ScheduledCharge.site_id == current_user.site_id,
            ScheduledCharge.deleted_at.is_(None),
        )
        .first()
    )
    if not sc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled charge not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(sc, key, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(sc)
    return _to_response(sc)


@router.delete("/{sc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheduled_charge(
    sc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> None:
    sc = (
        db.query(ScheduledCharge)
        .filter(
            ScheduledCharge.id == sc_id,
            ScheduledCharge.site_id == current_user.site_id,
            ScheduledCharge.deleted_at.is_(None),
        )
        .first()
    )
    if not sc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled charge not found")

    sc.deleted_at = datetime.now(UTC)
    db.commit()


# ---------------------------------------------------------------------------
# Run (manuel tetikle)
# ---------------------------------------------------------------------------

@router.post("/{sc_id}/run", response_model=ScheduledChargeRunResult)
def run_scheduled_charge(
    sc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> ScheduledChargeRunResult:
    """Bu kuralı şu anki ay için çalıştır."""
    sc = (
        db.query(ScheduledCharge)
        .filter(
            ScheduledCharge.id == sc_id,
            ScheduledCharge.site_id == current_user.site_id,
            ScheduledCharge.deleted_at.is_(None),
        )
        .first()
    )
    if not sc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scheduled charge not found")

    now = datetime.now(UTC)
    period = f"{now.year:04d}-{now.month:02d}"
    return _run_scheduled(sc, db, current_user.site_id, period)


@router.post("/run-all", response_model=list[ScheduledChargeRunResult])
def run_all_scheduled_charges(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> list[ScheduledChargeRunResult]:
    """Bu sitenin tüm aktif zamanlanmış kurallarını şu anki ay için çalıştır."""
    active_rules = (
        db.query(ScheduledCharge)
        .filter(
            ScheduledCharge.site_id == current_user.site_id,
            ScheduledCharge.active.is_(True),
            ScheduledCharge.deleted_at.is_(None),
        )
        .all()
    )
    now = datetime.now(UTC)
    period = f"{now.year:04d}-{now.month:02d}"
    return [_run_scheduled(sc, db, current_user.site_id, period) for sc in active_rules]
