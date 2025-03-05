import json
from typing import Dict, Any
from data import ncd_questions, ncd_risks_recommendations
from services import rag_service

# Store user sessions (in-memory, for now)
user_sessions: Dict[str, Dict[str, Any]] = {}


async def ncd_assessment(user_id: str, user_question: str) -> Dict[str, str]:
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    user_question = user_question.strip().lower()

    # Initialize session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {"stage": "conversation", "answers": {}, "question_index": None}

    session = user_sessions[user_id]

    # If assessment has not started, respond normally
    if session["stage"] == "conversation":
        if any(
            keyword in user_question
            for keyword in ["ncd risk", "risk assessment", "health check", "assessment"]
        ):
            session["stage"] = "assessment"
            session["question_index"] = 0
            return {"response": "Let's begin the assessment. " + ncd_questions["questions"][0]["question"]}
        else:
            return {"response": rag_service.retrieve_relevant_info(user_question)}

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
                session["stage"] = "conversation"
                return {"response": generate_assessment_result(session["answers"])}

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

    # Generate formatted response
    response = "Assessment complete! Based on your responses, here is a summary of your potential risk factors and recommendations:\n\n"

    for category, has_risk in risks.items():
      user_has_risk = False
      risk_messages = []
      recommendation_messages = []

      # Check Smoking Risks
      if category == "Respiratory Health":
        if answers.get("smoke") == "yes":
          user_has_risk = True
          risk_messages.append(risk_details["Respiratory Health"]["smoke"])
          recommendation_messages.append(recommendations["Respiratory Health"]["smoke"])
        if answers.get("passive_smoke") == "yes":
          user_has_risk = True
          risk_messages.append(risk_details["Respiratory Health"]["passive_smoke"])
          recommendation_messages.append(recommendations["Respiratory Health"]["passive_smoke"])
      # Check Alcohol Risks
      if category == "Cardiovascular Health":
        if answers.get("alcohol") == "yes":
          alcohol_freq = answers.get("alcohol_frequency", 0)
          if alcohol_freq > 3:
            user_has_risk = True
            risk_messages.append(risk_details["Cardiovascular Health"]["alcohol"])
            recommendation_messages.append(recommendations["Cardiovascular Health"]["alcohol"])
      # Check Female-Specific Risks
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