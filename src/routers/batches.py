from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.deps import require_roles
from src.core.enums import UserRole
from src.db import get_db
from src.models.batch import Batch, BatchInvite, batch_students, batch_trainers
from src.models.user import User
from src.schemas.batch import BatchCreate, BatchJoin, BatchRead, InviteCreate, InviteResponse
from src.services.summary import attendance_summary

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=BatchRead)
def create_batch(
    payload: BatchCreate,
    user: User = Depends(require_roles(UserRole.trainer, UserRole.institution)),
    db: Session = Depends(get_db),
) -> Batch:
    institution_id = payload.institution_id if user.role == UserRole.trainer else user.id
    if institution_id is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="institution_id is required")
    institution = db.get(User, institution_id)
    if institution is None or institution.role != UserRole.institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    if user.role == UserRole.trainer and user.institution_id != institution_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer cannot create for this institution")

    batch = Batch(name=payload.name, institution_id=institution_id)
    db.add(batch)
    db.flush()
    if user.role == UserRole.trainer:
        batch.trainers.append(user)
    db.commit()
    db.refresh(batch)
    return batch


@router.post("/{batch_id}/invite", response_model=InviteResponse)
def create_invite(
    batch_id: int,
    payload: InviteCreate,
    user: User = Depends(require_roles(UserRole.trainer)),
    db: Session = Depends(get_db),
) -> InviteResponse:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    is_assigned = db.execute(
        select(batch_trainers).where(batch_trainers.c.batch_id == batch_id, batch_trainers.c.trainer_id == user.id)
    ).first()
    if not is_assigned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer is not assigned to this batch")

    invite = BatchInvite(
        batch_id=batch_id,
        token=token_urlsafe(32),
        created_by=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=payload.expires_in_hours),
        used=False,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return InviteResponse(token=invite.token, expires_at=invite.expires_at)


@router.post("/join")
def join_batch(
    payload: BatchJoin,
    user: User = Depends(require_roles(UserRole.student)),
    db: Session = Depends(get_db),
) -> dict:
    invite = db.scalar(select(BatchInvite).where(BatchInvite.token == payload.token))
    if invite is None or invite.used:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    now = datetime.now(invite.expires_at.tzinfo) if invite.expires_at.tzinfo else datetime.now()
    if invite.expires_at < now:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invite has expired")
    batch = db.get(Batch, invite.batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    enrolled = db.execute(
        select(batch_students).where(batch_students.c.batch_id == batch.id, batch_students.c.student_id == user.id)
    ).first()
    if not enrolled:
        batch.students.append(user)
    invite.used = True
    db.commit()
    return {"message": "Joined batch", "batch_id": batch.id}


@router.get("/{batch_id}/summary")
def batch_summary(
    batch_id: int,
    user: User = Depends(require_roles(UserRole.institution)),
    db: Session = Depends(get_db),
) -> dict:
    batch = db.get(Batch, batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    if batch.institution_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Institution cannot access this batch")
    data = attendance_summary(db, batch_id=batch_id)
    data.update({"batch_id": batch.id, "batch_name": batch.name})
    return data
