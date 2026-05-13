from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.flat import Flat
from app.models.maintenance_request import MaintenanceRequest, MaintenanceStatus
from app.models.resident_flat_relation import ResidentFlatRelation
from app.models.user import User, UserRole
from app.schemas.maintenance_request import (
    MaintenanceRequestCreate,
    MaintenanceRequestResponse,
    MaintenanceRequestUpdate,
)

router = APIRouter(prefix="/maintenance-requests", tags=["maintenance-requests"])

_ADMIN_ROLES = require_roles({UserRole.admin, UserRole.manager})
_RESIDENT_ONLY = require_roles({UserRole.resident})


def _to_response(req: MaintenanceRequest, db: Session) -> MaintenanceRequestResponse:
    flat_unit_no = None
    flat_block_name = None
    reporter_name = None

    if req.flat_id:
        flat = db.query(Flat).filter(Flat.id == req.flat_id).first()
        if flat:
            flat_unit_no = flat.unit_no
            if flat.block:
                flat_block_name = flat.block.name

    if req.reported_by:
        reporter = db.query(User).filter(User.id == req.reported_by).first()
        if reporter:
            reporter_name = reporter.full_name or reporter.email

    return MaintenanceRequestResponse(
        id=req.id,
        site_id=req.site_id,
        flat_id=req.flat_id,
        reported_by=req.reported_by,
        assigned_to=req.assigned_to,
        category=req.category,
        status=req.status,
        title=req.title,
        description=req.description,
        admin_note=req.admin_note,
        created_at=req.created_at.isoformat(),
        flat_unit_no=flat_unit_no,
        flat_block_name=flat_block_name,
        reporter_name=reporter_name,
    )


# ---------------------------------------------------------------------------
# Resident: Talep oluştur
# ---------------------------------------------------------------------------

@router.post("", response_model=MaintenanceRequestResponse, status_code=status.HTTP_201_CREATED)
def create_request(
    payload: MaintenanceRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> MaintenanceRequestResponse:
    """Hem resident hem admin/manager talep açabilir."""
    # flat_id verilmişse site'ye ait olduğunu doğrula
    if payload.flat_id:
        flat = db.query(Flat).filter(
            Flat.id == payload.flat_id,
            Flat.site_id == current_user.site_id,
            Flat.deleted_at.is_(None),
        ).first()
        if not flat:
            raise HTTPException(status_code=404, detail="Daire bulunamadı.")

    req = MaintenanceRequest(
        site_id=current_user.site_id,
        flat_id=payload.flat_id,
        reported_by=current_user.id,
        category=payload.category,
        title=payload.title,
        description=payload.description,
    )
    db.add(req)
    db.commit()
    db.refresh(req)
    return _to_response(req, db)


# ---------------------------------------------------------------------------
# Resident: Kendi taleplerini listele
# ---------------------------------------------------------------------------

@router.get("/my", response_model=list[MaintenanceRequestResponse])
def my_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> list[MaintenanceRequestResponse]:
    """Giriş yapan kullanıcının kendi açtığı talepleri — tüm roller erişebilir."""
    items = (
        db.query(MaintenanceRequest)
        .filter(
            MaintenanceRequest.site_id == current_user.site_id,
            MaintenanceRequest.reported_by == current_user.id,
            MaintenanceRequest.deleted_at.is_(None),
        )
        .order_by(MaintenanceRequest.created_at.desc())
        .all()
    )
    return [_to_response(r, db) for r in items]


# ---------------------------------------------------------------------------
# Admin: Tüm talepleri listele
# ---------------------------------------------------------------------------

@router.get("", response_model=list[MaintenanceRequestResponse])
def list_requests(
    status_filter: MaintenanceStatus | None = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_ADMIN_ROLES),
) -> list[MaintenanceRequestResponse]:
    query = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.site_id == current_user.site_id,
        MaintenanceRequest.deleted_at.is_(None),
    )
    if status_filter:
        query = query.filter(MaintenanceRequest.status == status_filter)
    items = query.order_by(MaintenanceRequest.created_at.desc()).all()
    return [_to_response(r, db) for r in items]


# ---------------------------------------------------------------------------
# Admin: Durum / not güncelle
# ---------------------------------------------------------------------------

@router.patch("/{request_id}", response_model=MaintenanceRequestResponse)
def update_request(
    request_id: str,
    payload: MaintenanceRequestUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_ADMIN_ROLES),
) -> MaintenanceRequestResponse:
    req = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.id == request_id,
        MaintenanceRequest.site_id == current_user.site_id,
        MaintenanceRequest.deleted_at.is_(None),
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Talep bulunamadı.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    return _to_response(req, db)


# ---------------------------------------------------------------------------
# Admin: Sil
# ---------------------------------------------------------------------------

@router.delete("/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_request(
    request_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_ADMIN_ROLES),
) -> None:
    req = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.id == request_id,
        MaintenanceRequest.site_id == current_user.site_id,
        MaintenanceRequest.deleted_at.is_(None),
    ).first()
    if not req:
        raise HTTPException(status_code=404, detail="Talep bulunamadı.")
    from datetime import UTC, datetime
    req.deleted_at = datetime.now(UTC)
    db.commit()
