from pydantic import BaseModel, EmailStr, Field

from src.core.enums import UserRole


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    institution_id: int | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MonitoringTokenRequest(BaseModel):
    key: str = Field(min_length=1)

