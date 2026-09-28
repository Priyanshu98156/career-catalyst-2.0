from backend.models.base import Base, generate_uuid, get_utc_now
from backend.models.user import User
from backend.models.profile import Profile
from backend.models.experience import Experience, MasterBullet
from backend.models.job import JobDescription
from backend.models.resume import TailoredResume

# Re-export schemas for convenience and backward compatibility
from backend.schemas import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
    ParsedProfile,
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    ExperienceCreate,
    ExperienceResponse,
    MasterBulletCreate,
    MasterBulletResponse,
    JDAnalysis,
    JDAnalysisRequest,
    TailorRequest,
    TailoredResumeResponse,
    TailoredResumeContent,
)

__all__ = [
    "Base",
    "generate_uuid",
    "get_utc_now",
    "User",
    "Profile",
    "Experience",
    "MasterBullet",
    "JobDescription",
    "TailoredResume",
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    "ParsedProfile",
    "ProfileCreate",
    "ProfileUpdate",
    "ProfileResponse",
    "ExperienceCreate",
    "ExperienceResponse",
    "MasterBulletCreate",
    "MasterBulletResponse",
    "JDAnalysis",
    "JDAnalysisRequest",
    "TailorRequest",
    "TailoredResumeResponse",
    "TailoredResumeContent",
]
