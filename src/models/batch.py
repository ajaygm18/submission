from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


batch_trainers = Table(
    "batch_trainers",
    Base.metadata,
    Column("batch_id", ForeignKey("batches.id"), primary_key=True),
    Column("trainer_id", ForeignKey("users.id"), primary_key=True),
)

batch_students = Table(
    "batch_students",
    Base.metadata,
    Column("batch_id", ForeignKey("batches.id"), primary_key=True),
    Column("student_id", ForeignKey("users.id"), primary_key=True),
)


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    institution_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    institution = relationship("User", foreign_keys=[institution_id])
    trainers = relationship("User", secondary=batch_trainers, backref="trainer_batches")
    students = relationship("User", secondary=batch_students, backref="student_batches")


class BatchInvite(Base):
    __tablename__ = "batch_invites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), index=True, nullable=False)
    token: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    batch = relationship("Batch", backref="invites")
    creator = relationship("User", foreign_keys=[created_by])

