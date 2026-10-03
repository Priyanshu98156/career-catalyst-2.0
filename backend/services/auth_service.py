import secrets
from typing import Optional, Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.models import RefreshToken, User, tenant_filter
from backend.schemas.auth import TokenData, UserCreate
from backend.security import (
    create_access_token,
    decode_token,
    generate_refresh_token_data,
    hash_password,
    hash_token,
    verify_password,
)


def create_refresh_token(user_id: str, tenant_id: str, db: Session) -> str:
    """Generate a long-lived Refresh Token (default 7 days) and save its hash in DB."""
    raw_token, expire = generate_refresh_token_data(user_id=user_id, tenant_id=tenant_id)

    # Persist token hash to DB for session tracking & revocation
    db_token = RefreshToken(
        user_id=user_id,
        tenant_id=tenant_id,
        token_hash=hash_token(raw_token),
        expires_at=expire,
        revoked=False,
    )
    db.add(db_token)
    db.commit()

    return raw_token


def rotate_refresh_token(refresh_token_str: str, db: Session) -> Tuple[str, str, User]:
    """
    Refresh Token Rotation:
    Validate provided refresh token, revoke it, and return a new (access_token, refresh_token, user) tuple.
    """
    payload = decode_token(refresh_token_str)
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a valid refresh token",
        )

    user_id = payload.get("sub")
    tenant_id = payload.get("tenant_id")
    token_h = hash_token(refresh_token_str)

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_h,
        RefreshToken.revoked.is_(False),
    ).first()

    if not db_token:
        # Potential token reuse attack: revoke all tokens for this user
        db.query(RefreshToken).filter(RefreshToken.user_id == user_id).update({"revoked": True})
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token was revoked or invalid. Please sign in again.",
        )

    # Invalidate old refresh token (Rotation)
    db_token.revoked = True
    db.commit()

    user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found")

    new_access_token = create_access_token(user_id=user.id, tenant_id=user.tenant_id, email=user.email)
    new_refresh_token = create_refresh_token(user_id=user.id, tenant_id=user.tenant_id, db=db)

    return new_access_token, new_refresh_token, user


def revoke_user_refresh_token(refresh_token_str: str, db: Session) -> bool:
    """Revoke a specific refresh token upon logout."""
    token_h = hash_token(refresh_token_str)
    db_token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_h).first()
    if db_token:
        db_token.revoked = True
        db.commit()
        return True
    return False


# ---------------------------------------------------------------------------
# User Authentication & Registration Queries
# ---------------------------------------------------------------------------

def register_user(user_in: UserCreate, db: Session) -> User:
    """Register a new user with a hashed password and dedicated tenant_id."""
    existing_user = db.query(User).filter(
        *tenant_filter(User, user_in.tenant_id),
        User.email == user_in.email,
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists in this workspace/tenant.",
        )

    db_user = User(
        tenant_id=user_in.tenant_id or f"tenant_{secrets.token_hex(6)}",
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role="member",
        is_active=True,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(email: str, password: str, tenant_id: str, db: Session) -> Optional[User]:
    """Verify email and password within the specified tenant workspace."""
    user = db.query(User).filter(*tenant_filter(User, tenant_id), User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated")
    return user
