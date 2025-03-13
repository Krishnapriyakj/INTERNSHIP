import json
from typing import Dict, Any
from data import ncd_questions, ncd_risks_recommendations

# Global user sessions (in-memory, for now)
user_sessions: Dict[str, Dict[str, Any]] = {}

def is_user_in_assessment(user_id: str) -> bool:
    """Check if a user is currently undergoing an assessment."""
    return user_id in user_sessions and user_sessions[user_id]["stage"] == "assessment"

async def ncd_assessment(user_id: str, user_question: str) -> Dict[str, str]:
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    user_question = user_question.strip().lower()

    # Check if the user wants to stop the assessment
    if user_question in ["stop", "exit", "cancel", "end assessment"]:
        if user_id in user_sessions:
            # Clean up the session
            del user_sessions[user_id]
        return {"response": "Assessment stopped. You can start again anytime by saying 'start assessment'."}

    # Initialize session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {"stage": "conversation", "answers": {}, "question_index": None}

    session = user_sessions[user_id]

    # Start assessment if user requests it
    if session["stage"] == "conversation":
        session["stage"] = "assessment"
        session["question_index"] = 0
        return {"response": "Let's begin the assessment. " + ncd_questions["questions"][0]["question"]}

    # Proceed with the assessment
    current_index = session["question_index"]
    current_question = ncd_questions["questions"][current_index]
    expected_key = current_question["key"]
    valid_answers = current_question["valid_answers"]

    # Validate answer format
    if valid_answers == "numeric":
        try:
            user_answer = int(user_question)
        except ValueError:
            return {"response": "Please provide a numeric answer."}
    else:
        user_answer = user_question.strip().lower()
        if user_answer not in valid_answers:
            return {
                "response": f"Please answer with one of the following: {', '.join(valid_answers)}"
            }

    # Store the answer
    session["answers"][expected_key] = user_answer

    # Find the next valid question
    while True:
        current_index += 1
        if current_index >= len(ncd_questions["questions"]):
            # Assessment complete
            result = generate_assessment_result(session["answers"])
            # Clean up the session
            del user_sessions[user_id]
            return {"response": result}

        next_question = ncd_questions["questions"][current_index]
        if "depends_on" in next_question:
            dependency_key = next_question["depends_on"]
            if session["answers"].get(dependency_key) != next_question["condition"]:
                continue

        session["question_index"] = current_index
        return {"response": next_question["question"]}

def generate_assessment_result(answers):
    """Generates a structured health risk summary based on user responses."""
    risks = ncd_risks_recommendations["risks"]
    recommendations = ncd_risks_recommendations["recommendations"]
    risk_details = ncd_risks_recommendations["risk_details"]

    response = "Assessment complete! Based on your responses, here is a summary of your potential risk factors and recommendations:\n\n"

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
            response += f"🔹 **{category}**:\n"
            for risk in risk_messages:
                response += f"- {risk}\n"
            response += " **Recommendation**:\n"
            for rec in recommendation_messages:
                response += f"- {rec}\n"
            response += "\n"

    return response.strip() if risks else "Your responses do not indicate significant risk factors. However, regular health checkups are recommended."