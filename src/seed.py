from datetime import date, datetime, timedelta

from sqlalchemy import select

from src.core.enums import AttendanceStatus, UserRole
from src.core.security import hash_password
from src.db import Base, SessionLocal, engine
from src.models.attendance import Attendance
from src.models.batch import Batch, batch_students, batch_trainers
from src.models.session import Session as ClassSession
from src.models.user import User

PASSWORD = "password123"


def get_or_create_user(db, name: str, email: str, role: UserRole, institution_id: int | None = None) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user:
        return user
    user = User(
        name=name,
        email=email,
        role=role,
        institution_id=institution_id,
        hashed_password=hash_password(PASSWORD),
    )
    db.add(user)
    db.flush()
    return user


def ensure_link(db, table, **values) -> None:
    exists = db.execute(select(table).filter_by(**values)).first()
    if not exists:
        db.execute(table.insert().values(**values))


def seed(reset: bool = False) -> None:
    if reset:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        inst1 = get_or_create_user(db, "North City Institute", "institution1@example.com", UserRole.institution)
        inst2 = get_or_create_user(db, "South Valley Institute", "institution2@example.com", UserRole.institution)
        pm = get_or_create_user(db, "Priya Programme Manager", "pm@example.com", UserRole.programme_manager)
        mo = get_or_create_user(db, "Mohan Monitoring Officer", "monitor@example.com", UserRole.monitoring_officer)

        trainers = [
            get_or_create_user(db, "Trainer One", "trainer1@example.com", UserRole.trainer, inst1.id),
            get_or_create_user(db, "Trainer Two", "trainer2@example.com", UserRole.trainer, inst1.id),
            get_or_create_user(db, "Trainer Three", "trainer3@example.com", UserRole.trainer, inst2.id),
            get_or_create_user(db, "Trainer Four", "trainer4@example.com", UserRole.trainer, inst2.id),
        ]
        students = [
            get_or_create_user(db, f"Student {i:02d}", f"student{i}@example.com", UserRole.student)
            for i in range(1, 16)
        ]
        db.flush()

        batches = [
            Batch(name="Python Foundations A", institution_id=inst1.id),
            Batch(name="Data Skills B", institution_id=inst1.id),
            Batch(name="Web Backend C", institution_id=inst2.id),
        ]
        for batch in batches:
            existing = db.scalar(select(Batch).where(Batch.name == batch.name))
            if existing:
                batch.id = existing.id
            else:
                db.add(batch)
                db.flush()
        batches = [db.scalar(select(Batch).where(Batch.name == name)) for name in ["Python Foundations A", "Data Skills B", "Web Backend C"]]

        ensure_link(db, batch_trainers, batch_id=batches[0].id, trainer_id=trainers[0].id)
        ensure_link(db, batch_trainers, batch_id=batches[0].id, trainer_id=trainers[1].id)
        ensure_link(db, batch_trainers, batch_id=batches[1].id, trainer_id=trainers[1].id)
        ensure_link(db, batch_trainers, batch_id=batches[2].id, trainer_id=trainers[2].id)
        ensure_link(db, batch_trainers, batch_id=batches[2].id, trainer_id=trainers[3].id)

        for student in students[:7]:
            ensure_link(db, batch_students, batch_id=batches[0].id, student_id=student.id)
        for student in students[5:11]:
            ensure_link(db, batch_students, batch_id=batches[1].id, student_id=student.id)
        for student in students[10:]:
            ensure_link(db, batch_students, batch_id=batches[2].id, student_id=student.id)

        now = datetime.now()
        today = date.today()
        session_specs = [
            (batches[0], trainers[0], "Python setup", today - timedelta(days=7), "09:00", "11:00"),
            (batches[0], trainers[1], "Control flow", today - timedelta(days=6), "09:00", "11:00"),
            (batches[0], trainers[0], "Functions", today - timedelta(days=5), "09:00", "11:00"),
            (batches[1], trainers[1], "Spreadsheets", today - timedelta(days=4), "10:00", "12:00"),
            (batches[1], trainers[1], "SQL basics", today - timedelta(days=3), "10:00", "12:00"),
            (batches[2], trainers[2], "HTTP APIs", today - timedelta(days=2), "14:00", "16:00"),
            (batches[2], trainers[3], "FastAPI routes", today - timedelta(days=1), "14:00", "16:00"),
            (
                batches[2],
                trainers[2],
                "Deployment",
                today,
                (now - timedelta(minutes=30)).strftime("%H:%M"),
                (now + timedelta(minutes=90)).strftime("%H:%M"),
            ),
        ]
        sessions = []
        for batch, trainer, title, day, start, end in session_specs:
            existing = db.scalar(select(ClassSession).where(ClassSession.title == title, ClassSession.batch_id == batch.id))
            if existing:
                existing.date = day
                existing.start_time = datetime.strptime(start, "%H:%M").time()
                existing.end_time = datetime.strptime(end, "%H:%M").time()
                sessions.append(existing)
                continue
            session = ClassSession(
                batch_id=batch.id,
                trainer_id=trainer.id,
                title=title,
                date=day,
                start_time=datetime.strptime(start, "%H:%M").time(),
                end_time=datetime.strptime(end, "%H:%M").time(),
            )
            db.add(session)
            db.flush()
            sessions.append(session)

        statuses = [AttendanceStatus.present, AttendanceStatus.present, AttendanceStatus.late, AttendanceStatus.absent]
        for session in sessions:
            enrolled_ids = [
                row[0]
                for row in db.execute(
                    select(batch_students.c.student_id).where(batch_students.c.batch_id == session.batch_id)
                ).all()
            ]
            for index, student_id in enumerate(enrolled_ids):
                existing = db.scalar(
                    select(Attendance).where(Attendance.session_id == session.id, Attendance.student_id == student_id)
                )
                if not existing:
                    db.add(
                        Attendance(
                            session_id=session.id,
                            student_id=student_id,
                            status=statuses[index % len(statuses)],
                        )
                    )

        db.commit()
        print("Seed complete.")
        print(f"Demo password for all accounts: {PASSWORD}")
    finally:
        db.close()


if __name__ == "__main__":
    seed(reset=False)
