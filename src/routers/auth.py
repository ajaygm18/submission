from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.config import get_settings
from src.core.deps import require_roles
from src.core.enums import UserRole
from src.core.security import create_access_token, create_monitoring_token, hash_password, verify_password
from src.db import get_db
from src.models.user import User
from src.schemas.auth import LoginRequest, MonitoringTokenRequest, SignupRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> TokenResponse:
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    if payload.institution_id is not None:
        institution = db.get(User, payload.institution_id)
        if institution is None or institution.role != UserRole.institution:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    user = User(
        name=payload.name,
        email=payload.email.lower(),
        hashed_password=hash_password(payload.password),
        role=payload.role,
        institution_id=payload.institution_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(user.id, user.role))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(user.id, user.role))


@router.post("/monitoring-token", response_model=TokenResponse)
def monitoring_token(
    payload: MonitoringTokenRequest,
    user: User = Depends(require_roles(UserRole.monitoring_officer)),
) -> TokenResponse:
    configured_key = get_settings().monitoring_api_key
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Monitoring API key is not configured",
        )
    if payload.key != configured_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid monitoring API key")
    return TokenResponse(access_token=create_monitoring_token(user.id))
