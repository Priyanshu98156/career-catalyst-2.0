from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr


class EducationItem(BaseModel):
    """Academic degree / institution record."""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    gpa: Optional[str] = None


class CertificationItem(BaseModel):
    """Professional certification record."""
    name: str
    issuer: str
    issue_date: Optional[str] = None
    credential_url: Optional[str] = None


class ProjectItem(BaseModel):
    """Portfolio / personal project entry."""
    title: str
    description: Optional[str] = None
    technologies: List[str] = []
    bullet_points: List[str] = []
    link: Optional[str] = None


class ParsedExperienceItem(BaseModel):
    """Work experience item extracted from a candidate resume."""
    company: str
    role: str
    duration: Optional[str] = None
    location: Optional[str] = None
    bullet_points: List[str] = []
    skills_used: List[str] = []


class ParsedProfile(BaseModel):
    """Output schema for resume document (PDF/DOCX) extraction via Gemini."""
    full_name: str
    email: str
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    education: List[EducationItem] = []
    experiences: List[ParsedExperienceItem] = []
    projects: List[ProjectItem] = []
    certifications: List[CertificationItem] = []


class ProfileCreate(BaseModel):
    """Payload to create or initialize a candidate profile."""
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    education: List[Dict[str, Any]] = []
    certifications: List[Dict[str, Any]] = []


class ProfileUpdate(BaseModel):
    """Payload to partially update candidate profile details."""
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[str]] = None
    education: Optional[List[Dict[str, Any]]] = None
    certifications: Optional[List[Dict[str, Any]]] = None


class ProfileResponse(ProfileCreate):
    """Complete candidate profile response from database."""
    id: str
    tenant_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
