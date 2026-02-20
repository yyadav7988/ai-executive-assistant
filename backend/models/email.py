from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Boolean, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class EmailClassification(str, enum.Enum):
    URGENT = "urgent"
    ACTION_REQUIRED = "action_required"
    FYI = "fyi"
    SPAM = "spam"


class EmailStatus(str, enum.Enum):
    UNPROCESSED = "unprocessed"
    PROCESSED = "processed"
    ARCHIVED = "archived"
    REPLIED = "replied"
    PENDING_APPROVAL = "pending_approval"


class Email(Base):
    __tablename__ = "emails"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Gmail data
    gmail_id = Column(String, nullable=False, unique=True, index=True)
    thread_id = Column(String, nullable=False, index=True)
    subject = Column(String, nullable=False)
    from_email = Column(String, nullable=False, index=True)
    from_name = Column(String, nullable=True)
    body = Column(Text, nullable=False)
    
    # AI processing
    classification = Column(SQLEnum(EmailClassification), nullable=True)
    priority_score = Column(Integer, nullable=True)  # 1-100
    summary = Column(Text, nullable=True)
    
    # Status
    status = Column(SQLEnum(EmailStatus), default=EmailStatus.UNPROCESSED, nullable=False)
    
    # Timestamps
    received_at = Column(DateTime, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="emails")
    actions = relationship("EmailAction", back_populates="email", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Email {self.subject[:30]}>"


class EmailAction(Base):
    __tablename__ = "email_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email_id = Column(UUID(as_uuid=True), ForeignKey("emails.id"), nullable=False, index=True)
    
    # Action details
    action_type = Column(String, nullable=False)  # "reply", "archive", "schedule_meeting"
    draft_reply = Column(Text, nullable=True)
    reply_tone = Column(String, nullable=True)  # "professional", "friendly", "formal"
    
    # Status
    auto_sent = Column(Boolean, default=False, nullable=False)
    approved = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationship
    email = relationship("Email", back_populates="actions")
    
    def __repr__(self):
        return f"<EmailAction {self.action_type}>"
