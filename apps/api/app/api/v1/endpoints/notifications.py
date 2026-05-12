from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import require_tenant_context
from app.db.session import get_db
from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationResponse, NotificationUnreadCountResponse

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    is_read: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[NotificationResponse]:
    query = db.query(Notification).filter(
        Notification.site_id == current_user.site_id,
        Notification.deleted_at.is_(None),
    )
    if is_read is not None:
        query = query.filter(Notification.is_read == is_read)

    items = query.order_by(Notification.created_at.desc()).limit(limit).all()
    return [NotificationResponse.model_validate(item, from_attributes=True) for item in items]


@router.get("/unread-count", response_model=NotificationUnreadCountResponse)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> NotificationUnreadCountResponse:
    count = (
        db.query(func.count(Notification.id))
        .filter(
            Notification.site_id == current_user.site_id,
            Notification.is_read.is_(False),
            Notification.deleted_at.is_(None),
        )
        .scalar()
    ) or 0
    return NotificationUnreadCountResponse(unread_count=count)


@router.patch("/{notification_id}/read", response_model=NotificationResponse)
def mark_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> NotificationResponse:
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.site_id == current_user.site_id,
            Notification.deleted_at.is_(None),
        )
        .first()
    )
    if not notification:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return NotificationResponse.model_validate(notification, from_attributes=True)


@router.patch("/read-all", response_model=NotificationUnreadCountResponse)
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> NotificationUnreadCountResponse:
    db.query(Notification).filter(
        Notification.site_id == current_user.site_id,
        Notification.is_read.is_(False),
        Notification.deleted_at.is_(None),
    ).update({"is_read": True, "updated_at": datetime.now(UTC)})
    db.commit()
    return NotificationUnreadCountResponse(unread_count=0)


@router.post("/trigger-overdue", response_model=NotificationUnreadCountResponse)
def trigger_overdue_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> NotificationUnreadCountResponse:
    """Vadesi geçmiş pending borçlar için bildirim oluşturur (idempotent)."""
    from app.models.charge import Charge, ChargeStatus
    from app.services import notification_service

    today = datetime.now(UTC).date()

    overdue_charges = (
        db.query(Charge)
        .filter(
            Charge.site_id == current_user.site_id,
            Charge.status == ChargeStatus.pending,
            Charge.due_date < today,
            Charge.deleted_at.is_(None),
        )
        .all()
    )

    # Zaten bildirim varsa tekrar oluşturma
    existing_charge_ids = set(
        row[0]
        for row in db.query(Notification.related_charge_id)
        .filter(
            Notification.site_id == current_user.site_id,
            Notification.notification_type == "charge_overdue",
            Notification.deleted_at.is_(None),
        )
        .all()
        if row[0]
    )

    created = 0
    for charge in overdue_charges:
        if charge.id in existing_charge_ids:
            continue
        notification_service.notify_charge_overdue(
            db,
            site_id=current_user.site_id,
            flat_id=charge.flat_id,
            charge_id=charge.id,
            charge_type=charge.charge_type,
            period=charge.period,
            amount=str(charge.amount),
        )
        created += 1

    db.commit()
    return NotificationUnreadCountResponse(unread_count=created)
