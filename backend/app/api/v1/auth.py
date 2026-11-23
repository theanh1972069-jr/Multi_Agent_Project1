from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.app.api.deps import get_app_settings, get_current_user, get_db
from backend.app.core.config import Settings
from backend.app.core.security import create_access_token, hash_password, verify_password
from backend.app.db.models import User, UserProfile
from backend.app.schemas.auth import (
    AuthTokenResponse,
    UserLoginRequest,
    UserOut,
    UserProfileUpdateRequest,
    UserRegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _to_user_out(user: User) -> UserOut:
    profile = user.profile
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        birth_year=profile.birth_year if profile else None,
        gender=profile.gender if profile else None,
        preferred_language=profile.preferred_language if profile else "vi",
        created_at=user.created_at,
    )


@router.post(
    "/register",
    response_model=AuthTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> AuthTokenResponse:
    existing = db.scalar(select(User.id).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email is already registered",
        )

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role="user",
        is_active=True,
    )
    user.profile = UserProfile(preferred_language="vi")
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id, user.role, settings)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=_to_user_out(user),
    )


@router.post("/login", response_model=AuthTokenResponse)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
) -> AuthTokenResponse:
    user = db.scalar(
        select(User).options(joinedload(User.profile)).where(User.email == payload.email)
    )
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    token = create_access_token(user.id, user.role, settings)
    return AuthTokenResponse(
        access_token=token,
        token_type="bearer",
        user=_to_user_out(user),
    )


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)) -> UserOut:
    return _to_user_out(current_user)


@router.put("/me", response_model=UserOut)
def update_me(
    payload: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    fields = payload.model_fields_set
    if "full_name" in fields and payload.full_name is not None:
        current_user.full_name = payload.full_name

    profile = current_user.profile
    if profile is None:
        profile = UserProfile(user_id=current_user.id, preferred_language="vi")
        current_user.profile = profile

    if "birth_year" in fields:
        profile.birth_year = payload.birth_year
    if "gender" in fields:
        profile.gender = payload.gender
    if "preferred_language" in fields and payload.preferred_language is not None:
        profile.preferred_language = payload.preferred_language

    db.commit()
    db.refresh(current_user)
    return _to_user_out(current_user)
