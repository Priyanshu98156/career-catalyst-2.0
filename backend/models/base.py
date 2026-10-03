import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.orm import declared_attr
from backend.database import Base


def generate_uuid() -> str:
    """Generate RFC 4122 compliant UUID string."""
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def tenant_filter(model: Any, tenant_id: str, user_id: Optional[str] = None) -> List[Any]:
    """
    Construct standardized tenant and user isolation clauses for SQLAlchemy filter queries.
    Prevents cross-tenant data leaks and eliminates repetitive filter boilerplate (DRY-8).
    """
    clauses = [model.tenant_id == tenant_id]
    if user_id is not None and hasattr(model, "user_id"):
        clauses.append(model.user_id == user_id)
    return clauses


class TimestampMixin:
    """Audit timestamps for model creation and updates."""
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)


class TenantMixin(TimestampMixin):
    """Core multi-tenant entity mixin with UUID primary key, tenant boundary, and audit timestamps (DRY-10)."""
    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=False, index=True)


class UserTenantMixin(TenantMixin):
    """Mixin for multi-tenant entities belonging to a specific candidate user within a tenant (DRY-10)."""
    @declared_attr
    def user_id(cls):
        return Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
