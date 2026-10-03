from sqlalchemy import Column, Index, JSON, String, Text
from sqlalchemy.orm import relationship
from backend.models.base import Base, UserTenantMixin


class JobDescription(Base, UserTenantMixin):
    __tablename__ = "job_descriptions"

    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    raw_text = Column(Text, nullable=False)
    primary_skills = Column(JSON, default=list, nullable=False)
    responsibilities = Column(JSON, default=list, nullable=False)
    keywords = Column(JSON, default=list, nullable=False)

    # Relationships
    user = relationship("User", back_populates="job_descriptions")
    tailored_resumes = relationship("TailoredResume", back_populates="job_description", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_job_descriptions_tenant_user", "tenant_id", "user_id"),
    )
