# backend/app/services/memory_service.py
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, or_
import json
import re

from app.core.database import SessionLocal
from app.core.config import settings
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile
from app.models.learning_data import LearningData, ConversationSummary

logger = logging.getLogger(__name__)

class MemoryService:
    """
    Service for managing conversation memory, context retrieval, and memory consolidation
    """
    
    def __init__(self):
        self.max_context_messages = 50  # Maximum messages to keep in working memory
        self.consolidation_threshold = 100  # Consolidate after N messages
        
    def get_conversation_context(self, user_id: str, max_messages: int = None) -> List[Dict[str, Any]]:
        """
        Get conversation context for AI generation
        Returns recent conversations formatted for AI context
        """
        db = SessionLocal()
        try:
            limit = max_messages or self.max_context_messages
            
            conversations = db.query(Conversation)\
                .filter(Conversation.user_id == user_id)\
                .order_by(desc(Conversation.timestamp))\
                .limit(limit)\
                .all()
            
            # Format for AI context (reverse to chronological order)
            context = []
            for conv in reversed(conversations):
                context.append({
                    "role": "user" if conv.message_type == "user" else "assistant",
                    "content": conv.content,
                    "timestamp": conv.timestamp.isoformat(),
                    "id": str(conv.id)
                })
            
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving conversation context: {e}")
            return []
        finally:
            db.close()
    
    def get_relevant_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get memories relevant to the current query
        Uses semantic similarity and keyword matching
        """
        db = SessionLocal()
        try:
            # Extract keywords from query for basic matching
            keywords = self._extract_keywords(query.lower())
            
            # Get recent learning data that might be relevant
            learning_data = db.query(LearningData)\
                .filter(and_(
                    LearningData.user_id == user_id,
                    LearningData.is_active == True
                ))\
                .order_by(desc(LearningData.confidence), desc(LearningData.last_observed))\
                .limit(20)\
                .all()
            
            # Score and filter learning data by relevance
            relevant_memories = []
            for data in learning_data:
                relevance_score = self._calculate_relevance_score(data, query, keywords)
                if relevance_score > 0.1:  # Minimum relevance threshold
                    memory = {
                        "type": data.learning_type,
                        "key": data.key,
                        "value": data.value,
                        "confidence": data.confidence,
                        "relevance": relevance_score,
                        "context": data.context,
                        "last_observed": data.last_observed.isoformat()
                    }
                    relevant_memories.append(memory)
            
            # Sort by relevance and return top results
            relevant_memories.sort(key=lambda x: x["relevance"], reverse=True)
            return relevant_memories[:limit]
            
        except Exception as e:
            logger.error(f"Error retrieving relevant memories: {e}")
            return []
        finally:
            db.close()
    
    def get_conversation_summaries(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        """Get recent conversation summaries for context"""
        db = SessionLocal()
        try:
            summaries = db.query(ConversationSummary)\
                .filter(and_(
                    ConversationSummary.user_id == user_id,
                    ConversationSummary.is_active == True
                ))\
                .order_by(desc(ConversationSummary.end_time))\
                .limit(limit)\
                .all()
            
            return [summary.to_dict() for summary in summaries]
            
        except Exception as e:
            logger.error(f"Error retrieving conversation summaries: {e}")
            return []
        finally:
            db.close()
    
    def build_memory_context(self, user_id: str, current_query: str) -> str:
        """
        Build a comprehensive memory context for AI generation
        Combines user profile, relevant memories, and conversation history
        """
        try:
            context_parts = []
            
            # Get user profile
            db = SessionLocal()
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            db.close()
            
            if user_profile and user_profile.personal_facts:
                facts = []
                for key, value in user_profile.personal_facts.items():
                    facts.append(f"{key}: {value}")
                if facts:
                    context_parts.append(f"Personal facts: {', '.join(facts)}")
            
            # Get relevant memories
            relevant_memories = self.get_relevant_memories(user_id, current_query)
            if relevant_memories:
                memory_strings = []
                for memory in relevant_memories[:3]:  # Top 3 most relevant
                    memory_strings.append(f"{memory['key']}: {memory['value']}")
                context_parts.append(f"Relevant context: {', '.join(memory_strings)}")
            
            # Get communication preferences
            if user_profile and user_profile.communication_preferences:
                prefs = []
                for key, value in user_profile.communication_preferences.items():
                    prefs.append(f"{key}: {value}")
                if prefs:
                    context_parts.append(f"Communication preferences: {', '.join(prefs)}")
            
            return " | ".join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.error(f"Error building memory context: {e}")
            return ""
    
    def should_consolidate_memory(self, user_id: str) -> bool:
        """Check if memory consolidation is needed"""
        db = SessionLocal()
        try:
            # Check message count since last consolidation
            recent_messages = db.query(func.count(Conversation.id))\
                .filter(Conversation.user_id == user_id)\
                .filter(Conversation.timestamp > datetime.utcnow() - timedelta(hours=24))\
                .scalar() or 0
            
            # Check if we have too many active learning entries
            active_learning_count = db.query(func.count(LearningData.id))\
                .filter(and_(
                    LearningData.user_id == user_id,
                    LearningData.is_active == True
                ))\
                .scalar() or 0
            
            return (recent_messages > self.consolidation_threshold or 
                    active_learning_count > 200)
            
        except Exception as e:
            logger.error(f"Error checking consolidation needs: {e}")
            return False
        finally:
            db.close()
    
    async def consolidate_memory(self, user_id: str):
        """
        Consolidate memory by:
        1. Creating conversation summaries
        2. Merging similar learning entries
        3. Archiving old data
        """
        db = SessionLocal()
        try:
            logger.info(f"Starting memory consolidation for user {user_id}")
            
            # 1. Create conversation summary for recent messages
            await self._create_recent_summary(user_id, db)
            
            # 2. Merge similar learning entries
            self._merge_similar_learnings(user_id, db)
            
            # 3. Archive old, low-confidence learning data
            self._archive_old_learnings(user_id, db)
            
            # 4. Update user profile completeness
            user_profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if user_profile:
                user_profile.calculate_profile_completeness()
            
            db.commit()
            logger.info(f"Memory consolidation completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error during memory consolidation: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for relevance matching"""
        # Simple keyword extraction - can be enhanced with NLP libraries
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'me', 'my', 'myself', 'we', 'us', 'our', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their'}
        
        # Extract words, remove punctuation, filter stop words
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [word for word in words if word not in stop_words]
        
        # Return unique keywords
        return list(set(keywords))
    
    def _calculate_relevance_score(self, learning_data: LearningData, query: str, keywords: List[str]) -> float:
        """Calculate relevance score for learning data against current query"""
        score = 0.0
        
        # Check if keywords appear in learning data
        text_to_search = f"{learning_data.key} {learning_data.value} {learning_data.context or ''}".lower()
        
        keyword_matches = sum(1 for keyword in keywords if keyword in text_to_search)
        if keywords:
            keyword_score = keyword_matches / len(keywords)
            score += keyword_score * 0.6
        
        # Boost score for recent observations
        days_since_observed = (datetime.utcnow() - learning_data.last_observed).days
        recency_score = max(0, 1 - days_since_observed / 30)  # Decay over 30 days
        score += recency_score * 0.2
        
        # Boost score for high confidence
        score += learning_data.confidence * 0.2
        
        # Bonus for personal facts and communication preferences
        if learning_data.learning_type in ['personal_fact', 'communication_preference']:
            score += 0.1
        
        return min(score, 1.0)
    
    async def _create_recent_summary(self, user_id: str, db: Session):
        """Create summary of recent conversations"""
        try:
            # Get conversations from last 24 hours that haven't been summarized
            recent_conversations = db.query(Conversation)\
                .filter(Conversation.user_id == user_id)\
                .filter(Conversation.timestamp > datetime.utcnow() - timedelta(hours=24))\
                .order_by(Conversation.timestamp)\
                .all()
            
            if len(recent_conversations) < 10:  # Not enough for meaningful summary
                return
            
            # Check if we already have a recent summary
            existing_summary = db.query(ConversationSummary)\
                .filter(ConversationSummary.user_id == user_id)\
                .filter(ConversationSummary.start_time > datetime.utcnow() - timedelta(hours=25))\
                .first()
            
            if existing_summary:
                return  # Already have a recent summary
            
            # Create basic summary (could be enhanced with AI summarization)
            topics = set()
            total_words = 0
            
            for conv in recent_conversations:
                total_words += len(conv.content.split())
                if conv.topics:
                    topics.update(conv.topics)
            
            summary_text = f"Conversation session with {len(recent_conversations)} messages covering {len(topics)} topics. Average message length: {total_words // len(recent_conversations) if recent_conversations else 0} words."
            
            summary = ConversationSummary(
                user_id=user_id,
                title=f"Session from {recent_conversations[0].timestamp.strftime('%Y-%m-%d %H:%M')}",
                summary=summary_text,
                key_topics=list(topics),
                start_time=recent_conversations[0].timestamp,
                end_time=recent_conversations[-1].timestamp,
                message_count=len(recent_conversations),
                conversation_ids=[str(conv.id) for conv in recent_conversations],
                summary_type="automatic",
                confidence_score=0.7
            )
            
            db.add(summary)
            
        except Exception as e:
            logger.error(f"Error creating recent summary: {e}")
    
    def _merge_similar_learnings(self, user_id: str, db: Session):
        """Merge similar learning entries to reduce redundancy"""
        try:
            # Get all active learning data grouped by type and key
            learning_groups = db.query(LearningData)\
                .filter(and_(
                    LearningData.user_id == user_id,
                    LearningData.is_active == True
                ))\
                .order_by(LearningData.learning_type, LearningData.key)\
                .all()
            
            # Group by type and key
            groups = {}
            for learning in learning_groups:
                group_key = f"{learning.learning_type}:{learning.key}"
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(learning)
            
            # Merge groups with multiple entries
            for group_key, learnings in groups.items():
                if len(learnings) > 1:
                    # Keep the highest confidence entry, merge others
                    primary = max(learnings, key=lambda x: x.confidence)
                    others = [l for l in learnings if l.id != primary.id]
                    
                    for other in others:
                        # Merge reinforcement counts
                        primary.times_observed += other.times_observed
                        primary.times_reinforced += other.times_reinforced
                        primary.times_contradicted += other.times_contradicted
                        
                        # Update last observed if newer
                        if other.last_observed > primary.last_observed:
                            primary.last_observed = other.last_observed
                        
                        # Deactivate the merged entry
                        other.is_active = False
                        other.superseded_by = primary.id
                    
                    # Recalculate confidence for primary
                    primary.confidence = min(primary.confidence * 1.1, 1.0)
                    primary.validation_score = primary._calculate_validation_score()
            
        except Exception as e:
            logger.error(f"Error merging similar learnings: {e}")
    
    def _archive_old_learnings(self, user_id: str, db: Session):
        """Archive old, low-confidence learning entries"""
        try:
            # Find old, low-confidence entries to archive
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_learnings = db.query(LearningData)\
                .filter(and_(
                    LearningData.user_id == user_id,
                    LearningData.is_active == True,
                    LearningData.confidence < 0.3,
                    LearningData.last_observed < cutoff_date,
                    LearningData.times_contradicted > LearningData.times_reinforced
                ))\
                .all()
            
            for learning in old_learnings:
                learning.is_active = False
                learning.updated_at = datetime.utcnow()
            
            logger.info(f"Archived {len(old_learnings)} low-confidence learning entries")
            
        except Exception as e:
            logger.error(f"Error archiving old learnings: {e}")
    
    def get_memory_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for monitoring"""
        db = SessionLocal()
        try:
            stats = {}
            
            # Conversation stats
            total_conversations = db.query(func.count(Conversation.id))\
                .filter(Conversation.user_id == user_id).scalar() or 0
            
            recent_conversations = db.query(func.count(Conversation.id))\
                .filter(Conversation.user_id == user_id)\
                .filter(Conversation.timestamp > datetime.utcnow() - timedelta(days=7))\
                .scalar() or 0
            
            # Learning data stats
            active_learnings = db.query(func.count(LearningData.id))\
                .filter(and_(LearningData.user_id == user_id, LearningData.is_active == True))\
                .scalar() or 0
            
            high_confidence_learnings = db.query(func.count(LearningData.id))\
                .filter(and_(
                    LearningData.user_id == user_id, 
                    LearningData.is_active == True,
                    LearningData.confidence > 0.8
                )).scalar() or 0
            
            # Summary stats
            total_summaries = db.query(func.count(ConversationSummary.id))\
                .filter(ConversationSummary.user_id == user_id).scalar() or 0
            
            stats = {
                "conversations": {
                    "total": total_conversations,
                    "recent_7_days": recent_conversations
                },
                "learning": {
                    "active_entries": active_learnings,
                    "high_confidence_entries": high_confidence_learnings,
                    "confidence_ratio": high_confidence_learnings / max(active_learnings, 1)
                },
                "summaries": {
                    "total": total_summaries
                },
                "consolidation_needed": self.should_consolidate_memory(user_id)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {}
        finally:
            db.close()