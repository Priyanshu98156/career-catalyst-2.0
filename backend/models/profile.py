from sqlalchemy import Column, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, generate_uuid, get_utc_now


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    github_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    summary = Column(Text, nullable=True)
    skills = Column(JSON, default=list, nullable=False)  # List[str] or Dict
    education = Column(JSON, default=list, nullable=False)  # List[Dict]
    certifications = Column(JSON, default=list, nullable=False)  # List[Dict]
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationship
    user = relationship("User", back_populates="profiles")

    __table_args__ = (
        Index("idx_profiles_tenant_user", "tenant_id", "user_id"),
    )
