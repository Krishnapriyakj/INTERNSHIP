import json
import numpy as np
import joblib
import time
from typing import Dict, Any

# Load trained cancer prediction model
MODEL_PATH = "cancer_prediction_model.pkl"
cancer_model = joblib.load(MODEL_PATH)

SCALER_PATH = "scaler.pkl"
scaler = joblib.load(SCALER_PATH)

# Define questions for cancer risk assessment
with open("data/cancer_questions.json", "r") as f:
    cancer_questions = json.load(f)

# Load cancer risks and recommendations
with open("data/cancer_risks_recommendation.json", "r") as f:
    cancer_risks_recommendations = json.load(f)

# Global user sessions for cancer assessment
user_sessions: Dict[str, Dict[str, Any]] = {}

def is_user_in_cancer_assessment(user_id: str) -> bool:
    """Check if a user is currently undergoing a cancer assessment."""
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

async def cancer_assessment(user_id: str, user_question: str) -> Dict[str, str]:
    """Handles chatbot queries and dynamically assesses cancer risk within the conversation."""
    user_question = user_question.strip().lower()

    # Check if the user wants to stop the assessment
    if user_question in ["stop", "exit", "cancel", "end assessment"]:
        if user_id in user_sessions:
            # Clean up the session
            del user_sessions[user_id]
            return {"response": "Cancer risk assessment stopped. You can start again anytime by asking about cancer risk."}

    # Initialize session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {"stage": "conversation", "answers": {}, "question_index": None}

    session = user_sessions[user_id]

    # Start assessment if user requests it
    if session["stage"] == "conversation":
        session["stage"] = "assessment"
        session["question_index"] = 0
        return {"response": "Let's begin the cancer risk assessment. " + cancer_questions["questions"][0]["question"]}

    # Proceed with the assessment
    current_index = session["question_index"]
    current_question = cancer_questions["questions"][current_index]
    expected_key = current_question["key"]

    # Validate the answer
    try:
        user_answer = int(user_question)
        if not (0 <= user_answer <= 9):
            return {"response": "Please provide a number between 0 and 9."}
    except ValueError:
        return {"response": "Please provide a valid number between 0 and 9."}

    # Store the answer
    session["answers"][expected_key] = user_answer

    # Move to the next question or complete assessment
    current_index += 1
    if current_index >= len(cancer_questions["questions"]):
        # Assessment complete
        risk = predict_cancer_risk(session["answers"])
        detailed_recommendations = generate_detailed_recommendations(session["answers"])

        # Mark the session as completed instead of deleting it
        session["stage"] = "completed"
        session["completed_at"] = time.time()

        return {"response": f"Cancer Risk Assessment Completed. Your predicted risk level: {risk}\n\n{detailed_recommendations}"}

    # Update the question index and ask the next question
    session["question_index"] = current_index
    return {"response": cancer_questions["questions"][current_index]["question"]}

def predict_cancer_risk(user_answers):
    """Predict cancer risk level using the trained model."""
    # Extract features in the correct order
    input_features = [user_answers[q["key"]] for q in cancer_questions["questions"]]
    input_array = np.array(input_features).reshape(1, -1)
    input_scaled = scaler.transform(input_array)

    # Make prediction
    prediction = cancer_model.predict(input_array)[0]

    # Map prediction to risk level
    levels = {0: "Low", 1: "Medium", 2: "High"}
    return levels[prediction]

def generate_detailed_recommendations(answers):
    """Generate detailed recommendations based on user answers."""
    response = "Based on your responses, here are your specific risk factors and recommendations:\n\n"

    risk_categories = []

    # Determine specific risk factors based on answers
    if answers.get("Occupational Hazards", 0) >= 5 or answers.get("Passive Smoker", 0) >= 5:
        risk_categories.append("Lung Cancer")

    if answers.get("Obesity", 0) >= 5 or answers.get("Alcohol use", 0) >= 5:
        risk_categories.append("Breast Cancer")

    if answers.get("Obesity", 0) >= 5 or answers.get("Balanced Diet", 0) <= 4:
        risk_categories.append("Colorectal Cancer")

    if answers.get("Genetic Risk", 0) >= 5:
        risk_categories.append("Prostate Cancer")
        risk_categories.append("Skin Cancer")

    if answers.get("Occupational Hazards", 0) >= 5:
        risk_categories.append("Lung Cancer")
        risk_categories.append("Skin Cancer")

    if answers.get("Chest Pain", 0) >= 5 or answers.get("Coughing of Blood", 0) >= 5:
        risk_categories.append("Lung Cancer")

    if answers.get("Fatigue", 0) >= 5:
        risk_categories.append("Breast Cancer")
        risk_categories.append("Colorectal Cancer")

    # If no specific risks identified, provide general recommendations
    if not risk_categories:
        return generate_recommendations("Low")

    # Generate recommendations for each risk category
    for category in set(risk_categories):
        response += f"🔹 **{category}**:\n"

        # Add risk details
        for factor_key, factor_value in answers.items():
            if factor_key in cancer_risks_recommendations["risk_details"].get(category, {}):
                if (factor_key == "Balanced Diet" and factor_value <= 4) or factor_value >= 5:
                    response += f"- {cancer_risks_recommendations['risk_details'][category][factor_key]}\n"

        # Add recommendations
        response += "**Recommendations**:\n"
        for factor_key, factor_value in answers.items():
            if factor_key in cancer_risks_recommendations["recommendations"].get(category, {}):
                if (factor_key == "Balanced Diet" and factor_value <= 4) or factor_value >= 5:
                    response += f"- {cancer_risks_recommendations['recommendations'][category][factor_key]}\n"

        response += "\n"

    response += "Remember: This assessment is not a diagnosis. Always consult with healthcare professionals for proper medical advice."
    return response

def generate_recommendations(risk_level):
    """Generate general recommendations based on the risk level."""
    recommendations = {
        "Low": [
            "Continue with regular health check-ups.",
            "Maintain a healthy lifestyle with balanced diet and regular exercise.",
            "Avoid smoking and limit alcohol consumption.",
            "Be aware of your family history and inform your doctor about any changes."
        ],
        "Medium": [
            "Schedule a follow-up with your healthcare provider within 3-6 months.",
            "Consider additional screening tests based on your specific risk factors.",
            "Make lifestyle modifications to reduce risk factors (reduce smoking/alcohol, improve diet).",
            "Learn about early warning signs and symptoms to monitor."
        ],
        "High": [
            "Consult with a healthcare professional immediately.",
            "Follow through with recommended specialized screenings.",
            "Consider genetic counseling if there's a strong family history.",
            "Implement significant lifestyle changes under medical supervision.",
            "Join a support group for guidance and emotional support."
        ]
    }

    result = f"Based on your risk level ({risk_level}), here are my recommendations:\n\n"
    for rec in recommendations[risk_level]:
        result += f"- {rec}\n"
    result += "\nRemember: This assessment is not a diagnosis. Always consult with healthcare professionals for proper medical advice."
    return result
def clean_expired_sessions():
    """Clean up expired sessions"""
    current_time = time.time()
    expired_sessions = []
    
    for user_id, session in user_sessions.items():
        # Clean up completed sessions after 30 minutes
        if session.get("stage") == "completed" and current_time - session.get("completed_at", 0) > 1800:
            expired_sessions.append(user_id)
    
    for user_id in expired_sessions:
        del user_sessions[user_id]