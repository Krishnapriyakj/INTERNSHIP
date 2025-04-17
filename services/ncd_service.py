import json
import time
from typing import Dict, Any, Optional

# Load questions and recommendations
with open("data/ncd_questions.json", "r") as f:
    ncd_questions = json.load(f)

with open("data/ncd_risks_recommendations.json", "r") as f:
    ncd_risks_recommendations = json.load(f)

# Global user sessions (in-memory, for now)
user_sessions: Dict[str, Dict[str, Any]] = {}

def is_user_in_assessment(user_id: str) -> bool:
    """Check if a user is currently undergoing an assessment."""
    return user_id in user_sessions and user_sessions[user_id]["stage"] == "assessment"

def get_session_details(user_id: str) -> dict:
    """Get session details for a user if they exist"""
    if user_id in user_sessions:
        return {
            "stage": user_sessions[user_id].get("stage"),
            "question_index": user_sessions[user_id].get("question_index"),
            "answers": user_sessions[user_id].get("answers", {})
        }
    return {}

def get_completed_assessment(user_id: str) -> Optional[dict]:
    """Retrieve a completed assessment if it exists"""
    if user_id in user_sessions and user_sessions[user_id].get("stage") == "completed":
        return user_sessions[user_id]
    return None

async def ncd_assessment(user_id: str, user_question: str) -> Dict[str, str]:
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    
    user_question = user_question.strip().lower()
    
    # Expanded comprehensive list of exit keywords/phrases
    exit_keywords = [
        # Basic exit commands
        "stop", "exit", "cancel", "end", "quit", "finish", "leave","tired", "frustrate"
        # More detailed exit requests
        "i want to stop", "i want to exit", "i want to leave", "i want to quit", 
        "i want to finish", "i want to cancel", "i want to end",
        "i'd like to stop", "i'd like to exit", "i'd like to leave", "i'd like to quit",
        "i would like to stop", "i would like to exit", "i would like to leave",
        # Assessment specific exits
        "stop assessment", "exit assessment", "cancel assessment", "end assessment", 
        "quit assessment", "finish assessment", "leave assessment", "close assessment", 
        "terminate assessment", "stop the assessment", "exit the assessment", 
        "cancel the assessment", "end the assessment", "quit the assessment",
        # Polite forms
        "can we stop", "can we exit", "can we quit", "can we finish", "can we end",
        "could we stop", "could we exit", "could we quit", "could we finish",
        "let's stop", "let's exit", "let's quit", "let's end", "let's finish",
        # Negative responses
        "i don't want to continue", "i do not want to continue", "don't want to continue",
        "i don't want to do this", "i do not want to do this", "don't want to do this",
        "i'm not interested", "i am not interested", "no longer interested",
        # Interruption phrases
        "i need to go", "i have to go", "i must go", "i'm leaving", "i am leaving",
        "got to go", "gotta go", "have to leave", "need to leave",
        # Frustration indicators
        "i'm done", "i am done", "that's enough", "that is enough", "enough of this",
        "i'm tired of this", "i am tired of this", "i'm bored", "i am bored",
        # Change of mind
        "i changed my mind", "changed my mind", "never mind", "not now", 
        "not anymore", "not interested anymore", "no thanks", "no thank you",
        # Other common expressions
        "bye", "goodbye", "see you", "abort", "terminate", "forget it",
        "skip this", "skip assessment", "no more questions"
    ]
    
    # Initialize session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {"stage": "conversation", "answers": {}, "question_index": None}
    
    session = user_sessions[user_id]
    
    # Handle exit confirmation if we're in that state
    if session.get("awaiting_exit_confirmation"):
        if user_question == "yes":
            # User confirmed they want to exit
            del user_sessions[user_id]
            return {
                "response": "Assessment stopped. You can start again anytime by saying 'NCD assessment'.",
                "service_type": "ncd"
            }
        elif user_question == "no":
            # User wants to continue
            session["awaiting_exit_confirmation"] = False
            current_index = session["question_index"]
            current_question = ncd_questions["questions"][current_index]
            return {
                "response": f"Okay, continuing the assessment. {current_question['question']}",
                "service_type": "ncd"
            }
        else:
            # Invalid response to exit confirmation
            return {
                "response": "Please answer with 'yes' or 'no'. Do you want to leave? (yes/no)",
                "service_type": "ncd"
            }
    
    # Check for exit commands at any point during assessment
    if session["stage"] == "assessment" and any(keyword in user_question for keyword in exit_keywords):
        session["awaiting_exit_confirmation"] = True
        return {
            "response": "Do you want to leave? (yes/no)",
            "service_type": "ncd"
        }
    
    # Start assessment if user requests it
    if session["stage"] == "conversation":
        if any(phrase in user_question for phrase in ["ncd assessment", "health assessment", "start assessment"]):
            session["stage"] = "assessment"
            session["question_index"] = 0
            return {
                "response": "Let's begin the NCD assessment. " + ncd_questions["questions"][0]["question"],
                "service_type": "ncd"
            }
        return {
            "response": "Would you like to begin an NCD health assessment? (yes/no)",
            "service_type": "ncd"
        }
    
    # Handle yes/no response for starting assessment
    if session["stage"] == "conversation" and user_question in ["yes", "no"]:
        if user_question == "yes":
            session["stage"] = "assessment"
            session["question_index"] = 0
            return {
                "response": "Let's begin the NCD assessment. " + ncd_questions["questions"][0]["question"],
                "service_type": "ncd"
            }
        else:
            return {
                "response": "Okay, no problem. You can start an assessment anytime by saying 'NCD assessment'.",
                "service_type": "ncd"
            }
    
    # Proceed with the assessment
    if session["stage"] == "assessment":
        current_index = session["question_index"]
        current_question = ncd_questions["questions"][current_index]
        expected_key = current_question["key"]
        valid_answers = current_question["valid_answers"]
        
        # Validate answer format
        if valid_answers == "numeric":
            try:
                user_answer = int(user_question)
            except ValueError:
                # Check if it's an exit attempt before returning error
                if any(keyword in user_question for keyword in exit_keywords):
                    session["awaiting_exit_confirmation"] = True
                    return {
                        "response": "Do you want to leave? (yes/no)",
                        "service_type": "ncd"
                    }
                return {
                    "response": "Please provide a numeric answer.",
                    "service_type": "ncd"
                }
        else:
            user_answer = user_question.strip().lower()
            if user_answer not in valid_answers:
                # Check again if it's an exit attempt that wasn't caught by our earlier check
                if any(keyword in user_question for keyword in exit_keywords):
                    session["awaiting_exit_confirmation"] = True
                    return {
                        "response": "Do you want to leave? (yes/no)",
                        "service_type": "ncd"
                    }
                return {
                    "response": f"Please answer with one of the following: {', '.join(valid_answers)}",
                    "service_type": "ncd"
                }
        
        # Store the answer
        session["answers"][expected_key] = user_answer
        
        # Find the next valid question
        while True:
            current_index += 1
            if current_index >= len(ncd_questions["questions"]):
                # Assessment complete
                result = generate_assessment_result(session["answers"])
                session["stage"] = "completed"
                session["completed_at"] = time.time()
                session["service_type"] = "ncd"
                return {
                    "response": result,
                    "service_type": "ncd"
                }
            
            next_question = ncd_questions["questions"][current_index]
            if "depends_on" in next_question:
                dependency_key = next_question["depends_on"]
                if session["answers"].get(dependency_key) != next_question["condition"]:
                    continue
            
            session["question_index"] = current_index
            return {
                "response": next_question["question"],
                "service_type": "ncd"
            }
    
    # Fallback response
    return {
        "response": "I'm not sure what you'd like to do. Would you like to begin an NCD health assessment? (yes/no)",
        "service_type": "ncd"
    }

