from sqlalchemy import Boolean, Column, Index, String
from sqlalchemy.orm import relationship
from backend.models.base import Base, TenantMixin


class User(Base, TenantMixin):
    __tablename__ = "users"

    email = Column(String(255), nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    role = Column(String(50), default="member", nullable=False)

    # Relationships
    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="user", cascade="all, delete-orphan")
    master_bullets = relationship("MasterBullet", back_populates="user", cascade="all, delete-orphan")
    job_descriptions = relationship("JobDescription", back_populates="user", cascade="all, delete-orphan")
    tailored_resumes = relationship("TailoredResume", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_tenant_email", "tenant_id", "email", unique=True),
    )
