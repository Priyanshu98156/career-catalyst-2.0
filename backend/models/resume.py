from sqlalchemy import Column, Float, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, UserTenantMixin


class TailoredResume(Base, UserTenantMixin):
    __tablename__ = "tailored_resumes"

    jd_id = Column(String(36), ForeignKey("job_descriptions.id", ondelete="SET NULL"), nullable=True, index=True)
    
    title = Column(String(255), nullable=False)
    structured_content = Column(JSON, default=dict, nullable=False)  # Full synthesized JSON schema
    raw_latex = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    version = Column(Integer, default=1, nullable=False)

    # Relationships
    user = relationship("User", back_populates="tailored_resumes")
    job_description = relationship("JobDescription", back_populates="tailored_resumes")

    __table_args__ = (
        Index("idx_tailored_resumes_tenant_user", "tenant_id", "user_id"),
    )