def generate_assessment_result(answers):
    """Generates a structured health risk summary based on user responses."""
    if not answers:
        return "No assessment data available. Please complete the assessment first."
    
    risks = ncd_risks_recommendations["risks"]
    recommendations = ncd_risks_recommendations["recommendations"]
    risk_details = ncd_risks_recommendations["risk_details"]
    
    response = "Assessment complete! Based on your responses, here is a summary of your potential risk factors and recommendations:\n\n"
    has_any_risk = False

    for category, has_risk in risks.items():
        user_has_risk = False
        risk_messages = []
        recommendation_messages = []

        if category == "Respiratory Health":
            if answers.get("smoke") == "yes":
                user_has_risk = True
                risk_messages.append(risk_details["Respiratory Health"]["smoke"])
                recommendation_messages.append(recommendations["Respiratory Health"]["smoke"])
            if answers.get("passive_smoke") == "yes":
                user_has_risk = True
                risk_messages.append(risk_details["Respiratory Health"]["passive_smoke"])
                recommendation_messages.append(recommendations["Respiratory Health"]["passive_smoke"])

        if category == "Cardiovascular Health":
            if answers.get("alcohol") == "yes":
                alcohol_freq = answers.get("alcohol_frequency", 0)
                if isinstance(alcohol_freq, str):
                    try:
                        alcohol_freq = int(alcohol_freq)
                    except ValueError:
                        alcohol_freq = 0
                if alcohol_freq > 3:
                    user_has_risk = True
                    risk_messages.append(risk_details["Cardiovascular Health"]["alcohol"])
                    recommendation_messages.append(recommendations["Cardiovascular Health"]["alcohol"])

        if category == "Overall Well-being":
            if answers.get("gender") == "female":
                if answers.get("nipple_discharge") == "yes":
                    user_has_risk = True
                    risk_messages.append(risk_details["Overall Well-being"]["nipple_discharge"])
                    recommendation_messages.append(recommendations["Overall Well-being"]["nipple_discharge"])
                if answers.get("post_menopause_bleeding") == "yes":
                    user_has_risk = True
                    risk_messages.append(risk_details["Overall Well-being"]["post_menopause_bleeding"])
                    recommendation_messages.append(recommendations["Overall Well-being"]["post_menopause_bleeding"])

        if user_has_risk:
            has_any_risk = True
            response += f"🔹 **{category}**:\n"
            for risk in risk_messages:
                response += f"- {risk}\n"
            response += "**Recommendations**:\n"
            for rec in recommendation_messages:
                response += f"- {rec}\n"
            response += "\n"

    if not has_any_risk:
        response += "Your responses do not indicate significant risk factors. However, regular health checkups are recommended."

    return response

def clean_expired_sessions():
    """Clean up expired sessions"""
    current_time = time.time()
    expired_sessions = []
    for user_id, session in user_sessions.items():
        if session.get("stage") == "completed" and current_time - session.get("completed_at", 0) > 1800:
            expired_sessions.append(user_id)
    for user_id in expired_sessions:
        del user_sessions[user_id]