# backend/app/main.py
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
import uvicorn
import logging
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, get_db
from app.api import chat, learning, health
from app.services.ai_service import AIService
from app.services.learning_service import LearningService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create global service instances
ai_service = AIService()
learning_service = LearningService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle startup and shutdown events"""
    # Startup
    logger.info("Starting Personal AI Agent...")
    
    # Initialize database
    from app.models import conversation, user_profile, learning_data
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    
    # Initialize AI service
    await ai_service.initialize()
    
    # Initialize learning service
    await learning_service.initialize()
    
    # Store service instances in app state so other modules can access them
    app.state.ai_service = ai_service
    app.state.learning_service = learning_service
    
    logger.info("Personal AI Agent started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Personal AI Agent...")
    await ai_service.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Personal AI Agent",
    description="A learning, portable AI agent that runs on your infrastructure",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(learning.router, prefix="/api/learning", tags=["learning"])
app.include_router(health.router, prefix="/api/health", tags=["health"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Personal AI Agent API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level="info"
    )