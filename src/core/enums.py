from enum import StrEnum


class UserRole(StrEnum):
    student = "student"
    trainer = "trainer"
    institution = "institution"
    programme_manager = "programme_manager"
    monitoring_officer = "monitoring_officer"


class AttendanceStatus(StrEnum):
    present = "present"
    absent = "absent"
    late = "late"

