"""
FastAPI server for AutoStream AI Agent.
"""

import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional

from agent import get_agent


load_dotenv()


app = FastAPI(
    title="AutoStream AI Agent",
    description="AI-powered lead generation agent for AutoStream",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field("default", description="Session ID for conversation history")
    user_name: Optional[str] = Field(None, description="User's name (if known)")
    user_email: Optional[str] = Field(None, description="User's email (if known)")
    user_platform: Optional[str] = Field(None, description="Creator platform")


class ChatResponse(BaseModel):
    """Chat response model."""
    status: str
    response: str
    intent: Optional[str] = None
    lead_captured: bool = False
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    user_platform: Optional[str] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str


class StatsResponse(BaseModel):
    """Statistics response."""
    total_leads: int
    last_lead_timestamp: Optional[str] = None


# Routes
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        message="AutoStream AI Agent is running"
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for user messages.
    
    Args:
        request: ChatRequest with user message and optional context
        
    Returns:
        ChatResponse with agent response and state
    """
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        # Get agent
        agent = get_agent()
        
        # Prepare input state with optional user details
        input_data = {
            "message": request.message,
            "session_id": request.session_id,
        }
        
        # Update agent state with user details if provided
        if request.user_name:
            # This would require modifying the agent to accept external state updates
            pass
        
        # Get response from agent
        result = agent.chat(
            user_message=request.message,
            session_id=request.session_id
        )
        
        return ChatResponse(
            status=result.get("status", "success"),
            response=result.get("response", ""),
            intent=result.get("intent"),
            lead_captured=result.get("lead_captured", False),
            user_name=result.get("user_name"),
            user_email=result.get("user_email"),
            user_platform=result.get("user_platform"),
            error=result.get("error")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/lead-capture")
async def capture_lead(name: str, email: str, platform: str):
    """
    Manual lead capture endpoint.
    
    Args:
        name: User's name
        email: User's email
        platform: Creator platform (YouTube, Instagram, TikTok, etc.)
        
    Returns:
        Status and confirmation message
    """
    try:
        from lead_capture import get_lead_manager
        
        lead_manager = get_lead_manager()
        result = lead_manager.capture_lead(name, email, platform)
        
        return result
    
    except Exception as e:
        print(f"Error capturing lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get agent statistics."""
    try:
        from lead_capture import get_lead_manager
        
        lead_manager = get_lead_manager()
        leads = lead_manager.get_all_leads()
        
        last_lead_timestamp = None
        if leads:
            last_lead_timestamp = leads[-1].get("timestamp")
        
        return StatsResponse(
            total_leads=len(leads),
            last_lead_timestamp=last_lead_timestamp
        )
    
    except Exception as e:
        print(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/knowledge-base")
async def get_knowledge():
    """Get the knowledge base content."""
    try:
        from rag import get_knowledge_base
        
        kb = get_knowledge_base()
        return {"knowledge": kb.get_all_knowledge()}
    
    except Exception as e:
        print(f"Error retrieving knowledge base: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API documentation."""
    return {
        "name": "AutoStream AI Agent",
        "version": "1.0.0",
        "endpoints": {
            "POST /chat": "Send a message to the agent",
            "POST /lead-capture": "Manually capture a lead",
            "GET /stats": "Get agent statistics",
            "GET /knowledge-base": "Get the knowledge base",
            "GET /health": "Health check"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    # Run the server
    uvicorn.run(app, host="0.0.0.0", port=port)
