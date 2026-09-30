from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, HTTPException, Request, status
from jose import JWTError, jwt

from app.api.deps import CurrentUser, SessionDep
from app.core.config import get_settings
from app.core.logging import log_auth_event
from app.core.rate_limiter import auth_rate_limiter
from app.core.security import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    hash_refresh_token,
    revoke_refresh_token,
    store_refresh_token,
)
from app.db.models.refresh_token import RefreshToken
from app.db.models.user import User
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.schemas.user import UserCreate, UserLogin, UserResponse

settings = get_settings()

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: SessionDep, request: Request) -> User:
    # Apply rate limiting
    if not auth_rate_limiter.is_allowed(payload.email.lower()):
        log_auth_event("REGISTRATION_RATE_LIMITED", email=payload.email.lower(), success=False)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later.",
        )

    normalized_email = payload.email.lower()
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        log_auth_event("REGISTRATION_FAILED", email=normalized_email, success=False, details={"reason": "email_exists"})
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    user = User(
        email=normalized_email,
        full_name=payload.full_name,
        password_hash=get_password_hash(payload.password),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    log_auth_event("REGISTRATION_SUCCESS", email=normalized_email, success=True, details={"user_id": str(user.id)})
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: SessionDep, request: Request) -> TokenResponse:
    normalized_email = payload.email.lower()

    # Apply rate limiting to login attempts
    if not auth_rate_limiter.is_allowed(normalized_email):
        log_auth_event("LOGIN_RATE_LIMITED", email=normalized_email, success=False)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later.",
        )

    user = authenticate_user(db, normalized_email, payload.password)
    if not user:
        log_auth_event("LOGIN_FAILED", email=normalized_email, success=False, details={"reason": "invalid_credentials"})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": str(user.id)}, token_version=user.token_version)
    refresh_token = create_refresh_token({"sub": str(user.id)})
    store_refresh_token(
        db,
        user.id,
        refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    log_auth_event("LOGIN_SUCCESS", email=normalized_email, success=True, details={"user_id": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


@router.post("/refresh", response_model=TokenResponse)
def refresh_user_token(payload: RefreshTokenRequest, db: SessionDep, request: Request) -> TokenResponse:
    refresh_value = payload.refresh_token
    try:
        decoded = jwt.decode(refresh_value, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc

    if decoded.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user_id = decoded.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    token_hash = hash_refresh_token(refresh_value)
    token_record = db.query(RefreshToken).filter(RefreshToken.user_id == user.id, RefreshToken.token_hash == token_hash).first()
    if token_record is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked or invalid")
    expires_at = token_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if token_record.revoked_at is not None or expires_at <= datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired")

    token_record.revoked_at = datetime.now(timezone.utc)
    token_record.last_used_at = datetime.now(timezone.utc)
    db.add(token_record)

    access_token = create_access_token({"sub": str(user.id)}, token_version=user.token_version)
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    store_refresh_token(
        db,
        user.id,
        new_refresh_token,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    log_auth_event("TOKEN_REFRESHED", email=user.email, success=True, details={"user_id": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=new_refresh_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
def get_me(current_user: CurrentUser) -> User:
    return current_user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(current_user: CurrentUser, db: SessionDep) -> None:
    """Invalidate all access tokens and refresh tokens issued before this logout."""
    current_user.token_version += 1
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id, RefreshToken.revoked_at.is_(None)).update(
        {"revoked_at": datetime.now(timezone.utc)}
    )
    db.add(current_user)
    db.commit()
