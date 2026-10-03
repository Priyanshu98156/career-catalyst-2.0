from typing import Optional, Tuple
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.security import decode_token

# Bearer security scheme for Swagger UI and route protection
security = HTTPBearer(auto_error=False)


def get_tenant_and_user(
    x_tenant_id: Optional[str] = Header("default_tenant", alias="X-Tenant-ID"),
    x_user_id: Optional[str] = Header("default_user", alias="X-User-ID"),
) -> Tuple[str, str]:
    """
    Extract tenant_id and user_id from request headers for multi-tenant isolation.
    Centralized dependency used across all router modules.
    """
    return x_tenant_id or "default_tenant", x_user_id or "default_user"


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


def get_current_user(
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> User:
    """Strict dependency requiring an active authenticated user."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user
