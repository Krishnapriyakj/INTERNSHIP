from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
import joblib  # For loading the trained model

# Load trained cancer prediction model
MODEL_PATH = "cancer_prediction_model.pkl"
cancer_model = joblib.load(MODEL_PATH)
SCALER_PATH = "scaler.pkl"
scaler = joblib.load(SCALER_PATH)

# Initialize FastAPI
app = FastAPI(title="Conversational NCD Chatbot", version="1.1")

# ChromaDB Path
CHROMA_DB_PATH = "chroma_db"

# Define the prompt template for RAG with integrated NCD assessment
PROMPT_TEMPLATE = """
You are an AI health assistant that answers medical questions.
Use the following context to help answer the user's query. If context is empty simply give a general health companion response.

====================
Context:
{context}

====================

User: {question}
AI:"""

# Initialize LLM model
model = OllamaLLM(model="llama3.2")

# Function to set up ChromaDB for RAG retrieval
def get_embedding_function():
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    return embeddings

def retrieve_relevant_info(query_text):
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding_function)

    # Retrieve relevant documents
    results = db.similarity_search_with_score(query_text, k=2)
    
    prompt = ""
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    # Format the prompt with retrieved context
    if results:
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt = prompt_template.format(context=context_text, question=query_text)
    else:
        prompt = prompt_template.format(context="<empty>", question=query_text)

    # Get response from LLM
    response_text = model.invoke(prompt)
    
    return response_text

# Store user sessions
user_sessions = {}

# Define possible questions
cancer_questions = [
    {"question": "Rate your Occupational Hazards (0-9):", "key": "OccuPational Hazards", "type": "numeric", "valid_answers": "numeric"},
    {"question": "Rate your Alcohol Use (0-9):", "key": "Alcohol use", "type": "numeric", "valid_answers": "numeric"},
    {"question": "Rate your Passive Smoking (0-9):", "key": "Passive Smoker", "type": "numeric", "valid_answers": "numeric"},
    {"question": "Rate your Obesity Level (0-9):", "key": "Obesity", "type": "numeric",     "valid_answers": "numeric"},
    {"question": "Rate your Smoking Habit (0-9):", "key": "Smoking", "type": "numeric", "valid_answers": "numeric"},
    {"question": "Rate your Coughing of Blood Frequency (0-9):", "key": "Coughing of Blood", "type": "numeric", "valid_answers": "numeric"},
    {"question": "Rate your Balanced Diet (0-9):", "key": "Balanced Diet", "type": "numeric", "valid_answers": "numeric"},
    {"question": "Rate your Chest Pain Level (0-9):", "key": "Chest Pain", "type": "numeric", "valid_answers": "numeric"},
    {"question": "Rate your Fatigue Level (0-9):", "key": "Fatigue", "type": "numeric", "valid_answers": "numeric"},
    {"question": "Rate your Genetic Risk (0-9):", "key": "Genetic Risk", "type": "numeric", "valid_answers": "numeric"},
]

# Request model for chatbot queries
class QueryRequest(BaseModel):
    user_id: str
    question: str

@app.post("/chat/", summary="Chat with the AI for health queries and NCD assessment")
async def chat(query: QueryRequest):
    """Handles chatbot queries and dynamically assesses NCD risk within the conversation."""
    user_id = query.user_id
    user_question = query.question.strip().lower()

    # Initialize session if not exists
    if user_id not in user_sessions:
        user_sessions[user_id] = {"stage": "conversation", "answers": {}, "question_index": None}
    
    session = user_sessions[user_id]
    
    # If assessment has not started, respond normally
    if session["stage"] == "conversation":
        if any(keyword in user_question for keyword in ["cancer risk", "risk assessment", "health check", "assessment"]):
            session["stage"] = "assessment"
            session["question_index"] = 0
            return {"response": "Let's begin the assessment. " + cancer_questions[0]["question"]}
        else:
            return {"response": retrieve_relevant_info(user_question)}
    
    # Proceed with the assessment
    if session["stage"] == "assessment":
        current_index = session["question_index"]
        current_question = cancer_questions[current_index]
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
            if current_index >= len(cancer_questions):
                session["stage"] = "conversation"
                return {"response": generate_assessment_result(session["answers"])}
            
            next_question = cancer_questions[current_index]
            
            session["question_index"] = current_index
            return {"response": next_question["question"]}

def generate_assessment_result(answers):
    input_features = [answers[q["key"]] for q in cancer_questions]
    print(input_features)

    input_array = np.array(input_features).reshape(1, -1)
    input_scaled = scaler.transform(input_array)
    prediction = cancer_model.predict(input_scaled)[0]

    levels = {0: "Low", 1: "Medium", 2: "High"}

    
    
if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server...")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)



# """Generates a structured health risk summary based on user responses."""
#     risks = {"Respiratory Health": [], "Cardiovascular Health": [], "Overall Well-being": []}
#     recommendations = {"Respiratory Health": [], "Cardiovascular Health": [], "Overall Well-being": []}

#     # Smoking Risks
#     if answers.get("smoke") == "yes":
#         risks["Respiratory Health"].append("Smoking increases the risk of lung disease, chronic bronchitis, and lung cancer.")
#         recommendations["Respiratory Health"].append("Consider reducing or quitting smoking. Support groups and medical guidance can help.")

#     if answers.get("passive_smoke") == "yes":
#         risks["Respiratory Health"].append("Exposure to passive smoking may increase respiratory and cardiovascular risks.")
#         recommendations["Respiratory Health"].append("Avoid areas with high smoke exposure to reduce health risks.")

#     # Alcohol Risks
#     if answers.get("alcohol") == "yes":
#         alcohol_freq = answers.get("alcohol_frequency", 0)
#         if alcohol_freq > 3:
#             risks["Cardiovascular Health"].append("Frequent alcohol consumption can increase the risk of high blood pressure and heart disease.")
#             recommendations["Cardiovascular Health"].append("Reduce alcohol intake and monitor blood pressure regularly.")

#     # Female-Specific Risks
#     if answers.get("gender") == "female":
#         if answers.get("nipple_discharge") == "yes":
#             risks["Overall Well-being"].append("Nipple discharge may require medical evaluation for potential underlying issues.")
#             recommendations["Overall Well-being"].append("Consult a doctor to rule out any health concerns.")

#         if answers.get("post_menopause_bleeding") == "yes":
#             risks["Overall Well-being"].append("Post-menopausal bleeding should be checked by a doctor as it could indicate health issues.")
#             recommendations["Overall Well-being"].append("Seek medical advice to ensure early detection and treatment.")

#     # Generate formatted response
#     response = "Assessment complete! Based on your responses, here is a summary of your potential risk factors and recommendations:\n\n"

#     for category, risk_list in risks.items():
#         if risk_list:
#             response += f"🔹 **{category}**:\n"
#             for risk in risk_list:
#                 response += f"- {risk}\n"
#             if recommendations[category]:
#                 response += "✅ **Recommendation**:\n"
#                 for rec in recommendations[category]:
#                     response += f"- {rec}\n"
#             response += "\n"

#     return response.strip() if risks else "Your responses do not indicate significant risk factors. However, regular health checkups are recommended."
