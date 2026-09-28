from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    """Base user data shared across requests."""
    email: EmailStr
    full_name: Optional[str] = None
    tenant_id: str = Field(default="default_tenant", description="Tenant ID for multi-tenant isolation")


class UserCreate(UserBase):
    """Payload required to register a new user."""
    password: str = Field(min_length=6, description="User raw password (will be hashed)")


class UserLogin(BaseModel):
    """Payload required for user authentication."""
    email: EmailStr
    password: str
    tenant_id: str = "default_tenant"


class UserResponse(UserBase):
    """Public user response object."""
    id: str
    is_active: bool
    role: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT response returned upon successful authentication (Access + Refresh)."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    user: Optional[UserResponse] = None


class RefreshTokenRequest(BaseModel):
    """Payload to request a new access token using a refresh token."""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Payload returned upon refreshing tokens."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Payload extracted from decoded JWT access token."""
    email: Optional[str] = None
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    token_type: Optional[str] = None


class MessageResponse(BaseModel):
    """Standard generic success message response."""
    message: str
