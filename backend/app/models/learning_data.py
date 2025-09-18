# backend/app/models/learning_data.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base

class LearningData(Base):
    __tablename__ = "learning_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False, index=True)
    
    # What was learned
    learning_type = Column(String(50), nullable=False, index=True)  # Type of learning
    category = Column(String(50), default="general")  # Sub-category for organization
    key = Column(String(100), nullable=False)  # The specific attribute learned
    value = Column(Text, nullable=False)  # The learned value
    confidence = Column(Float, default=0.5, nullable=False)  # Confidence in this learning (0-1)
    
    # Context and source
    source_conversation_id = Column(UUID(as_uuid=True), nullable=True)  # Which conversation taught us this
    context = Column(Text, nullable=True)  # Additional context about how this was learned
    extraction_method = Column(String(50), default="ai_analysis")  # How this was extracted
    
    # Validation and reinforcement
    times_observed = Column(Integer, default=1)  # How many times we've seen evidence of this
    times_reinforced = Column(Integer, default=0)  # How many times this was confirmed
    times_contradicted = Column(Integer, default=0)  # How many times this was contradicted
    last_observed = Column(DateTime, default=datetime.utcnow)  # When we last saw evidence
    last_reinforced = Column(DateTime, default=datetime.utcnow)  # When this was last confirmed
    
    # metadatas
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status and lifecycle
    is_active = Column(Boolean, default=True, nullable=False)  # Whether this learning is still considered valid
    is_validated = Column(Boolean, default=False)  # Whether this has been validated
    superseded_by = Column(UUID(as_uuid=True), nullable=True)  # If replaced by newer learning
    validation_score = Column(Float, default=0.0)  # Score based on reinforcement vs contradiction
    
    # Additional metadatas
    importance_score = Column(Float, default=0.5)  # How important this learning is (0-1)
    tags = Column(JSONB, default=list)  # Tags for categorization
    related_learnings = Column(JSONB, default=list)  # IDs of related learning entries
    
    def __repr__(self):
        return f"<LearningData(type='{self.learning_type}', key='{self.key}', confidence={self.confidence:.2f}, active={self.is_active})>"
    
    def to_dict(self):
        """Convert learning data to dictionary"""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "learning_type": self.learning_type,
            "category": self.category,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "source_conversation_id": str(self.source_conversation_id) if self.source_conversation_id else None,
            "context": self.context,
            "extraction_method": self.extraction_method,
            "validation": {
                "times_observed": self.times_observed,
                "times_reinforced": self.times_reinforced,
                "times_contradicted": self.times_contradicted,
                "last_observed": self.last_observed,
                "last_reinforced": self.last_reinforced,
                "is_validated": self.is_validated,
                "validation_score": self.validation_score
            },
            "metadatas": {
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "is_active": self.is_active,
                "importance_score": self.importance_score,
                "tags": self.tags or [],
                "related_learnings": self.related_learnings or []
            }
        }
    
    def reinforce(self, new_confidence: float = None):
        """Reinforce this learning data point"""
        self.times_reinforced += 1
        self.times_observed += 1
        self.last_reinforced = datetime.utcnow()
        self.last_observed = datetime.utcnow()
        
        if new_confidence is not None:
            # Update confidence using weighted average
            weight = min(self.times_reinforced / 10.0, 0.5)  # Max weight of 50%
            self.confidence = weight * new_confidence + (1 - weight) * self.confidence
        else:
            # Increase confidence slightly with reinforcement
            self.confidence = min(self.confidence * 1.1, 1.0)
        
        self.validation_score = self._calculate_validation_score()
        self.updated_at = datetime.utcnow()
    
    def contradict(self):
        """Mark this learning as contradicted"""
        self.times_contradicted += 1
        self.times_observed += 1
        self.last_observed = datetime.utcnow()
        
        # Decrease confidence when contradicted
        contradiction_penalty = 0.2
        self.confidence = max(self.confidence - contradiction_penalty, 0.1)
        
        self.validation_score = self._calculate_validation_score()
        
        # Deactivate if contradicted too many times relative to reinforcements
        if self.times_contradicted > self.times_reinforced + 2:
            self.is_active = False
        
        self.updated_at = datetime.utcnow()
    
    def _calculate_validation_score(self) -> float:
        """Calculate validation score based on reinforcement vs contradiction"""
        total_feedback = self.times_reinforced + self.times_contradicted
        if total_feedback == 0:
            return 0.0
        
        # Score based on ratio of reinforcements to total feedback
        reinforcement_ratio = self.times_reinforced / total_feedback
        
        # Bonus for multiple observations
        observation_bonus = min(self.times_observed / 10.0, 0.2)
        
        return min(reinforcement_ratio + observation_bonus, 1.0)
    
    def supersede_with(self, new_learning_id: uuid.UUID):
        """Mark this learning as superseded by a newer one"""
        self.is_active = False
        self.superseded_by = new_learning_id
        self.updated_at = datetime.utcnow()


