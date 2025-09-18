# backend/app/models/conversation.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
import uuid

from app.core.database import Base

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, default="default_user")  # For multi-user support later
    message_type = Column(String)  # "user" or "assistant"
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSONB, default={})  # Changed from metadata to message_metadata
    
    # Learning-related fields
    importance_score = Column(Float, default=0.0)  # How important this message is for learning
    contains_personal_info = Column(Boolean, default=False)
    topics = Column(JSONB, default=[])  # Extracted topics from this message
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, type={self.message_type}, timestamp={self.timestamp})>"
