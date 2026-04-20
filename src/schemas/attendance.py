from datetime import datetime

from pydantic import BaseModel

from src.core.enums import AttendanceStatus


class AttendanceMark(BaseModel):
    session_id: int
    status: AttendanceStatus


class AttendanceRead(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: AttendanceStatus
    marked_at: datetime
    student_name: str | None = None

    model_config = {"from_attributes": True}

