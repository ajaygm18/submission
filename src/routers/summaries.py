from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.deps import require_roles
from src.core.enums import UserRole
from src.db import get_db
from src.models.batch import Batch
from src.models.user import User
from src.services.summary import attendance_summary

router = APIRouter(tags=["summaries"])


@router.get("/institutions/{institution_id}/summary")
def institution_summary(
    institution_id: int,
    user: User = Depends(require_roles(UserRole.programme_manager)),
    db: Session = Depends(get_db),
) -> dict:
    institution = db.get(User, institution_id)
    if institution is None or institution.role != UserRole.institution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    data = attendance_summary(db, institution_id=institution_id)
    data.update({"institution_id": institution.id, "institution_name": institution.name})
    return data


@router.get("/programme/summary")
def programme_summary(
    user: User = Depends(require_roles(UserRole.programme_manager)),
    db: Session = Depends(get_db),
) -> dict:
    data = attendance_summary(db)
    data.update(
        {
            "institutions": db.scalar(select(func.count(User.id)).where(User.role == UserRole.institution)) or 0,
            "batches": db.scalar(select(func.count(Batch.id))) or 0,
        }
    )
    return data

