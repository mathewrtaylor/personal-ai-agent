# backend/app/models/user_profile.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB, UUID
from datetime import datetime
import uuid

from app.core.database import Base

class UserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, default="default_user", unique=True)
    
    # Personal information learned from conversations
    personal_facts = Column(JSONB, default={})  # Name, interests, job, etc.
    communication_preferences = Column(JSONB, default={})  # Tone, length, formality
    topics_of_interest = Column(JSONB, default=[])
    expertise_areas = Column(JSONB, default=[])
    
    # Communication style metrics
    avg_message_length = Column(Float, default=0.0)
    formality_score = Column(Float, default=0.5)  # 0=very casual, 1=very formal
    preferred_response_length = Column(String, default="medium")  # short, medium, long
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_interaction = Column(DateTime, default=datetime.utcnow)
    
    # Statistics
    total_messages = Column(Integer, default=0)
    total_conversations = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<UserProfile(user_id={self.user_id}, messages={self.total_messages})>"