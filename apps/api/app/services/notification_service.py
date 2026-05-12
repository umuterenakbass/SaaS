"""
Notification service — internal helper.
Other endpoints call these functions to create notifications;
they never touch the Notification model directly.
"""

from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationType


def _create(
    db: Session,
    *,
    site_id: str,
    notification_type: NotificationType,
    title: str,
    body: str,
    user_id: str | None = None,
    related_flat_id: str | None = None,
    related_charge_id: str | None = None,
    related_payment_id: str | None = None,
) -> Notification:
    notification = Notification(
        site_id=site_id,
        user_id=user_id,
        notification_type=notification_type,
        title=title,
        body=body,
        related_flat_id=related_flat_id,
        related_charge_id=related_charge_id,
        related_payment_id=related_payment_id,
        is_read=False,
    )
    db.add(notification)
    return notification


# ---------- Public helpers (called by endpoint layers) ----------


def notify_charge_created(
    db: Session,
    *,
    site_id: str,
    flat_id: str,
    charge_id: str,
    charge_type: str,
    period: str,
    amount: str,
    user_id: str | None = None,
) -> Notification:
    return _create(
        db,
        site_id=site_id,
        notification_type=NotificationType.charge_created,
        title=f"Yeni borç: {charge_type} — {period}",
        body=f"{period} dönemi için {amount} ₺ tutarında {charge_type} borcu oluşturuldu.",
        user_id=user_id,
        related_flat_id=flat_id,
        related_charge_id=charge_id,
    )


def notify_payment_received(
    db: Session,
    *,
    site_id: str,
    flat_id: str,
    payment_id: str,
    amount: str,
    method: str,
    user_id: str | None = None,
) -> Notification:
    return _create(
        db,
        site_id=site_id,
        notification_type=NotificationType.payment_received,
        title=f"Ödeme alındı: {amount} ₺",
        body=f"{amount} ₺ tutarında {method} ödemesi alındı.",
        user_id=user_id,
        related_flat_id=flat_id,
        related_payment_id=payment_id,
    )


def notify_charge_overdue(
    db: Session,
    *,
    site_id: str,
    flat_id: str,
    charge_id: str,
    charge_type: str,
    period: str,
    amount: str,
    user_id: str | None = None,
) -> Notification:
    return _create(
        db,
        site_id=site_id,
        notification_type=NotificationType.charge_overdue,
        title=f"Vadesi geçmiş borç: {charge_type} — {period}",
        body=f"{period} dönemi {charge_type} borcunun ({amount} ₺) vadesi geçti.",
        user_id=user_id,
        related_flat_id=flat_id,
        related_charge_id=charge_id,
    )


def notify_plan_generated(
    db: Session,
    *,
    site_id: str,
    plan_name: str,
    period: str,
    created_count: int,
    skipped_count: int,
    user_id: str | None = None,
) -> Notification:
    return _create(
        db,
        site_id=site_id,
        notification_type=NotificationType.plan_generated,
        title=f"Plan üretimi: {plan_name} — {period}",
        body=(
            f'"{plan_name}" planı {period} dönemi için çalıştırıldı. '
            f"{created_count} borç oluşturuldu, {skipped_count} atlandı."
        ),
        user_id=user_id,
    )
