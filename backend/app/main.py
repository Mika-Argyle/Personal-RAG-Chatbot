# Imports

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any

from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

from app.config import get_settings
from app.services.rag_service import get_rag_service

# Load Environment Variables
load_dotenv()

# Get configuration
settings = get_settings()

# Data Models (Input/Output Structure)
# Using Pydantic models for automatic documentation, and validation.

# User Input 
class ChatRequest(BaseModel):
    message: str
    chat_history: Optional[List[Dict[str, str]]] = None

# AI Response with RAG context
class ChatResponse(BaseModel):
    response: str
    model_used: str
    sources_used: Optional[int] = 0
    sources: Optional[List[Dict[str, Any]]] = None

# Document input for knowledge base
class DocumentRequest(BaseModel):
    documents: List[Dict[str, Any]]


# Initialize services and lifespan management
rag_service = get_rag_service()
openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup RAG service."""
    # Startup
    success = await rag_service.initialize()
    if not success:
        print("⚠️  Warning: RAG service initialization failed - running in fallback mode")
    yield
    # Shutdown (if needed)

# Create Application Instance

app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan
)

# CORS Middleware - Will Enable: Frontend <> API Communication

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"], 
    allow_headers=["*"],
)

#-------API ENDPOINTS------------|


# API Endpoint - Root

# GET request handler for root ("/") AKA 
# homepage of API (http://localhost:8000/)
@app.get("/")   
async def root():
    # Return basic service information
    return {
        "message": "Personal RAG Chatbot API is running!",
        "status": "healthy",
        "version": "1.0.0"
    }

# API Endpoint - Health

# GET request handler for (http://localhost:8000/health)
@app.get("/health")     
async def health_check():
    return {"status": "healthy"}


# API Endpoint - RAG-enabled Chat

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    RAG-enabled chat endpoint that responds using context from knowledge base.

    This endpoint showcases Retrieval-Augmented Generation (RAG) capabilities
    by combining vector similarity search with language model generation.

    Args:
        request (ChatRequest): Contains the user's message and optional chat history
        
    Returns:
        ChatResponse: AI-generated response with RAG context and source metadata
    """
    try:
        # Use RAG service for context-aware response
        rag_response = await rag_service.chat_with_context(
            user_message=request.message,
            chat_history=request.chat_history or []
        )
        
        # Return structured response with RAG metadata
        return ChatResponse(
            response=rag_response["response"],
            model_used=rag_response["model_used"],
            sources_used=rag_response.get("sources_used", 0),
            sources=rag_response.get("sources", [])
        )
        
    except Exception as e:
        # Fallback to simple OpenAI chat if RAG fails
        try:
            fallback_response = await openai_client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {"role": "system", "content": 
                    "You are a helpful assistant for a "
                    "software developer's portfolio website."},
                    {"role": "user", "content": request.message}
                ],
                max_tokens=settings.max_tokens,
                temperature=settings.temperature
            )
            
            return ChatResponse(
                response=fallback_response.choices[0].message.content or "No response generated",
                model_used=settings.openai_model,
                sources_used=0,
                sources=[]
            )
            
        except Exception as fallback_error:
            return {"error": f"Chat failed: {str(fallback_error)}"}


# API Endpoint - Knowledge Base Statistics (Read-only for visitors)

@app.get("/api/knowledge-base/stats")
async def get_knowledge_base_stats():
    """
    Get statistics about the RAG knowledge base.
    
    This endpoint allows visitors to see the scope and scale of the
    knowledge base without allowing any modifications.
    
    Returns:
        Dict: Knowledge base statistics including document count, model info, and RAG settings
    """
    try:
        stats = await rag_service.get_knowledge_base_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get knowledge base stats: {str(e)}"
        )