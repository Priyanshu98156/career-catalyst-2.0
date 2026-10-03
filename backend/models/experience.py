from sqlalchemy import Boolean, Column, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, UserTenantMixin


class Experience(Base, UserTenantMixin):
    """Stores candidate past work history / companies."""
    __tablename__ = "experiences"

    company = Column(String(255), nullable=False)
    role = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    is_current = Column(Boolean, default=False, nullable=False)

    # Bidirectional link to User: user.experiences <-> experience.user
    user = relationship("User", back_populates="experiences")
    
    # One-to-Many link to MasterBullet: deleting an Experience deletes its attached bullets (cascade)
    bullets = relationship("MasterBullet", back_populates="experience", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_experiences_tenant_user", "tenant_id", "user_id"),
    )


class MasterBullet(Base, UserTenantMixin):
    """Stores individual quantified achievements / project bullet points."""
    __tablename__ = "master_bullets"

    experience_id = Column(String(36), ForeignKey("experiences.id", ondelete="SET NULL"), nullable=True, index=True)
    
    project_name = Column(String(255), nullable=True)
    bullet_text = Column(Text, nullable=False)
    skills_used = Column(JSON, default=list, nullable=False)  # List[str]
    category = Column(String(100), default="Work Experience", nullable=False)  # e.g., "Work Experience", "Project"
    impact_metrics = Column(String(255), nullable=True)

    # Bidirectional link to User: user.master_bullets <-> master_bullet.user
    user = relationship("User", back_populates="master_bullets")
    
    # Bidirectional link to Experience: experience.bullets <-> master_bullet.experience
    experience = relationship("Experience", back_populates="bullets")

    __table_args__ = (
        Index("idx_master_bullets_tenant_user", "tenant_id", "user_id"),
    )
