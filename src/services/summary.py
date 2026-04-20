from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.enums import AttendanceStatus
from src.models.attendance import Attendance
from src.models.batch import Batch
from src.models.session import Session as ClassSession


def attendance_summary(db: Session, batch_id: int | None = None, institution_id: int | None = None) -> dict:
    stmt = select(Attendance.status, func.count(Attendance.id)).join(ClassSession)
    session_count_stmt = select(func.count(ClassSession.id))
    student_count_stmt = select(func.count(func.distinct(Attendance.student_id))).join(ClassSession)

    if batch_id is not None:
        stmt = stmt.where(ClassSession.batch_id == batch_id)
        session_count_stmt = session_count_stmt.where(ClassSession.batch_id == batch_id)
        student_count_stmt = student_count_stmt.where(ClassSession.batch_id == batch_id)

    if institution_id is not None:
        stmt = stmt.join(Batch, ClassSession.batch_id == Batch.id).where(Batch.institution_id == institution_id)
        session_count_stmt = session_count_stmt.join(Batch).where(Batch.institution_id == institution_id)
        student_count_stmt = student_count_stmt.join(Batch, ClassSession.batch_id == Batch.id).where(
            Batch.institution_id == institution_id
        )

    counts = {status.value: 0 for status in AttendanceStatus}
    for status_value, count in db.execute(stmt.group_by(Attendance.status)).all():
        key = status_value.value if hasattr(status_value, "value") else str(status_value)
        counts[key] = count

    total = sum(counts.values())
    percentages = {key: round((value / total * 100), 2) if total else 0 for key, value in counts.items()}
    return {
        "total_attendance_records": total,
        "status_counts": counts,
        "status_percentages": percentages,
        "sessions": db.scalar(session_count_stmt) or 0,
        "students_with_attendance": db.scalar(student_count_stmt) or 0,
    }

