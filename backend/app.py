# Imports

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os
from openai import AsyncOpenAI
from dotenv import load_dotenv
from pydantic import BaseModel

# Load Environment Variables
load_dotenv()

# Data Models (Input/Output Structure)
# Using Pydantic models for automatic documentation, and validation.

# User Input 
class ChatRequest(BaseModel):
    message: str

# AI Response
class ChatResponse(BaseModel):
    response: str
    model_used: str


# Create Application Instance

app = FastAPI(
    title="Personal RAG Chatbot API",
    description="AI-powered chatbot for my website portfolio",
    version="1.0.0"
)

# CORS Middleware - Will Enable: Frontend <> API Communication

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"], 
    allow_headers=["*"],
)

# Initialize OpenAI client
# Returns key from environment variables (no key in source code = SECURE)
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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


#API Endpoint - Chat Request

# Sends the user's message with additional logic/context(ChatRequest) to AI,
# then returns the AI-generated response with metadata(ChatResponse).
@app.post("/api/chat")
async def chat(request: ChatRequest):
    #Docstring for API Docs
    """
    Chat endpoint that responds using OpenAI's GPT model.

    Args:
        request (ChatRequest): Contains the user's message
        
    Returns:
        ChatResponse: AI-generated response with metadata
    """
    # AI Request Logic 
    try:
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": 
                "You are a helpful assistant for a "
                "software developer's portfolio website."},
                {"role": "user", "content": request.message}
            ],
            max_tokens=500,
            temperature=0.7
        )

        # Response Processing
        return ChatResponse(
            response=response.choices[0].message.content,
            model_used="gpt-4o-mini"
        )

    # Error Handling
    except Exception as e:
        return {"error": f"Chat failed: {str(e)}"}