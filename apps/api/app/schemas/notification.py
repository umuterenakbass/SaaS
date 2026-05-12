from datetime import datetime

from pydantic import BaseModel

from app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    id: str
    site_id: str
    user_id: str | None
    notification_type: NotificationType
    title: str
    body: str
    related_flat_id: str | None
    related_charge_id: str | None
    related_payment_id: str | None
    is_read: bool
    created_at: datetime


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int
