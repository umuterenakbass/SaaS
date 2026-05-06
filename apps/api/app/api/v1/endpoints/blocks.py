from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import require_roles, require_tenant_context
from app.db.session import get_db
from app.models.block import Block
from app.models.user import User, UserRole
from app.schemas.block import BlockCreateRequest, BlockResponse, BlockUpdateRequest

router = APIRouter(prefix="/blocks", tags=["blocks"])


@router.get("", response_model=list[BlockResponse])
def list_blocks(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> list[BlockResponse]:
    blocks = (
        db.query(Block)
        .filter(Block.site_id == current_user.site_id, Block.deleted_at.is_(None))
        .order_by(Block.created_at.desc())
        .all()
    )
    return [BlockResponse.model_validate(item, from_attributes=True) for item in blocks]


@router.post("", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
def create_block(
    payload: BlockCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> BlockResponse:
    duplicate = (
        db.query(Block)
        .filter(
            Block.site_id == current_user.site_id,
            Block.code == payload.code,
            Block.deleted_at.is_(None),
        )
        .first()
    )
    if duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Block code already exists",
        )

    block = Block(
        site_id=current_user.site_id,
        name=payload.name.strip(),
        code=payload.code.strip(),
    )
    db.add(block)
    db.commit()
    db.refresh(block)
    return BlockResponse.model_validate(block, from_attributes=True)


@router.get("/{block_id}", response_model=BlockResponse)
def get_block(
    block_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
) -> BlockResponse:
    block = (
        db.query(Block)
        .filter(
            Block.id == block_id,
            Block.site_id == current_user.site_id,
            Block.deleted_at.is_(None),
        )
        .first()
    )
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")

    return BlockResponse.model_validate(block, from_attributes=True)


@router.patch("/{block_id}", response_model=BlockResponse)
def update_block(
    block_id: str,
    payload: BlockUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> BlockResponse:
    block = (
        db.query(Block)
        .filter(
            Block.id == block_id,
            Block.site_id == current_user.site_id,
            Block.deleted_at.is_(None),
        )
        .first()
    )
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")

    updates = payload.model_dump(exclude_unset=True)
    if "code" in updates:
        duplicate = (
            db.query(Block)
            .filter(
                Block.site_id == current_user.site_id,
                Block.code == updates["code"],
                Block.id != block_id,
                Block.deleted_at.is_(None),
            )
            .first()
        )
        if duplicate:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Block code already exists",
            )

    for key, value in updates.items():
        setattr(block, key, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(block)
    return BlockResponse.model_validate(block, from_attributes=True)


@router.delete("/{block_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_block(
    block_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_tenant_context),
    _: User = Depends(require_roles({UserRole.admin, UserRole.manager})),
) -> None:
    block = (
        db.query(Block)
        .filter(
            Block.id == block_id,
            Block.site_id == current_user.site_id,
            Block.deleted_at.is_(None),
        )
        .first()
    )
    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Block not found")

    block.deleted_at = datetime.now(UTC)
    db.commit()
