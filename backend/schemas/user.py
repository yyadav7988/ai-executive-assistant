from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.user import AutomationLevel


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    google_id: str
    access_token: str
    refresh_token: str
    token_expiry: datetime


class UserUpdate(BaseModel):
    automation_level: Optional[AutomationLevel] = None
    onboarding_completed: Optional[bool] = None


class UserResponse(UserBase):
    id: UUID
    google_id: str
    automation_level: AutomationLevel
    onboarding_completed: bool
    created_at: datetime
    last_sync: Optional[datetime]
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
