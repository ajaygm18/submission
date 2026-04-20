from datetime import date, datetime, time, timezone

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db import Base


class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"), index=True, nullable=False)
    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    batch = relationship("Batch", backref="sessions")
    trainer = relationship("User")

