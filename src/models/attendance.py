from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.enums import AttendanceStatus
from src.db import Base


class Attendance(Base):
    __tablename__ = "attendance"
    __table_args__ = (UniqueConstraint("session_id", "student_id", name="uq_attendance_session_student"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("sessions.id"), index=True, nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[AttendanceStatus] = mapped_column(Enum(AttendanceStatus), nullable=False)
    marked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    session = relationship("Session", backref="attendance_records")
    student = relationship("User")

