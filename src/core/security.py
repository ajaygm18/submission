from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from passlib.context import CryptContext

from src.config import get_settings
from src.core.enums import UserRole

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _encode(payload: dict[str, Any]) -> str:
    settings = get_settings()
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(user_id: int, role: UserRole) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=settings.access_token_expire_hours)
    return _encode(
        {
            "user_id": user_id,
            "role": role.value,
            "token_type": "access",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
    )


def create_monitoring_token(user_id: int) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    exp = now + timedelta(hours=settings.monitoring_token_expire_hours)
    return _encode(
        {
            "user_id": user_id,
            "role": UserRole.monitoring_officer.value,
            "token_type": "monitoring",
            "scope": "monitoring:read",
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
    )


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])

