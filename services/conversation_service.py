from typing import Dict, Any, List, Optional
import time

# Global conversation memory storage
conversation_memory: Dict[str, Dict[str, Any]] = {}

# Constants
MEMORY_RETENTION_TIME = 1800  # 30 minutes in seconds
MAX_CONVERSATION_HISTORY = 10  # Store last 10 interactions

def store_interaction(user_id: str, service_type: str, details: Dict[str, Any], question: str, response: str) -> None:
    """Store an interaction in the conversation memory."""
    timestamp = time.time()
    
    if user_id not in conversation_memory:
        conversation_memory[user_id] = {
            "last_accessed": timestamp,
            "last_service": service_type,
            "service_details": details,
            "history": []
        }
    else:
        conversation_memory[user_id]["last_accessed"] = timestamp
        conversation_memory[user_id]["last_service"] = service_type
        conversation_memory[user_id]["service_details"] = details
    
    conversation_memory[user_id]["history"].append({
        "timestamp": timestamp,
        "question": question,
        "response": response
    })
    
    if len(conversation_memory[user_id]["history"]) > MAX_CONVERSATION_HISTORY:
        conversation_memory[user_id]["history"] = conversation_memory[user_id]["history"][-MAX_CONVERSATION_HISTORY:]

def get_user_context(user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve user context if it exists and hasn't expired."""
    if user_id not in conversation_memory:
        return None
    
    last_accessed = conversation_memory[user_id]["last_accessed"]
    if time.time() - last_accessed > MEMORY_RETENTION_TIME:
        del conversation_memory[user_id]
        return None
    
    conversation_memory[user_id]["last_accessed"] = time.time()
    return conversation_memory[user_id]

def get_last_interaction(user_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent interaction for a user"""
    context = get_user_context(user_id)
    if context and context["history"]:
        return context["history"][-1]
    return None

def handle_conversation_continuation(user_id: str, user_question: str) -> Optional[Dict[str, str]]:
    """Handle conversation continuations like 'thank you', 'ok', etc."""
    continuers = ["thanks", "thank you", "ok", "okay", "got it", "i understand",
                 "that's helpful", "that is helpful", "good", "great", "perfect"]
    
    user_input_lower = user_question.strip().lower()
    is_acknowledgment = any(cont == user_input_lower or user_input_lower.startswith(cont) 
                          for cont in continuers)

    if not is_acknowledgment:
        return None

    context = get_user_context(user_id)
    if not context:
        return {"response": "You're welcome! How can I assist you further?"}

    last_service = context.get("last_service")
    last_interaction = context.get("history", [{}])[-1]

    # Special handling for post-assessment acknowledgments
    if last_service == "ncd" and "assessment complete" in last_interaction.get("response", "").lower():
        response = ("You're welcome! The NCD assessment helps identify potential health risks. "
                   "Would you like to:\n"
                   "1. Review your results again\n"
                   "2. Start a new assessment\n"
                   "3. Get help with something else?")
        
        store_interaction(
            user_id=user_id,
            service_type="ncd",
            details={"post_assessment": True},
            question=user_question,
            response=response
        )
        return {"response": response}

    # Existing continuation handling
    if last_service == "ncd":
        response = "You're welcome! The NCD assessment helps identify potential health risks. Would you like to learn more about any specific health topic or try another assessment?"
    elif last_service == "cancer":
        response = "You're welcome! Remember that the cancer risk assessment is just a screening tool. Would you like to discuss anything else about your health risks or book an appointment with a specialist?"
    elif last_service == "appointment":
        response = "You're welcome! Your appointment details have been provided. Is there anything else you'd like to know about your upcoming visit or other health services?"
    else:
        response = "You're welcome! Is there anything else I can help you with regarding your health concerns?"

    store_interaction(
        user_id=user_id,
        service_type=last_service,
        details=context.get("service_details", {}),
        question=user_question,
        response=response
    )
    return {"response": response}

def clean_expired_conversations() -> None:
    """Remove expired conversation memories"""
    current_time = time.time()
    expired_users = []
    for user_id, data in conversation_memory.items():
        if current_time - data["last_accessed"] > MEMORY_RETENTION_TIME:
            expired_users.append(user_id)
    for user_id in expired_users:
        del conversation_memory[user_id]