from sqlalchemy import Column, Index, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, UserTenantMixin


class Profile(Base, UserTenantMixin):
    __tablename__ = "profiles"

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

    # Relationship
    user = relationship("User", back_populates="profiles")

    __table_args__ = (
        Index("idx_profiles_tenant_user", "tenant_id", "user_id"),
    )
