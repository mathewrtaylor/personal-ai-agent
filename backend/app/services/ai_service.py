# backend/app/services/ai_service.py
import asyncio
import httpx
import logging
from typing import List, Dict, Any, Optional
import json

from app.core.config import settings
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = None
        self.model_provider = settings.MODEL_PROVIDER.lower()
        self.initialized = False
    
    async def initialize(self):
        """Initialize the AI service based on configured provider"""
        try:
            if self.model_provider == "ollama":
                await self._initialize_ollama()
            elif self.model_provider == "openai":
                await self._initialize_openai()
            elif self.model_provider == "anthropic":
                await self._initialize_anthropic()
            else:
                raise ValueError(f"Unsupported model provider: {self.model_provider}")
            
            self.initialized = True
            logger.info(f"AI Service initialized with {self.model_provider}")
        except Exception as e:
            logger.error(f"Failed to initialize AI service: {e}")
            raise
    
    async def _initialize_ollama(self):
        """Initialize Ollama connection and ensure model is available"""
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Check if Ollama is running
        try:
            response = await self.client.get(f"{settings.OLLAMA_HOST}/api/tags")
            if response.status_code != 200:
                raise Exception("Ollama not accessible")
        except Exception as e:
            logger.error(f"Cannot connect to Ollama: {e}")
            raise
        
        # Check if model is available, pull if not
        await self._ensure_ollama_model()
    
    async def _ensure_ollama_model(self):
        """Ensure the specified model is available in Ollama"""
        try:
            # List available models
            response = await self.client.get(f"{settings.OLLAMA_HOST}/api/tags")
            models = response.json()
            
            model_names = [model["name"] for model in models.get("models", [])]
            
            if settings.OLLAMA_MODEL not in model_names:
                logger.info(f"Model {settings.OLLAMA_MODEL} not found, pulling...")
                # Pull the model
                pull_data = {"name": settings.OLLAMA_MODEL}
                response = await self.client.post(
                    f"{settings.OLLAMA_HOST}/api/pull",
                    json=pull_data,
                    timeout=300.0  # Model pulling can take a while
                )
                
                if response.status_code != 200:
                    raise Exception(f"Failed to pull model: {response.text}")
                
                logger.info(f"Successfully pulled model {settings.OLLAMA_MODEL}")
            else:
                logger.info(f"Model {settings.OLLAMA_MODEL} is available")
                
        except Exception as e:
            logger.error(f"Error ensuring Ollama model: {e}")
            raise
    
    async def _initialize_openai(self):
        """Initialize OpenAI client"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        
        self.client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            timeout=60.0
        )
    
    async def _initialize_anthropic(self):
        """Initialize Anthropic client"""
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
        
        self.client = httpx.AsyncClient(
            base_url="https://api.anthropic.com/v1",
            headers={
                "x-api-key": settings.ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01"
            },
            timeout=60.0
        )
    
    async def generate_response(
        self,
        message: str,
        conversation_history: List[Conversation],
        user_profile: Optional[UserProfile] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a response using the configured AI model"""
        
        if not self.initialized:
            raise Exception("AI Service not initialized")
        
        # Build context from conversation history and user profile
        context = self._build_context(conversation_history, user_profile)
        
        # Use custom system prompt or default
        system = system_prompt or self._build_system_prompt(user_profile)
        
        try:
            if self.model_provider == "ollama":
                return await self._generate_ollama_response(message, context, system)
            elif self.model_provider == "openai":
                return await self._generate_openai_response(message, context, system)
            elif self.model_provider == "anthropic":
                return await self._generate_anthropic_response(message, context, system)
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            raise
    
    def _build_context(self, conversation_history: List[Conversation], user_profile: Optional[UserProfile]) -> str:
        """Build context string from conversation history and user profile"""
        context_parts = []
        
        # Add user profile context if available
        if user_profile:
            profile_context = []
            
            # Add personal facts
            if user_profile.personal_facts:
                facts = [f"{k}: {v}" for k, v in user_profile.personal_facts.items()]
                profile_context.append(f"Personal facts: {', '.join(facts)}")
            
            # Add communication preferences
            if user_profile.communication_preferences:
                prefs = [f"{k}: {v}" for k, v in user_profile.communication_preferences.items()]
                profile_context.append(f"Communication preferences: {', '.join(prefs)}")
            
            # Add interests
            if user_profile.topics_of_interest:
                profile_context.append(f"Interests: {', '.join(user_profile.topics_of_interest)}")
            
            if profile_context:
                context_parts.append("User Profile:\n" + "\n".join(profile_context))
        
        # Add recent conversation history
        if conversation_history:
            history_lines = []
            for conv in conversation_history[-20:]:  # Last 20 messages
                role = "User" if conv.message_type == "user" else "Assistant"
                history_lines.append(f"{role}: {conv.content}")
            
            if history_lines:
                context_parts.append("Recent Conversation:\n" + "\n".join(history_lines))
        
        return "\n\n".join(context_parts)
    
    def _build_system_prompt(self, user_profile: Optional[UserProfile]) -> str:
        """Build system prompt based on user profile"""
        base_prompt = settings.SYSTEM_PROMPT
        
        if not user_profile:
            return base_prompt
        
        # Customize based on communication preferences
        style_additions = []
        
        if user_profile.communication_preferences:
            prefs = user_profile.communication_preferences
            
            # Formality
            if prefs.get("formality") == "casual":
                style_additions.append("Use a casual, friendly tone.")
            elif prefs.get("formality") == "formal":
                style_additions.append("Maintain a professional, formal tone.")
            
            # Response length preference
            if prefs.get("response_length") == "brief":
                style_additions.append("Keep responses concise and to the point.")
            elif prefs.get("response_length") == "detailed":
                style_additions.append("Provide detailed, comprehensive responses.")
            
            # Other preferences
            if prefs.get("humor") == "appreciated":
                style_additions.append("Feel free to include appropriate humor.")
            
            if prefs.get("technical_level") == "expert":
                style_additions.append("Use technical terminology when appropriate.")
            elif prefs.get("technical_level") == "beginner":
                style_additions.append("Explain technical concepts in simple terms.")
        
        if style_additions:
            return base_prompt + "\n\nAdditional style guidance: " + " ".join(style_additions)
        
        return base_prompt
    
    async def _generate_ollama_response(self, message: str, context: str, system: str) -> Dict[str, Any]:
        """Generate response using Ollama"""
        messages = [
            {"role": "system", "content": system}
        ]
        
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        response = await self.client.post(
            f"{settings.OLLAMA_HOST}/api/chat",
            json=payload
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.text}")
        
        result = response.json()
        return {
            "content": result["message"]["content"],
            "model": settings.OLLAMA_MODEL,
            "provider": "ollama",
            "metadata": {
                "total_duration": result.get("total_duration"),
                "load_duration": result.get("load_duration"),
                "prompt_eval_count": result.get("prompt_eval_count"),
                "eval_count": result.get("eval_count")
            }
        }
    
    async def _generate_openai_response(self, message: str, context: str, system: str) -> Dict[str, Any]:
        """Generate response using OpenAI"""
        messages = [
            {"role": "system", "content": system}
        ]
        
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": settings.OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
        }
        
        response = await self.client.post("/chat/completions", json=payload)
        
        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.text}")
        
        result = response.json()
        choice = result["choices"][0]
        
        return {
            "content": choice["message"]["content"],
            "model": settings.OPENAI_MODEL,
            "provider": "openai",
            "metadata": {
                "usage": result.get("usage"),
                "finish_reason": choice.get("finish_reason")
            }
        }
    
    async def _generate_anthropic_response(self, message: str, context: str, system: str) -> Dict[str, Any]:
        """Generate response using Anthropic"""
        full_prompt = system
        if context:
            full_prompt += f"\n\nContext: {context}"
        full_prompt += f"\n\nHuman: {message}\n\nAssistant:"
        
        payload = {
            "model": settings.ANTHROPIC_MODEL,
            "prompt": full_prompt,
            "max_tokens_to_sample": 2000,
            "temperature": 0.7,
        }
        
        response = await self.client.post("/complete", json=payload)
        
        if response.status_code != 200:
            raise Exception(f"Anthropic API error: {response.text}")
        
        result = response.json()
        
        return {
            "content": result["completion"],
            "model": settings.ANTHROPIC_MODEL,
            "provider": "anthropic",
            "metadata": {
                "stop_reason": result.get("stop_reason")
            }
        }
    
    async def analyze_for_learning(self, conversation_history: List[Conversation]) -> Dict[str, Any]:
        """Analyze conversation for learning opportunities"""
        if not conversation_history:
            return {}
        
        # Build analysis prompt
        recent_messages = conversation_history[-10:]  # Analyze last 10 messages
        conversation_text = "\n".join([
            f"{'User' if msg.message_type == 'user' else 'Assistant'}: {msg.content}"
            for msg in recent_messages
        ])
        
        analysis_prompt = f"""
        {settings.LEARNING_PROMPT}
        
        Conversation to analyze:
        {conversation_text}
        
        Respond with a JSON object containing:
        {{
            "personal_facts": {{"key": "value"}},
            "communication_preferences": {{"preference": "value"}},
            "topics_of_interest": ["topic1", "topic2"],
            "expertise_areas": ["area1", "area2"],
            "formality_score": 0.5,
            "preferred_response_length": "medium"
        }}
        """
        
        try:
            result = await self.generate_response(
                analysis_prompt,
                [],  # No history for analysis
                None,  # No profile for analysis
                "You are an AI assistant that analyzes conversations to extract learning data. Always respond with valid JSON."
            )
            
            # Try to parse JSON from response
            content = result["content"].strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            return json.loads(content)
        
        except Exception as e:
            logger.error(f"Error in learning analysis: {e}")
            return {}
    
    async def cleanup(self):
        """Clean up resources"""
        if self.client:
            await self.client.aclose()
        self.initialized = False