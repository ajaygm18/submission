from datetime import date, datetime, timedelta
import os
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-long-enough-for-hs256")
os.environ.setdefault("MONITORING_API_KEY", "test-monitoring-key")

from src.core.enums import UserRole
from src.core.security import hash_password
from src.db import Base, get_db
from src.main import app
from src.models.batch import Batch, batch_students, batch_trainers
from src.models.session import Session as ClassSession
from src.models.user import User


@pytest.fixture()
def db_session(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def seeded(db_session):
    institution = User(
        name="Test Institution",
        email="institution@example.com",
        role=UserRole.institution,
        hashed_password=hash_password("password123"),
    )
    trainer = User(
        name="Test Trainer",
        email="trainer@example.com",
        role=UserRole.trainer,
        hashed_password=hash_password("password123"),
    )
    student = User(
        name="Test Student",
        email="student@example.com",
        role=UserRole.student,
        hashed_password=hash_password("password123"),
    )
    db_session.add_all([institution, trainer, student])
    db_session.flush()
    trainer.institution_id = institution.id
    batch = Batch(name="Test Batch", institution_id=institution.id)
    db_session.add(batch)
    db_session.flush()
    db_session.execute(batch_trainers.insert().values(batch_id=batch.id, trainer_id=trainer.id))
    db_session.execute(batch_students.insert().values(batch_id=batch.id, student_id=student.id))
    now = datetime.now()
    session = ClassSession(
        batch_id=batch.id,
        trainer_id=trainer.id,
        title="Active Session",
        date=date.today(),
        start_time=(now - timedelta(minutes=10)).time(),
        end_time=(now + timedelta(minutes=50)).time(),
    )
    db_session.add(session)
    db_session.commit()
    return {"institution": institution, "trainer": trainer, "student": student, "batch": batch, "session": session}

