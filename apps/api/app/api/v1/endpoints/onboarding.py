import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.block import Block
from app.models.charge import Charge
from app.models.flat import Flat, FlatStatus
from app.models.user import User, UserRole
from app.schemas.onboarding import (
    BlockSetupItem,
    BlockSummary,
    OnboardingSetupRequest,
    OnboardingSetupResult,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

_ADMIN = require_roles({UserRole.admin, UserRole.manager})


def _generate_unit_no(prefix: str, floor: int, position: int) -> str:
    """Daire numarası üret: A101, A102 veya (prefix boşsa) 101, 102"""
    return f"{prefix}{floor}{position:02d}"


def _create_block_with_flats(
    db: Session,
    site_id: str,
    item: BlockSetupItem,
) -> tuple[Block, int]:
    """Bir blok + tüm dairelerini oluştur. (block, flat_count) döndürür."""
    # Kod çakışması kontrolü
    existing = (
        db.query(Block)
        .filter(Block.site_id == site_id, Block.code == item.code, Block.deleted_at.is_(None))
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{item.code}' kodlu blok zaten mevcut",
        )

    block = Block(
        id=str(uuid.uuid4()),
        site_id=site_id,
        name=item.name,
        code=item.code,
    )
    db.add(block)
    db.flush()  # block.id'yi al

    prefix = item.unit_prefix if item.unit_prefix else item.code
    flat_count = 0
    seen_units: set[str] = set()

    for floor in range(1, item.floors + 1):
        for pos in range(1, item.flats_per_floor + 1):
            unit_no = _generate_unit_no(prefix, floor, pos)
            # Aynı blok içinde duplicate olmamalı
            if unit_no in seen_units:
                continue
            seen_units.add(unit_no)

            flat = Flat(
                id=str(uuid.uuid4()),
                site_id=site_id,
                block_id=block.id,
                unit_no=unit_no,
                floor=floor,
                status=FlatStatus.active,
            )
            db.add(flat)
            flat_count += 1

    return block, flat_count


@router.post(
    "/setup",
    response_model=OnboardingSetupResult,
    status_code=status.HTTP_201_CREATED,
    summary="Toplu blok + daire kurulumu",
    description=(
        "Tek istekte birden fazla blok ve tüm dairelerini oluşturur. "
        "İsteğe bağlı olarak oluşturulan tüm dairelere ortak bir borç şablonu uygular."
    ),
)
def onboarding_setup(
    payload: OnboardingSetupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(_ADMIN),
) -> OnboardingSetupResult:
    site_id = current_user.site_id

    # Kod çakışmasını önceden kontrol et (atomik)
    codes = [b.code for b in payload.blocks]
    if len(codes) != len(set(codes)):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Blok kodları birbirinden farklı olmalı",
        )

    block_summaries: list[BlockSummary] = []
    total_flats = 0
    created_flat_ids: list[str] = []

    for item in payload.blocks:
        block, flat_count = _create_block_with_flats(db, site_id, item)
        block_summaries.append(
            BlockSummary(id=block.id, name=block.name, code=block.code, flats_created=flat_count)
        )
        total_flats += flat_count

    # Tüm flush edilmiş dairelerin ID'lerini topla
    db.flush()
    all_flat_ids = [
        f.id
        for bs in block_summaries
        for f in db.query(Flat)
        .filter(
            Flat.site_id == site_id,
            Flat.block_id.in_([b.id for b in db.query(Block).filter(Block.id.in_([bs.id for bs in block_summaries])).all()]),
            Flat.deleted_at.is_(None),
        )
        .all()
    ]

    # Borç şablonu uygulanacaksa tüm dairelere ekle
    charges_created = 0
    if payload.charge_template:
        tmpl = payload.charge_template
        due = date.fromisoformat(tmpl.due_date)

        for flat_id in all_flat_ids:
            charge = Charge(
                id=str(uuid.uuid4()),
                site_id=site_id,
                flat_id=flat_id,
                charge_type=tmpl.charge_type,
                amount=tmpl.amount,
                period=tmpl.period,
                due_date=due,
            )
            db.add(charge)
            charges_created += 1

    db.commit()

    return OnboardingSetupResult(
        blocks_created=len(block_summaries),
        flats_created=total_flats,
        charges_created=charges_created,
        blocks=block_summaries,
        message=(
            f"{len(block_summaries)} blok ve {total_flats} daire oluşturuldu"
            + (f", {charges_created} borç eklendi" if charges_created else "")
            + "."
        ),
    )