class ConversationSummary(Base):
    __tablename__ = "conversation_summaries"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False, index=True)
    
    # Summary content
    title = Column(String(200), nullable=True)  # Brief title for the summary
    summary = Column(Text, nullable=False)  # Human-readable summary
    key_topics = Column(JSONB, default=list)  # Main topics discussed
    important_facts = Column(JSONB, default=list)  # Important facts learned
    insights = Column(JSONB, default=list)  # Insights or patterns discovered
    
    # Time period and scope
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    message_count = Column(Integer, nullable=False)
    conversation_ids = Column(JSONB, default=list)  # IDs of conversations included
    
    # Summary metadatas
    summary_type = Column(String(50), default="automatic")  # automatic, manual, periodic, triggered
    summarization_method = Column(String(50), default="ai_generated")  # How summary was created
    confidence_score = Column(Float, default=0.5)  # Confidence in summary accuracy
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    def __repr__(self):
        period = f"{self.start_time.date()} to {self.end_time.date()}"
        return f"<ConversationSummary(user='{self.user_id}', period='{period}', messages={self.message_count})>"
    
    def to_dict(self):
        """Convert summary to dictionary"""
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "title": self.title,
            "summary": self.summary,
            "key_topics": self.key_topics or [],
            "important_facts": self.important_facts or [],
            "insights": self.insights or [],
            "period": {
                "start_time": self.start_time,
                "end_time": self.end_time,
                "message_count": self.message_count,
                "conversation_ids": self.conversation_ids or []
            },
            "metadatas": {
                "summary_type": self.summary_type,
                "summarization_method": self.summarization_method,
                "confidence_score": self.confidence_score,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
                "is_active": self.is_active,
                "is_archived": self.is_archived
            }
        }


class LearningSession(Base):
    __tablename__ = "learning_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(50), nullable=False, index=True)
    
    # Session details
    session_type = Column(String(50), default="conversation_analysis")  # Type of learning session
    trigger = Column(String(100), nullable=True)  # What triggered this learning session
    
    # Processing details
    conversations_analyzed = Column(Integer, default=0)
    learning_entries_created = Column(Integer, default=0)
    learning_entries_updated = Column(Integer, default=0)
    processing_time_seconds = Column(Float, default=0.0)
    
    # Results
    insights_discovered = Column(JSONB, default=list)
    patterns_identified = Column(JSONB, default=list)
    confidence_changes = Column(JSONB, default=dict)  # Track confidence changes
    
    # Status
    status = Column(String(50), default="completed")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<LearningSession(user='{self.user_id}', type='{self.session_type}', status='{self.status}')>"
    
    def complete_session(self, insights: list = None, patterns: list = None):
        """Mark session as completed"""
        self.status = "completed"
        self.completed_at = datetime.utcnow()
        if insights:
            self.insights_discovered = insights
        if patterns:
            self.patterns_identified = patterns
    
    def fail_session(self, error: str):
        """Mark session as failed"""
        self.status = "failed"
        self.completed_at = datetime.utcnow()
        self.error_message = error