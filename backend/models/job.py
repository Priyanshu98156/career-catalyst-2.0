from sqlalchemy import Column, DateTime, ForeignKey, Index, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, generate_uuid, get_utc_now


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=False)
    primary_skills = Column(JSON, default=list, nullable=False)
    responsibilities = Column(JSON, default=list, nullable=False)
    keywords = Column(JSON, default=list, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="job_descriptions")
    tailored_resumes = relationship("TailoredResume", back_populates="job_description", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_job_descriptions_tenant_user", "tenant_id", "user_id"),
    )
