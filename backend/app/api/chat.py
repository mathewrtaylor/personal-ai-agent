# backend/app/api/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic models for request/response
class ChatMessage(BaseModel):
    content: str
    user_id: Optional[str] = "default_user"

class ChatResponse(BaseModel):
    response: str
    message_id: str
    model: str
    provider: str
    timestamp: datetime
    metadata: dict = {}

class ConversationHistory(BaseModel):
    id: str
    message_type: str
    content: str
    timestamp: datetime
    metadata: dict = {}

@router.post("/warmup")
async def warmup_model(request: Request):
    """Warm up the AI model to reduce response time for next request"""
    try:
        # Get AI service from app state
        ai_service = request.app.state.ai_service
        
        if not ai_service.initialized:
            return {"status": "not_ready", "message": "AI service not initialized"}
        
        # Send minimal request to warm up the model
        warmup_response = await ai_service.generate_response(
            ".", # Minimal prompt
            [],  # No history
            None, # No profile
            "You are a helpful assistant. Respond with just 'ok'." # Simple system prompt
        )
        
        return {
            "status": "warmed",
            "message": "Model warmed up successfully",
            "time_taken": warmup_response.get("metadata", {}).get("total_duration", "unknown")
        }
        
    except Exception as e:
        logger.warning(f"Warmup failed but continuing: {e}")
        return {"status": "failed", "message": str(e)}

@router.post("/message", response_model=ChatResponse)
async def send_message(
    message: ChatMessage,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db)
):
    """Send a message to the AI agent and get a response"""
    try:
        # Get services from app state
        ai_service = request.app.state.ai_service
        learning_service = request.app.state.learning_service
        
        # Check if AI service is initialized
        if not ai_service.initialized:
            raise HTTPException(status_code=503, detail="AI Service not ready yet, please try again")
        
        # Store user message
        user_conversation = Conversation(
            user_id=message.user_id,
            message_type="user",
            content=message.content,
            timestamp=datetime.utcnow()
        )
        db.add(user_conversation)
        db.commit()
        db.refresh(user_conversation)
        
        # Get conversation history for context
        conversation_history = db.query(Conversation)\
            .filter(Conversation.user_id == message.user_id)\
            .order_by(Conversation.timestamp.desc())\
            .limit(50)\
            .all()
        conversation_history.reverse()  # Chronological order
        
        # Get user profile for personalization
        user_profile = db.query(UserProfile)\
            .filter(UserProfile.user_id == message.user_id)\
            .first()
        
        # Generate AI response
        ai_response = await ai_service.generate_response(
            message.content,
            conversation_history,
            user_profile
        )
        
        # Store AI response
        ai_conversation = Conversation(
            user_id=message.user_id,
            message_type="assistant",
            content=ai_response["content"],
            timestamp=datetime.utcnow(),
            message_metadata=ai_response.get("metadata", {})  # Updated to message_metadata
        )
        db.add(ai_conversation)
        db.commit()
        db.refresh(ai_conversation)
        
        # Update user profile stats
        if user_profile:
            user_profile.total_messages += 1
            user_profile.last_interaction = datetime.utcnow()
        else:
            # Create new profile
            user_profile = UserProfile(
                user_id=message.user_id,
                total_messages=1,
                last_interaction=datetime.utcnow()
            )
            db.add(user_profile)
        
        db.commit()
        
        # Schedule learning update in background
        background_tasks.add_task(
            update_learning,
            learning_service,
            message.user_id,
            [user_conversation, ai_conversation]
        )
        
        return ChatResponse(
            response=ai_response["content"],
            message_id=str(ai_conversation.id),
            model=ai_response["model"],
            provider=ai_response["provider"],
            timestamp=ai_conversation.timestamp,
            metadata=ai_response.get("metadata", {})
        )
        
    except Exception as e:
        logger.error(f"Error in send_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[ConversationHistory])
async def get_conversation_history(
    user_id: str = "default_user",
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get conversation history for a user"""
    try:
        conversations = db.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .order_by(Conversation.timestamp.desc())\
            .offset(offset)\
            .limit(limit)\
            .all()
        
        result = []
        for conv in reversed(conversations):  # Return in chronological order
            # Safely handle message_metadata - ensure it's always a dict
            metadata = {}
            if conv.message_metadata:  # Updated to message_metadata
                if isinstance(conv.message_metadata, dict):
                    metadata = conv.message_metadata
                else:
                    # Convert other types to dict or use empty dict
                    try:
                        metadata = dict(conv.message_metadata) if conv.message_metadata else {}
                    except (TypeError, ValueError):
                        metadata = {}
            
            result.append(ConversationHistory(
                id=str(conv.id),
                message_type=conv.message_type,
                content=conv.content,
                timestamp=conv.timestamp,
                metadata=metadata
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/clear")
async def clear_conversation_history(
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """Clear conversation history for a user"""
    try:
        # Delete conversations
        deleted_count = db.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .delete()
        
        # Reset user profile message count
        user_profile = db.query(UserProfile)\
            .filter(UserProfile.user_id == user_id)\
            .first()
        
        if user_profile:
            user_profile.total_messages = 0
            user_profile.total_conversations += 1
        
        db.commit()
        
        return {"message": f"Cleared {deleted_count} messages", "user_id": user_id}
        
    except Exception as e:
        logger.error(f"Error clearing conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_chat_stats(
    user_id: str = "default_user",
    db: Session = Depends(get_db)
):
    """Get chat statistics for a user"""
    try:
        # Get user profile
        user_profile = db.query(UserProfile)\
            .filter(UserProfile.user_id == user_id)\
            .first()
        
        # Get conversation count
        total_conversations = db.query(Conversation)\
            .filter(Conversation.user_id == user_id)\
            .count()
        
        user_messages = db.query(Conversation)\
            .filter(Conversation.user_id == user_id, Conversation.message_type == "user")\
            .count()
        
        assistant_messages = db.query(Conversation)\
            .filter(Conversation.user_id == user_id, Conversation.message_type == "assistant")\
            .count()
        
        # Calculate average message length
        from sqlalchemy import func
        avg_user_msg_length = db.query(func.avg(func.length(Conversation.content)))\
            .filter(Conversation.user_id == user_id, Conversation.message_type == "user")\
            .scalar() or 0
        
        stats = {
            "user_id": user_id,
            "total_messages": total_conversations,
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "avg_user_message_length": round(float(avg_user_msg_length), 1),
            "profile_exists": user_profile is not None,
        }
        
        if user_profile:
            stats.update({
                "account_created": user_profile.created_at,
                "last_interaction": user_profile.last_interaction,
                "formality_score": user_profile.formality_score,
                "preferred_response_length": user_profile.preferred_response_length,
                "topics_of_interest_count": len(user_profile.topics_of_interest or []),
                "personal_facts_count": len(user_profile.personal_facts or {})
            })
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting chat stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Background task functions
async def update_learning(learning_service, user_id: str, new_conversations: List[Conversation]):
    """Background task to update learning based on new conversations"""
    try:
        await learning_service.process_new_conversations(user_id, new_conversations)
    except Exception as e:
        logger.error(f"Error in background learning update: {e}")