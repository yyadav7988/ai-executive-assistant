from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

from app.models.email import EmailClassification, EmailStatus


class EmailBase(BaseModel):
    subject: str
    from_email: EmailStr
    from_name: Optional[str] = None
    body: str


class EmailCreate(EmailBase):
    gmail_id: str
    thread_id: str
    received_at: datetime
    user_id: UUID


class EmailResponse(EmailBase):
    id: UUID
    gmail_id: str
    thread_id: str
    classification: Optional[EmailClassification]
    priority_score: Optional[int]
    summary: Optional[str]
    status: EmailStatus
    received_at: datetime
    processed_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmailActionCreate(BaseModel):
    email_id: UUID
    action_type: str
    draft_reply: Optional[str] = None
    reply_tone: Optional[str] = None


class EmailActionResponse(BaseModel):
    id: UUID
    email_id: UUID
    action_type: str
    draft_reply: Optional[str]
    reply_tone: Optional[str]
    auto_sent: bool
    approved: bool
    created_at: datetime
    sent_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class EmailWithActions(EmailResponse):
    actions: list[EmailActionResponse] = []
