from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


class SynthesizedExperience(BaseModel):
    """Experience item tailored specifically to target JD keywords."""
    company: str
    role: str
    duration: Optional[str] = None
    location: Optional[str] = None
    tailored_bullets: List[str]


class TailoredResumeContent(BaseModel):
    """Full structured JSON representation of a synthesized tailored resume."""
    candidate_name: str
    contact_info: Dict[str, Optional[str]]
    professional_summary: str
    highlighted_skills: List[str]
    experiences: List[SynthesizedExperience]
    projects: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []


class TailorRequest(BaseModel):
    """Request payload to initiate AI RAG tailoring pipeline."""
    job_description: str = Field(..., min_length=10, description="Full job description text")
    target_job_title: Optional[str] = Field(None, max_length=150, description="Target job title override")
    top_k_bullets: Optional[int] = Field(None, ge=1, le=50, description="Top-K bullets to retrieve via pgvector RAG")
    master_bullets: Optional[List[str]] = Field(None, description="Direct bullets override bypassing RAG retrieval")

    @model_validator(mode="after")
    def validate_retrieval_strategy(self) -> "TailorRequest":
        if not self.job_description.strip():
            raise ValueError("job_description cannot be empty or whitespace.")

        if self.master_bullets is not None:
            cleaned = [b.strip() for b in self.master_bullets if b and b.strip()]
            self.master_bullets = cleaned if cleaned else None

        # Resolve mutual exclusivity between manual bullets and vector top_k
        if self.master_bullets is not None:
            # If manual bullets are provided, RAG top_k is cleared to avoid ambiguity
            self.top_k_bullets = None
        elif self.top_k_bullets is None:
            # Default to 8 when RAG is active
            self.top_k_bullets = 8

        return self


class TailoredResumeResponse(BaseModel):
    """Final synthesized resume response with ATS match score and LaTeX."""
    id: Optional[str] = None
    job_title: str
    match_score: Optional[float] = None
    matched_keywords: List[str] = []
    missing_keywords: List[str] = []
    structured_resume: TailoredResumeContent
    latex_source: Optional[str] = None


class TailoredResumeModelResponse(BaseModel):
    """Database record response for a saved tailored resume."""
    id: str
    tenant_id: str
    user_id: str
    jd_id: Optional[str] = None
    title: str
    structured_content: Dict[str, Any]
    raw_latex: Optional[str] = None
    match_score: Optional[float] = None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
