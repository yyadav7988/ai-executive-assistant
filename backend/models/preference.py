from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.database import Base


class Preference(Base):
    __tablename__ = "preferences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Preference key-value
    key = Column(String, nullable=False, index=True)
    value = Column(JSON, nullable=False)
    
    # Timestamp
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<Preference {self.key}>"


class MemoryEntry(Base):
    __tablename__ = "memory_entries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Memory data
    entry_type = Column(String, nullable=False, index=True)  # "writing_style", "contact", "pattern"
    content = Column(String, nullable=False)
    metadata = Column(JSON, nullable=True)
    
    # For future vector search (embeddings)
    # embedding = Column(Vector(1536), nullable=True)  # Requires pgvector extension
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationship
    user = relationship("User", back_populates="memory_entries")
    
    def __repr__(self):
        return f"<MemoryEntry {self.entry_type}>"
