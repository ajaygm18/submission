from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.deps import require_roles
from src.core.enums import UserRole
from src.db import get_db
from src.models.attendance import Attendance
from src.models.batch import batch_students
from src.models.session import Session as ClassSession
from src.models.user import User
from src.schemas.attendance import AttendanceMark

router = APIRouter(prefix="/attendance", tags=["attendance"])


@router.post("/mark")
def mark_attendance(
    payload: AttendanceMark,
    user: User = Depends(require_roles(UserRole.student)),
    db: Session = Depends(get_db),
) -> dict:
    session = db.get(ClassSession, payload.session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    enrolled = db.execute(
        select(batch_students).where(
            batch_students.c.batch_id == session.batch_id,
            batch_students.c.student_id == user.id,
        )
    ).first()
    if not enrolled:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Student is not enrolled in this batch")

    now = datetime.now()
    starts = datetime.combine(session.date, session.start_time)
    ends = datetime.combine(session.date, session.end_time)
    if not starts <= now <= ends:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Attendance can only be marked during session")

    record = db.scalar(
        select(Attendance).where(Attendance.session_id == session.id, Attendance.student_id == user.id)
    )
    if record is None:
        record = Attendance(session_id=session.id, student_id=user.id, status=payload.status)
        db.add(record)
    else:
        record.status = payload.status
        record.marked_at = datetime.now()
    db.commit()
    db.refresh(record)
    return {
        "id": record.id,
        "session_id": record.session_id,
        "student_id": record.student_id,
        "status": record.status.value,
        "marked_at": record.marked_at,
    }

