from fastapi import APIRouter, Depends
from typing import Dict

from models.schema import QueryRequest
from services import ncd_service

router = APIRouter()


@router.post("/chat/", summary="Chat with the AI for health queries and NCD assessment")
async def chat(query: QueryRequest) -> Dict[str, str]:
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    return await ncd_service.ncd_assessment(query.user_id, query.question)