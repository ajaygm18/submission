from collections.abc import Iterable

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from src.core.enums import UserRole
from src.core.security import decode_token
from src.db import get_db
from src.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def _extract_payload(credentials: HTTPAuthorizationCredentials | None) -> dict:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    try:
        return decode_token(credentials.credentials)
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = _extract_payload(credentials)
    if payload.get("token_type") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Standard access token required")
    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token user no longer exists")
    return user


def require_roles(*roles: UserRole):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role is not permitted")
        return current_user

    return dependency


def get_monitoring_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    payload = _extract_payload(credentials)
    if payload.get("token_type") != "monitoring" or payload.get("scope") != "monitoring:read":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Monitoring token required")
    if payload.get("role") != UserRole.monitoring_officer.value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Monitoring officer role required")
    user_id = payload.get("user_id")
    if not isinstance(user_id, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    user = db.get(User, user_id)
    if user is None or user.role != UserRole.monitoring_officer:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid monitoring token user")
    return user

