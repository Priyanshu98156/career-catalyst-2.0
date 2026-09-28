from typing import List, Optional
from pydantic import BaseModel


class JDAnalysis(BaseModel):
    """Structured extraction of target job description requirements via Gemini."""
    job_title: str
    company: Optional[str] = None
    primary_skills: List[str] = []
    core_responsibilities: List[str] = []
    keywords_to_target: List[str] = []
    seniority_level: Optional[str] = None


class JDAnalysisRequest(BaseModel):
    """Payload to request automated analysis of a job description."""
    job_description: str
    job_title: Optional[str] = None
    company: Optional[str] = None
