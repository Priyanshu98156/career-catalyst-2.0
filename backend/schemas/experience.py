from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class MasterBulletCreate(BaseModel):
    """Payload to create a new quantified achievement / master bullet point."""
    bullet_text: str
    skills_used: List[str] = []
    category: str = "Work Experience"
    project_name: Optional[str] = None
    impact_metrics: Optional[str] = None
    experience_id: Optional[str] = None


class MasterBulletResponse(MasterBulletCreate):
    """Master bullet response from database."""
    id: str
    tenant_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExperienceCreate(BaseModel):
    """Payload to create a work experience / job role with nested bullets."""
    company: str
    role: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool = False
    bullets: List[MasterBulletCreate] = []


class ExperienceResponse(BaseModel):
    """Work experience response including associated master bullets."""
    id: str
    tenant_id: str
    user_id: str
    company: str
    role: str
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    is_current: bool
    bullets: List[MasterBulletResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
