from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, generate_uuid, get_utc_now


class Experience(Base):
    """Stores candidate past work history / companies."""
    __tablename__ = "experiences"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Bidirectional link to User: user.experiences <-> experience.user
    user = relationship("User", back_populates="experiences")
    
    # One-to-Many link to MasterBullet: deleting an Experience deletes its attached bullets (cascade)
    bullets = relationship("MasterBullet", back_populates="experience", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_experiences_tenant_user", "tenant_id", "user_id"),
    )


class MasterBullet(Base):
    """Stores individual quantified achievements / project bullet points."""
    __tablename__ = "master_bullets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    experience_id = Column(String(36), ForeignKey("experiences.id", ondelete="SET NULL"), nullable=True, index=True)
    
    project_name = Column(String(255), nullable=True)
    bullet_text = Column(Text, nullable=False)
    skills_used = Column(JSON, default=list, nullable=False)  # List[str]
    category = Column(String(100), default="Work Experience", nullable=False)  # e.g., "Work Experience", "Project"
    impact_metrics = Column(String(255), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Bidirectional link to User: user.master_bullets <-> master_bullet.user
    user = relationship("User", back_populates="master_bullets")
    
    # Bidirectional link to Experience: experience.bullets <-> master_bullet.experience
    experience = relationship("Experience", back_populates="bullets")

    __table_args__ = (
        Index("idx_master_bullets_tenant_user", "tenant_id", "user_id"),
    )
