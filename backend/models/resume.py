from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, generate_uuid, get_utc_now


class TailoredResume(Base):
    __tablename__ = "tailored_resumes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    tenant_id = Column(String(64), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jd_id = Column(String(36), ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    structured_content = Column(JSON, default=dict, nullable=False)  # Full synthesized JSON schema
    raw_latex = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    user = relationship("User", back_populates="tailored_resumes")
    job_description = relationship("JobDescription", back_populates="tailored_resumes")

    __table_args__ = (
        Index("idx_tailored_resumes_tenant_user", "tenant_id", "user_id"),
    )
