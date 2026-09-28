from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict


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
    job_description: str
    target_job_title: Optional[str] = None
    top_k_bullets: int = 8
    master_bullets: Optional[List[str]] = None


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
