# backend/app/core/config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    SECRET_KEY: str = "your-secret-key-change-this-in-production"
    
    # Database
    DATABASE_URL: str = "postgresql://aiagent:aiagent123@postgres:5432/aiagent"
    
    # AI Model Configuration
    MODEL_PROVIDER: str = "ollama"  # ollama, openai, anthropic
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_MODEL: str = "llama3.2:latest"
    
    # External AI APIs (optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    ANTHROPIC_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"
    
    # Learning Configuration
    ENABLE_LEARNING: bool = True
    MAX_CONVERSATION_HISTORY: int = 1000
    LEARNING_UPDATE_INTERVAL: int = 10  # Update learning after N messages
    MEMORY_CONSOLIDATION_INTERVAL: int = 100  # Consolidate memory after N messages
    
    # Vector Database (optional)
    CHROMA_HOST: str = "http://chroma:8000"
    ENABLE_VECTOR_MEMORY: bool = False
    
    # Security - Updated CORS settings
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:80",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "http://172.18.0.5:3000",  # Docker internal network
        "*"  # Allow all origins for development - remove in production
    ]
    
    # System prompts
    SYSTEM_PROMPT: str = """You are a personal AI assistant that learns from your user's communication style and preferences. 
    You have access to conversation history and learned personal context. Be helpful, natural, and adapt your responses 
    to match the user's preferred communication style while maintaining your helpful and ethical nature."""
    
    LEARNING_PROMPT: str = """Analyze this conversation to extract:
    1. Communication style preferences (formal/casual, brief/detailed, etc.)
    2. Personal facts and preferences mentioned
    3. Topics of interest
    4. Any specific ways the user likes to receive information
    Return structured data about what you learned."""

    class Config:
        env_file = ".env"

# Create settings instance
settings = Settings()

# Validate configuration
def validate_config():
    """Validate configuration and warn about missing values"""
    if settings.MODEL_PROVIDER == "openai" and not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required when using OpenAI model provider")
    
    if settings.MODEL_PROVIDER == "anthropic" and not settings.ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic model provider")
    
    if settings.SECRET_KEY == "your-secret-key-change-this-in-production":
        import warnings
        warnings.warn("Using default SECRET_KEY - change this in production!")

# Validate on import
validate_config()