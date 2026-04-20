from datetime import date, datetime, time

from pydantic import BaseModel, Field, model_validator


class SessionCreate(BaseModel):
    batch_id: int
    title: str = Field(min_length=1, max_length=180)
    date: date
    start_time: time
    end_time: time

    @model_validator(mode="after")
    def validate_time_window(self) -> "SessionCreate":
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


class SessionRead(BaseModel):
    id: int
    batch_id: int
    trainer_id: int
    title: str
    date: date
    start_time: time
    end_time: time
    created_at: datetime

    model_config = {"from_attributes": True}

