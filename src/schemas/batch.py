from datetime import datetime

from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    institution_id: int | None = None


class BatchRead(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class InviteCreate(BaseModel):
    expires_in_hours: int = Field(default=72, ge=1, le=720)


class InviteResponse(BaseModel):
    token: str
    expires_at: datetime


class BatchJoin(BaseModel):
    token: str = Field(min_length=10)

