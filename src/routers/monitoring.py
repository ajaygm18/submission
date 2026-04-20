from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.core.deps import get_monitoring_user
from src.db import get_db
from src.models.attendance import Attendance
from src.models.session import Session as ClassSession
from src.models.user import User

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/attendance")
def monitoring_attendance(
    user: User = Depends(get_monitoring_user),
    db: Session = Depends(get_db),
) -> dict:
    rows = (
        db.query(Attendance, ClassSession, User)
        .join(ClassSession, Attendance.session_id == ClassSession.id)
        .join(User, Attendance.student_id == User.id)
        .order_by(Attendance.marked_at.desc())
        .limit(500)
        .all()
    )
    return {
        "records": [
            {
                "attendance_id": attendance.id,
                "session_id": session.id,
                "session_title": session.title,
                "batch_id": session.batch_id,
                "student_id": student.id,
                "student_name": student.name,
                "status": attendance.status.value,
                "marked_at": attendance.marked_at,
            }
            for attendance, session, student in rows
        ]
    }

