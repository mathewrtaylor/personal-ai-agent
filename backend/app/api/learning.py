# backend/app/api/learning.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.user_profile import UserProfile
from app.models.learning_data import LearningData, ConversationSummary
from app.services.learning_service import LearningService

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models
class LearningFeedback(BaseModel):
    message_id: str
    helpful: bool
    feedback_text: Optional[str] = None

class UserProfileResponse(BaseModel):
    user_id: str
    total_messages: int
    communication_metrics: dict
    personal_facts: dict
    communication_preferences: dict
    topics_of_interest: List[str]
    expertise_areas: List[str]
    profile_created: datetime
    last_updated: datetime

# Dependency injection
learning_service = LearningService()

@router.get("/profile")
async def get_user_profile(
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """Get the learned user profile and learning summary"""
    try:
        # Get learning summary from service
        summary = await learning_service.get_learning_summary(user_id)
        
        if "error" in summary:
            if "No user profile found" in summary["error"]:
                return {
                    "user_id": user_id,
                    "profile_exists": False,
                    "message": "No profile found. Start chatting to build your profile!",
                    "total_messages": 0,
                    "communication_metrics": {},
                    "personal_facts": {},
                    "communication_preferences": {},
                    "topics_of_interest": [],
                    "expertise_areas": []
                }
            else:
                raise HTTPException(status_code=500, detail=summary["error"])
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/feedback")
async def submit_feedback(
    feedback: LearningFeedback,
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """Submit feedback on AI responses to improve learning"""
    try:
        # Store feedback as learning data
        feedback_data = LearningData(
            user_id=user_id,
            learning_type="feedback",
            key="response_quality",
            value="helpful" if feedback.helpful else "not_helpful",
            confidence=1.0,
            source_conversation_id=feedback.message_id,
            context=feedback.feedback_text or "User feedback on response quality",
            created_at=datetime.utcnow()
        )
        
        db.add(feedback_data)
        db.commit()
        
        return {
            "message": "Feedback recorded successfully",
            "feedback_id": str(feedback_data.id)
        }
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_learning_stats(
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """Get learning statistics and insights"""
    try:
        # Get user profile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        
        if not user_profile:
            return {
                "user_id": user_id,
                "profile_exists": False,
                "total_learning_entries": 0,
                "learning_types": [],
                "confidence_distribution": {}
            }
        
        # Get learning data statistics
        learning_data = db.query(LearningData)\
            .filter(LearningData.user_id == user_id)\
            .filter(LearningData.is_active == True)\
            .all()
        
        # Calculate statistics
        learning_types = {}
        confidence_distribution = {"high": 0, "medium": 0, "low": 0}
        
        for data in learning_data:
            # Count by type
            learning_types[data.learning_type] = learning_types.get(data.learning_type, 0) + 1
            
            # Count by confidence
            if data.confidence > 0.7:
                confidence_distribution["high"] += 1
            elif data.confidence > 0.4:
                confidence_distribution["medium"] += 1
            else:
                confidence_distribution["low"] += 1
        
        # Get conversation summaries
        summaries = db.query(ConversationSummary)\
            .filter(ConversationSummary.user_id == user_id)\
            .order_by(ConversationSummary.created_at.desc())\
            .limit(5)\
            .all()
        
        return {
            "user_id": user_id,
            "profile_exists": True,
            "total_learning_entries": len(learning_data),
            "learning_types": learning_types,
            "confidence_distribution": confidence_distribution,
            "recent_summaries": [
                {
                    "summary": summary.summary,
                    "period": f"{summary.start_time.strftime('%Y-%m-%d')} to {summary.end_time.strftime('%Y-%m-%d')}",
                    "message_count": summary.message_count,
                    "created_at": summary.created_at
                }
                for summary in summaries
            ],
            "profile_metrics": {
                "total_messages": user_profile.total_messages,
                "avg_message_length": user_profile.avg_message_length,
                "formality_score": user_profile.formality_score,
                "topics_count": len(user_profile.topics_of_interest or []),
                "facts_count": len(user_profile.personal_facts or {}),
                "preferences_count": len(user_profile.communication_preferences or {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting learning stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/trigger-update")
async def trigger_learning_update(
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """Manually trigger a learning update (useful for testing)"""
    try:
        from app.models.conversation import Conversation
        
        # Get recent conversations
        recent_conversations = db.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .order_by(Conversation.timestamp.desc())\
            .limit(10)\
            .all()
        
        if not recent_conversations:
            return {
                "message": "No conversations found to analyze",
                "user_id": user_id
            }
        
        # Process conversations for learning
        await learning_service.process_new_conversations(user_id, recent_conversations)
        
        return {
            "message": "Learning update triggered successfully",
            "user_id": user_id,
            "analyzed_messages": len(recent_conversations)
        }
        
    except Exception as e:
        logger.error(f"Error triggering learning update: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-summary")
async def create_conversation_summary(
    user_id: str = "default_user",
    message_count: int = 50
):
    """Create a summary of recent conversations"""
    try:
        await learning_service.create_conversation_summary(user_id, message_count)
        
        return {
            "message": "Conversation summary created successfully",
            "user_id": user_id,
            "analyzed_messages": message_count
        }
        
    except Exception as e:
        logger.error(f"Error creating conversation summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reset-profile")
async def reset_user_profile(
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """Reset user profile and learning data (useful for testing)"""
    try:
        # Delete learning data
        deleted_learning = db.query(LearningData)\
            .filter(LearningData.user_id == user_id)\
            .delete()
        
        # Delete conversation summaries
        deleted_summaries = db.query(ConversationSummary)\
            .filter(ConversationSummary.user_id == user_id)\
            .delete()
        
        # Reset user profile
        user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if user_profile:
            user_profile.personal_facts = {}
            user_profile.communication_preferences = {}
            user_profile.topics_of_interest = []
            user_profile.expertise_areas = []
            user_profile.formality_score = 0.5
            user_profile.avg_message_length = 0.0
            user_profile.preferred_response_length = "medium"
            user_profile.last_updated = datetime.utcnow()
        
        db.commit()
        
        return {
            "message": "User profile and learning data reset successfully",
            "user_id": user_id,
            "deleted_learning_entries": deleted_learning,
            "deleted_summaries": deleted_summaries,
            "profile_reset": bool(user_profile)
        }
        
    except Exception as e:
        logger.error(f"Error resetting user profile: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/learning-history")
async def get_learning_history(
    user_id: str = "default_user",
    limit: int = 50,
    learning_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get detailed learning history"""
    try:
        query = db.query(LearningData)\
            .filter(LearningData.user_id == user_id)\
            .filter(LearningData.is_active == True)
        
        if learning_type:
            query = query.filter(LearningData.learning_type == learning_type)
        
        learning_data = query.order_by(LearningData.created_at.desc())\
            .limit(limit)\
            .all()
        
        return {
            "user_id": user_id,
            "total_entries": len(learning_data),
            "filter_type": learning_type,
            "learning_history": [
                {
                    "id": str(data.id),
                    "type": data.learning_type,
                    "key": data.key,
                    "value": data.value,
                    "confidence": data.confidence,
                    "context": data.context,
                    "created_at": data.created_at,
                    "times_reinforced": data.times_reinforced,
                    "last_reinforced": data.last_reinforced
                }
                for data in learning_data
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting learning history: {e}")
        raise HTTPException(status_code=500, detail=str(e))