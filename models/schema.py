"""Pydantic models for request/response validation."""
from pydantic import BaseModel

class QueryRequest(BaseModel):
    """Request model for chatbot queries."""
    user_id: str
    question: str

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str