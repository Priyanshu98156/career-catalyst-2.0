import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.config import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_SECRET_KEY,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from backend.database import get_db
from backend.models import RefreshToken, User
from backend.schemas.auth import TokenData, UserCreate

# Security bearer scheme for FastAPI Swagger docs and route protection
security = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# Password Hashing & Verification (PBKDF2-HMAC-SHA256)
# ---------------------------------------------------------------------------

def hash_password(password: str) -> str:
    """Hash a password using salted PBKDF2-HMAC-SHA256."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations=100_000,
    )
    return f"{salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against the stored salt$hash."""
    try:
        salt, key = hashed_password.split("$", 1)
        expected_key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt.encode("utf-8"),
            iterations=100_000,
        )
        return hmac.compare_digest(expected_key.hex(), key)
    except Exception:
        return False


def hash_token(token: str) -> str:
    """Compute a SHA-256 hash of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# JWT Token Generation & Verification (Double Token Strategy)
# ---------------------------------------------------------------------------

def create_access_token(user_id: str, tenant_id: str, email: str) -> str:
    """Generate a short-lived Access Token (default 15 minutes)."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": email,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_refresh_token(user_id: str, tenant_id: str, db: Session) -> str:
    """Generate a long-lived Refresh Token (default 7 days) and save its hash in DB."""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_hex(16)
    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "type": "refresh",
        "jti": jti,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    raw_token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

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


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token's signature and expiration."""
    try:
        return jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


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
        User.tenant_id == user_in.tenant_id,
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
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated")
    return user


# ---------------------------------------------------------------------------
# FastAPI Auth Dependency (Supports Bearer JWT with graceful fallback)
# ---------------------------------------------------------------------------

def get_current_user_optional(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Extract current authenticated user if Bearer token is provided."""
    if not auth or not auth.credentials:
        return None
    try:
        payload = decode_token(auth.credentials)
        if payload.get("type") != "access":
            return None
        user_id = payload.get("sub")
        return db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
    except Exception:
        return None
