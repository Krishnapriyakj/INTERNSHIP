"""API routes for the chatbot application."""
from fastapi import APIRouter, Depends

from models.schema import QueryRequest, ChatResponse
from services.rag_service import retrieve_relevant_info
from services.ncd_service import NCDAssessmentManager

router = APIRouter()
ncd_manager = NCDAssessmentManager()

@router.post("/chat/", response_model=ChatResponse, summary="Chat with the AI for health queries and NCD assessment")
async def chat(query: QueryRequest):
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    # First, check if this is part of an NCD assessment
    ncd_response = ncd_manager.process_message(query.user_id, query.question)
    
    # If NCD assessment is active, return its response
    if ncd_response:
        return ncd_response
    
    # Otherwise, handle as a regular query with RAG
    response = retrieve_relevant_info(query.question)
    return {"response": response}