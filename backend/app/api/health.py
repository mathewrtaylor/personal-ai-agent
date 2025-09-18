# backend/app/api/health.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import httpx
import logging
from datetime import datetime

from app.core.database import get_db
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/")
async def health_check(db: Session = Depends(get_db)):
    """Basic health check endpoint"""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow(),
            "version": "1.0.0",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with all service statuses"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "1.0.0",
        "services": {}
    }
    
    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
            "type": "postgresql"
        }
    except Exception as e:
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check AI model service
    if settings.MODEL_PROVIDER == "ollama":
        health_status["services"]["ai_model"] = await check_ollama_health()
    elif settings.MODEL_PROVIDER == "openai":
        health_status["services"]["ai_model"] = await check_openai_health()
    elif settings.MODEL_PROVIDER == "anthropic":
        health_status["services"]["ai_model"] = await check_anthropic_health()
    
    # Check vector database if enabled
    if settings.ENABLE_VECTOR_MEMORY:
        health_status["services"]["vector_db"] = await check_chroma_health()
    
    # Update overall status
    service_statuses = [service["status"] for service in health_status["services"].values()]
    if "unhealthy" in service_statuses:
        health_status["status"] = "unhealthy"
    elif "degraded" in service_statuses:
        health_status["status"] = "degraded"
    
    return health_status

@router.get("/models")
async def check_model_status():
    """Check status of available AI models"""
    try:
        if settings.MODEL_PROVIDER == "ollama":
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
                if response.status_code == 200:
                    models_data = response.json()
                    return {
                        "provider": "ollama",
                        "status": "available",
                        "current_model": settings.OLLAMA_MODEL,
                        "available_models": [model["name"] for model in models_data.get("models", [])],
                        "host": settings.OLLAMA_HOST
                    }
                else:
                    return {
                        "provider": "ollama",
                        "status": "unavailable",
                        "error": f"HTTP {response.status_code}"
                    }
        
        elif settings.MODEL_PROVIDER == "openai":
            return {
                "provider": "openai",
                "status": "configured" if settings.OPENAI_API_KEY else "not_configured",
                "model": settings.OPENAI_MODEL,
                "api_key_set": bool(settings.OPENAI_API_KEY)
            }
        
        elif settings.MODEL_PROVIDER == "anthropic":
            return {
                "provider": "anthropic",
                "status": "configured" if settings.ANTHROPIC_API_KEY else "not_configured", 
                "model": settings.ANTHROPIC_MODEL,
                "api_key_set": bool(settings.ANTHROPIC_API_KEY)
            }
        
        else:
            return {
                "provider": settings.MODEL_PROVIDER,
                "status": "unknown_provider",
                "error": f"Unknown provider: {settings.MODEL_PROVIDER}"
            }
            
    except Exception as e:
        logger.error(f"Error checking model status: {e}")
        return {
            "provider": settings.MODEL_PROVIDER,
            "status": "error",
            "error": str(e)
        }

async def check_ollama_health():
    """Check Ollama service health"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if Ollama is running
            response = await client.get(f"{settings.OLLAMA_HOST}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                return {
                    "status": "healthy" if settings.OLLAMA_MODEL in model_names else "degraded",
                    "host": settings.OLLAMA_HOST,
                    "current_model": settings.OLLAMA_MODEL,
                    "model_available": settings.OLLAMA_MODEL in model_names,
                    "total_models": len(models)
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "host": settings.OLLAMA_HOST
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "host": settings.OLLAMA_HOST
        }

async def check_openai_health():
    """Check OpenAI API health"""
    if not settings.OPENAI_API_KEY:
        return {
            "status": "not_configured",
            "error": "API key not set"
        }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
            )
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "model": settings.OPENAI_MODEL
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}"
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

async def check_anthropic_health():
    """Check Anthropic API health"""
    if not settings.ANTHROPIC_API_KEY:
        return {
            "status": "not_configured",
            "error": "API key not set"
        }
    
    # Anthropic doesn't have a simple health check endpoint
    # So we just verify the key is configured
    return {
        "status": "configured",
        "model": settings.ANTHROPIC_MODEL,
        "note": "API key configured, health check limited"
    }

async def check_chroma_health():
    """Check ChromaDB health"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.CHROMA_HOST}/api/v1/heartbeat")
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "host": settings.CHROMA_HOST
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "host": settings.CHROMA_HOST
                }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "host": settings.CHROMA_HOST
        }