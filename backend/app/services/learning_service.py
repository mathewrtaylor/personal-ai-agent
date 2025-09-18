# backend/app/services/learning_service.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
import json
import re

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile
from app.models.learning_data import LearningData, ConversationSummary

logger = logging.getLogger(__name__)

class LearningService:
    def __init__(self):
        self.initialized = False
        self.ai_service = None
    
    async def initialize(self):
        """Initialize the learning service"""
        # Import here to avoid circular imports
        from app.services.ai_service import AIService
        self.ai_service = AIService()
        self.initialized = True
        logger.info("Learning Service initialized")
    
    async def process_new_conversations(self, user_id: str, new_conversations: List[Conversation]):
        """Process new conversations to extract learning"""
        if not settings.ENABLE_LEARNING:
            return
        
        if not self.initialized or not self.ai_service.initialized:
            logger.warning("Learning service or AI service not initialized")
            return
        
        db = SessionLocal()
        try:
            # Get user profile
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if not user_profile:
                user_profile = UserProfile(user_id=user_id)
                db.add(user_profile)
                db.commit()
                db.refresh(user_profile)
            
            # Check if we should trigger learning update
            if user_profile.total_messages % settings.LEARNING_UPDATE_INTERVAL == 0:
                await self._perform_learning_update(user_id, db)
            
            # Update basic communication metrics
            self._update_communication_metrics(user_id, new_conversations, db)
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error processing new conversations: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def _perform_learning_update(self, user_id: str, db: Session):
        """Perform comprehensive learning analysis"""
        try:
            # Get recent conversation history
            recent_conversations = db.query(Conversation)\
                .filter(Conversation.user_id == user_id)\
                .order_by(Conversation.timestamp.desc())\
                .limit(20)\
                .all()
            
            if not recent_conversations:
                return
            
            # Analyze conversations with AI
            analysis = await self.ai_service.analyze_for_learning(recent_conversations)
            
            if analysis:
                await self._update_user_profile_from_analysis(user_id, analysis, db)
                await self._store_learning_data(user_id, analysis, recent_conversations[0].id, db)
            
        except Exception as e:
            logger.error(f"Error in learning update: {e}")
    
    async def _update_user_profile_from_analysis(self, user_id: str, analysis: Dict[str, Any], db: Session):
        """Update user profile based on AI analysis"""
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            return
        
        # Update personal facts
        if "personal_facts" in analysis and analysis["personal_facts"]:
            if not user_profile.personal_facts:
                user_profile.personal_facts = {}
            user_profile.personal_facts.update(analysis["personal_facts"])
        
        # Update communication preferences
        if "communication_preferences" in analysis and analysis["communication_preferences"]:
            if not user_profile.communication_preferences:
                user_profile.communication_preferences = {}
            user_profile.communication_preferences.update(analysis["communication_preferences"])
        
        # Update topics of interest
        if "topics_of_interest" in analysis and analysis["topics_of_interest"]:
            existing_topics = set(user_profile.topics_of_interest or [])
            new_topics = set(analysis["topics_of_interest"])
            user_profile.topics_of_interest = list(existing_topics.union(new_topics))
        
        # Update expertise areas
        if "expertise_areas" in analysis and analysis["expertise_areas"]:
            existing_areas = set(user_profile.expertise_areas or [])
            new_areas = set(analysis["expertise_areas"])
            user_profile.expertise_areas = list(existing_areas.union(new_areas))
        
        # Update formality score (weighted average)
        if "formality_score" in analysis:
            current_score = user_profile.formality_score or 0.5
            new_score = float(analysis["formality_score"])
            # Use exponential moving average
            alpha = 0.3  # Learning rate
            user_profile.formality_score = alpha * new_score + (1 - alpha) * current_score
        
        # Update preferred response length
        if "preferred_response_length" in analysis:
            user_profile.preferred_response_length = analysis["preferred_response_length"]
        
        user_profile.last_updated = datetime.utcnow()
    
    async def _store_learning_data(self, user_id: str, analysis: Dict[str, Any], conversation_id: str, db: Session):
        """Store specific learning data points"""
        timestamp = datetime.utcnow()
        
        # Store personal facts
        if "personal_facts" in analysis:
            for key, value in analysis["personal_facts"].items():
                learning_data = LearningData(
                    user_id=user_id,
                    learning_type="personal_fact",
                    key=key,
                    value=str(value),
                    confidence=0.8,
                    source_conversation_id=conversation_id,
                    context=f"Learned from conversation analysis",
                    created_at=timestamp
                )
                db.add(learning_data)
        
        # Store communication preferences
        if "communication_preferences" in analysis:
            for key, value in analysis["communication_preferences"].items():
                learning_data = LearningData(
                    user_id=user_id,
                    learning_type="communication_preference",
                    key=key,
                    value=str(value),
                    confidence=0.7,
                    source_conversation_id=conversation_id,
                    context=f"Inferred communication preference",
                    created_at=timestamp
                )
                db.add(learning_data)
        
        # Store topics of interest
        if "topics_of_interest" in analysis:
            for topic in analysis["topics_of_interest"]:
                learning_data = LearningData(
                    user_id=user_id,
                    learning_type="topic_interest",
                    key="topic",
                    value=str(topic),
                    confidence=0.6,
                    source_conversation_id=conversation_id,
                    context=f"Topic mentioned in conversation",
                    created_at=timestamp
                )
                db.add(learning_data)
    
    def _update_communication_metrics(self, user_id: str, conversations: List[Conversation], db: Session):
        """Update basic communication metrics"""
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if not user_profile:
            return
        
        # Calculate average message length for user messages
        user_messages = [conv for conv in conversations if conv.message_type == "user"]
        if user_messages:
            total_length = sum(len(msg.content) for msg in user_messages)
            avg_length = total_length / len(user_messages)
            
            # Update with exponential moving average
            alpha = 0.2
            current_avg = user_profile.avg_message_length or 0
            user_profile.avg_message_length = alpha * avg_length + (1 - alpha) * current_avg
    
    async def get_learning_summary(self, user_id: str) -> Dict[str, Any]:
        """Get a summary of what has been learned about the user"""
        db = SessionLocal()
        try:
            # Get user profile
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not user_profile:
                return {"error": "No user profile found"}
            
            # Get learning data
            learning_data = db.query(LearningData)\
                .filter(and_(LearningData.user_id == user_id, LearningData.is_active == True))\
                .order_by(LearningData.created_at.desc())\
                .all()
            
            # Organize learning data by type
            learning_by_type = {}
            for data in learning_data:
                if data.learning_type not in learning_by_type:
                    learning_by_type[data.learning_type] = []
                learning_by_type[data.learning_type].append({
                    "key": data.key,
                    "value": data.value,
                    "confidence": data.confidence,
                    "created_at": data.created_at,
                    "times_reinforced": data.times_reinforced
                })
            
            # Build summary
            summary = {
                "user_id": user_id,
                "profile_created": user_profile.created_at,
                "last_updated": user_profile.last_updated,
                "total_messages": user_profile.total_messages,
                "communication_metrics": {
                    "avg_message_length": user_profile.avg_message_length,
                    "formality_score": user_profile.formality_score,
                    "preferred_response_length": user_profile.preferred_response_length
                },
                "personal_facts": user_profile.personal_facts or {},
                "communication_preferences": user_profile.communication_preferences or {},
                "topics_of_interest": user_profile.topics_of_interest or [],
                "expertise_areas": user_profile.expertise_areas or [],
                "learning_data": learning_by_type,
                "learning_stats": {
                    "total_learning_entries": len(learning_data),
                    "learning_types": list(learning_by_type.keys()),
                    "high_confidence_learnings": len([d for d in learning_data if d.confidence > 0.8])
                }
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting learning summary: {e}")
            return {"error": str(e)}
        finally:
            db.close()
    
    async def create_conversation_summary(self, user_id: str, message_count: int = 50):
        """Create a summary of recent conversations"""
        if not self.ai_service or not self.ai_service.initialized:
            logger.warning("AI service not available for summarization")
            return
        
        db = SessionLocal()
        try:
            # Get recent conversations
            conversations = db.query(Conversation)\
                .filter(Conversation.user_id == user_id)\
                .order_by(Conversation.timestamp.desc())\
                .limit(message_count)\
                .all()
            
            if len(conversations) < 10:  # Not enough for meaningful summary
                return
            
            # Build summary prompt
            conversation_text = "\n".join([
                f"{'User' if conv.message_type == 'user' else 'Assistant'}: {conv.content}"
                for conv in reversed(conversations)
            ])
            
            summary_prompt = f"""
            Please provide a concise summary of this conversation, highlighting:
            1. Main topics discussed
            2. Key information shared by the user
            3. Any notable preferences or patterns
            
            Conversation:
            {conversation_text}
            
            Provide a structured summary in 2-3 paragraphs.
            """
            
            # Generate summary
            result = await self.ai_service.generate_response(
                summary_prompt,
                [],
                None,
                "You are a helpful assistant that creates concise conversation summaries."
            )
            
            # Store summary
            start_time = conversations[-1].timestamp
            end_time = conversations[0].timestamp
            
            summary = ConversationSummary(
                user_id=user_id,
                summary=result["content"],
                start_time=start_time,
                end_time=end_time,
                message_count=len(conversations),
                created_at=datetime.utcnow()
            )
            
            db.add(summary)
            db.commit()
            
            logger.info(f"Created conversation summary for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error creating conversation summary: {e}")
        finally:
            db.close()