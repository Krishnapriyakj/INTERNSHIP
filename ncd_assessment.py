from pydantic import BaseModel
from typing import Dict, Any

from chatbot import retrieve_relevant_info
from ncd_questions import ncd_questions  # Import the list

# Request model for chatbot queries
class QueryRequest(BaseModel):
    user_id: str
    question: str

# Store user sessions (in-memory, for now)
user_sessions: Dict[str, Dict[str, Any]] = {}


async def ncd_assessment(query: QueryRequest) -> Dict[str, str]:
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    user_id = query.user_id
    user_question = query.question.strip().lower()

    # Initialize session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {"stage": "conversation", "answers": {}, "question_index": None}

    session = user_sessions[user_id]

    # If assessment has not started, respond normally
    if session["stage"] == "conversation":
        if any(keyword in user_question for keyword in ["ncd risk", "risk assessment", "health check", "assessment"]):
            session["stage"] = "assessment"
            session["question_index"] = 0
            return {"response": "Let's begin the assessment. " + ncd_questions[0]["question"]}
        else:
            return {"response": retrieve_relevant_info(user_question)}

    # Proceed with the assessment
    if session["stage"] == "assessment":
        current_index = session["question_index"]
        current_question = ncd_questions[current_index]
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
                return {"response": f"Please answer with one of the following: {', '.join(valid_answers)}"}

        # Store the answer
        session["answers"][expected_key] = user_answer

        # Find the next valid question
        while True:
            current_index += 1
            if current_index >= len(ncd_questions):
                session["stage"] = "conversation"
                return {"response": generate_assessment_result(session["answers"])}

            next_question = ncd_questions[current_index]
            if "depends_on" in next_question:
                dependency_key = next_question["depends_on"]
                if session["answers"].get(dependency_key) != next_question["condition"]:
                    continue

            session["question_index"] = current_index
            return {"response": next_question["question"]}


def generate_assessment_result(answers):
    """Generates a structured health risk summary based on user responses."""
    risks = {"Respiratory Health": [], "Cardiovascular Health": [], "Overall Well-being": []}
    recommendations = {"Respiratory Health": [], "Cardiovascular Health": [], "Overall Well-being": []}

    # Smoking Risks
    if answers.get("smoke") == "yes":
        risks["Respiratory Health"].append("Smoking increases the risk of lung disease, chronic bronchitis, and lung cancer.")
        recommendations["Respiratory Health"].append("Consider reducing or quitting smoking. Support groups and medical guidance can help.")

    if answers.get("passive_smoke") == "yes":
        risks["Respiratory Health"].append("Exposure to passive smoking may increase respiratory and cardiovascular risks.")
        recommendations["Respiratory Health"].append("Avoid areas with high smoke exposure to reduce health risks.")

    # Alcohol Risks
    if answers.get("alcohol") == "yes":
        alcohol_freq = answers.get("alcohol_frequency", 0)
        if alcohol_freq > 3:
            risks["Cardiovascular Health"].append("Frequent alcohol consumption can increase the risk of high blood pressure and heart disease.")
            recommendations["Cardiovascular Health"].append("Reduce alcohol intake and monitor blood pressure regularly.")

    # Female-Specific Risks
    if answers.get("gender") == "female":
        if answers.get("nipple_discharge") == "yes":
            risks["Overall Well-being"].append("Nipple discharge may require medical evaluation for potential underlying issues.")
            recommendations["Overall Well-being"].append("Consult a doctor to rule out any health concerns.")

        if answers.get("post_menopause_bleeding") == "yes":
            risks["Overall Well-being"].append("Post-menopausal bleeding should be checked by a doctor as it could indicate health issues.")
            recommendations["Overall Well-being"].append("Seek medical advice to ensure early detection and treatment.")

    # Generate formatted response
    response = "Assessment complete! Based on your responses, here is a summary of your potential risk factors and recommendations:\n\n"

    for category, risk_list in risks.items():
        if risk_list:
            response += f"🔹 **{category}**:\n"
            for risk in risk_list:
                response += f"- {risk}\n"
            if recommendations[category]:
                response += " **Recommendation**:\n"
                for rec in recommendations[category]:
                    response += f"- {rec}\n"
            response += "\n"

    return response.strip() if risks else "Your responses do not indicate significant risk factors. However, regular health checkups are recommended."