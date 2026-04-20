from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.deps import require_roles
from src.core.enums import UserRole
from src.db import get_db
from src.models.attendance import Attendance
from src.models.batch import Batch, batch_trainers
from src.models.session import Session as ClassSession
from src.models.user import User
from src.schemas.session import SessionCreate, SessionRead

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead)
def create_session(
    payload: SessionCreate,
    user: User = Depends(require_roles(UserRole.trainer)),
    db: Session = Depends(get_db),
) -> ClassSession:
    batch = db.get(Batch, payload.batch_id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    is_assigned = db.execute(
        select(batch_trainers).where(batch_trainers.c.batch_id == batch.id, batch_trainers.c.trainer_id == user.id)
    ).first()
    if not is_assigned:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer is not assigned to this batch")
    session = ClassSession(
        batch_id=payload.batch_id,
        trainer_id=user.id,
        title=payload.title,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/{session_id}/attendance")
def session_attendance(
    session_id: int,
    user: User = Depends(require_roles(UserRole.trainer)),
    db: Session = Depends(get_db),
) -> dict:
    session = db.get(ClassSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.trainer_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Trainer cannot access this session")
    rows = (
        db.query(Attendance, User)
        .join(User, Attendance.student_id == User.id)
        .filter(Attendance.session_id == session_id)
        .order_by(User.name)
        .all()
    )
    return {
        "session_id": session_id,
        "records": [
            {
                "student_id": student.id,
                "student_name": student.name,
                "status": attendance.status.value,
                "marked_at": attendance.marked_at,
            }
            for attendance, student in rows
        ],
    }

