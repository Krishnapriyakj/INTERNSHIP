from fastapi import APIRouter, Depends
from typing import Dict

from models.schema import QueryRequest
from services import ncd_service, rag_service

router = APIRouter()


@router.post("/chat/", summary="Chat with the AI for health queries and NCD assessment")
async def chat(query: QueryRequest) -> Dict[str, str]:
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    user_id = query.user_id
    user_question = query.question.strip().lower()

    # Check if the user is in an active assessment session
    if ncd_service.is_user_in_assessment(user_id) or any(
        keyword in user_question for keyword in ["ncd risk", "risk assessment", "health check", "assessment"]
    ):
        return await ncd_service.ncd_assessment(user_id, user_question)

    # Default to normal chatbot response
    return {"response": rag_service.retrieve_relevant_info(user_question)}
