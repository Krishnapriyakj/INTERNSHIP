from fastapi import APIRouter
from models.schema import QueryRequest, RegisterRequest
from services import (
    ncd_service, 
    rag_service, 
    cancer_service, 
    appointment_service, 
    decision_service,
    conversation_service  
)
from typing import Dict, Any
import uuid

router = APIRouter()

# Temporary in-memory user store (replace with DB in production)
registered_users = {}

@router.post("/register", summary="Register a new user")
async def register_user(request: RegisterRequest) -> Dict[str, Any]:
    """Registers a new user and returns a unique user ID."""
    user_id = str(uuid.uuid4())[:8]

    registered_users[user_id] = {
        "name": request.name,
        "email": request.email,
        "phone": request.phone,
        "age": request.age,
        "gender": request.gender
    }

    return {"message": "User registered successfully", "user_id": user_id}


@router.post("/chat/", summary="Chat with the AI for health queries and assessments")
async def chat(query: QueryRequest) -> Dict[str, Any]:
    """Handles chatbot queries and dynamically routes them to appropriate services."""
    user_id = query.user_id
    user_question = query.question.strip().lower()

    # Default response format
    response = {
        "response": "",
        "type": "text",
        "options": []
    }

    # Check if the user is in an active session
    if ncd_service.is_user_in_assessment(user_id):
        result = await ncd_service.ncd_assessment(user_id, user_question)
        response["response"] = result.get("response", "")
        return response
        
    if cancer_service.is_user_in_cancer_assessment(user_id):
        result = await cancer_service.cancer_assessment(user_id, user_question)
        response["response"] = result.get("response", "")
        return response
        
    if appointment_service.is_user_in_appointment_booking(user_id):
        result = await appointment_service.appointment_booking(user_id, user_question)
        # For appointment service, preserve the full response structure
        return {
            "response": result.get("response", ""),
            "type": result.get("type", "text"),
            "options": result.get("options", [])
        }

    # For new requests, determine intent using LLM
    intent = await decision_service.determine_intent(user_question)

    # Print the intent for debugging
    print(f"Determined intent: {intent} for question: {user_question}")

    # Route to appropriate service based on intent
    if intent == "book_appointment" or any(keyword in user_question for keyword in ["book appointment", "schedule appointment", "make appointment"]):
        result = await appointment_service.appointment_booking(user_id, user_question)
        return {
            "response": result.get("response", ""),
            "type": result.get("type", "text"),
            "options": result.get("options", [])
        }
        
    if intent == "cancer_risk_assessment" or any(keyword in user_question for keyword in ["cancer risk", "cancer assessment", "cancer check", "cancer screening"]):
        result = await cancer_service.cancer_assessment(user_id, user_question)
        response["response"] = result.get("response", "")
        return response
        
    if intent == "ncd_risk_assessment" or any(keyword in user_question for keyword in ["ncd risk", "risk assessment", "health check", "assessment"]):
        result = await ncd_service.ncd_assessment(user_id, user_question)
        response["response"] = result.get("response", "")
        return response

    # Default to RAG response
    response["response"] = rag_service.retrieve_relevant_info(user_question)
    return response


@router.post("/maintenance/cleanup/", summary="Clean up expired conversations")
async def cleanup_expired_conversations():
    """Maintenance endpoint to clean up expired conversations and sessions"""
    # Clean conversation memory
    conversation_service.clean_expired_conversations()
    
    # Clean service-specific sessions
    ncd_service.clean_expired_sessions()
    cancer_service.clean_expired_sessions()
    appointment_service.clean_expired_sessions()
    
    return {"status": "success", "message": "Expired sessions cleaned up"}
