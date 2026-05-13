from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.announcement import Announcement
from app.models.user import User, UserRole
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse, AnnouncementUpdate

router = APIRouter(prefix="/announcements", tags=["announcements"])

_ADMIN_ROLES = require_roles({UserRole.admin, UserRole.manager})


def _to_response(a: Announcement) -> AnnouncementResponse:
    return AnnouncementResponse(
        id=a.id,
        site_id=a.site_id,
        created_by=a.created_by,
        title=a.title,
        body=a.body,
        block_id=a.block_id,
        is_pinned=a.is_pinned,
        is_published=a.is_published,
        created_at=a.created_at.isoformat(),
    )


# ---------------------------------------------------------------------------
# Admin: CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=list[AnnouncementResponse])
def list_announcements(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> list[AnnouncementResponse]:
    """Tüm kullanıcılar listeleyebilir (admin: hepsi, resident: sadece published)."""
    query = db.query(Announcement).filter(
        Announcement.site_id == current_user.site_id,
        Announcement.deleted_at.is_(None),
    )
    if current_user.role == UserRole.resident:
        query = query.filter(Announcement.is_published.is_(True))
    items = query.order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc()).all()
    return [_to_response(a) for a in items]


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
def create_announcement(
    payload: AnnouncementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_ADMIN_ROLES),
) -> AnnouncementResponse:
    ann = Announcement(
        site_id=current_user.site_id,
        created_by=current_user.id,
        title=payload.title,
        body=payload.body,
        block_id=payload.block_id,
        is_pinned=payload.is_pinned,
        is_published=payload.is_published,
    )
    db.add(ann)
    db.commit()
    db.refresh(ann)
    return _to_response(ann)


@router.patch("/{announcement_id}", response_model=AnnouncementResponse)
def update_announcement(
    announcement_id: str,
    payload: AnnouncementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_ADMIN_ROLES),
) -> AnnouncementResponse:
    ann = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.site_id == current_user.site_id,
        Announcement.deleted_at.is_(None),
    ).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Duyuru bulunamadı.")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(ann, field, value)
    db.commit()
    db.refresh(ann)
    return _to_response(ann)


@router.delete("/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_announcement(
    announcement_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_ADMIN_ROLES),
) -> None:
    ann = db.query(Announcement).filter(
        Announcement.id == announcement_id,
        Announcement.site_id == current_user.site_id,
        Announcement.deleted_at.is_(None),
    ).first()
    if not ann:
        raise HTTPException(status_code=404, detail="Duyuru bulunamadı.")
    from datetime import UTC, datetime
    ann.deleted_at = datetime.now(UTC)
    db.commit()
