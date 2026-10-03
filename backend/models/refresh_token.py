from sqlalchemy import Boolean, Column, DateTime, Index, String
from sqlalchemy.orm import relationship
from backend.models.base import Base, UserTenantMixin


class RefreshToken(Base, UserTenantMixin):
    __tablename__ = "refresh_tokens"

    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_token_lookup", "token_hash", "revoked"),
    )
