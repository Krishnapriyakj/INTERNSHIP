from fastapi import FastAPI
from pydantic import BaseModel
from langchain_ollama import OllamaLLM, OllamaEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
import joblib  # For loading the trained model
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import json
import datetime
import pandas as pd
from collections import defaultdict
import openpyxl

file_path='HOSPITAL LIST.xlsx'
hospital_df=pd.read_excel(file_path)

# Initialize FastAPI
app = FastAPI(title="Cancer Risk Assessment Chatbot", version="1.0")

# ChromaDB Path
CHROMA_DB_PATH = "chroma_db"

# Load trained cancer prediction model
MODEL_PATH = "cancer_prediction_model.pkl"
cancer_model = joblib.load(MODEL_PATH)
SCALER_PATH = "scaler.pkl"
scaler = joblib.load(SCALER_PATH)

# Define the RAG prompt template
PROMPT_TEMPLATE = """
You are an AI health assistant that answers medical questions.
Use the following context to help answer the user's query. If context is empty simply give a general health companion response.

====================
Context:
{context}

====================

Question: {question}
"""

FORMAT_EXTRACT_TEMPLATE = ChatPromptTemplate.from_template("""
From the given context. 
1. Make the day into 3 letter format if not already in such as (Mon, Tue, Wed, Thu, Fri, Sat, Sun).
2. Expand department name such as 'Card' to 'Cardiology'.
3. Convert time to HH:MM in 24hr format if not already in such as 10:00, 12:00, 14:00, etc.                                                           
------------
Context:
{context}
                                                           
------------
Say only the output same as in the JSON form as the context keys. No explanations needed.
""")

DECISION_MAKER = ChatPromptTemplate.from_template("""
Analyse the given prompt and return only one among the 3 values based upon their use:

"book_appointment" - If the prompt is asking to book an appointment. This can enable users to book an appointment with the hospital. 
                    The context may or may not have data such as day, time, department, etc.

"cancer_risk_assessment" - If the prompt is asking to assess the cancer risk. This can enable users to assess their cancer risk based on the given parameters.
                            Used when user asks about their chances or risk of getting cancer.

"generic" - If not following any other usecase a 'generic' indicate the response may be a LLM response chat or a RAG response. Both will fall in this category.

Only say one among the 3 value. No explanations and elaborations needed.
PROMPT : {prompt}
""")

model = OllamaLLM(model="llama3.2")

# Define attributes for cancer risk assessment
cancer_questions = [
    {"question": "Rate your Occupational Hazards (0-9):", "key": "OccuPational Hazards", "type": "numeric"},
    {"question": "Rate your Alcohol Use (0-9):", "key": "Alcohol use", "type": "numeric"},
    {"question": "Rate your Passive Smoking (0-9):", "key": "Passive Smoker", "type": "numeric"},
    {"question": "Rate your Obesity Level (0-9):", "key": "Obesity", "type": "numeric"},
    {"question": "Rate your Smoking Habit (0-9):", "key": "Smoking", "type": "numeric"},
    {"question": "Rate your Coughing of Blood Frequency (0-9):", "key": "Coughing of Blood", "type": "numeric"},
    {"question": "Rate your Balanced Diet (0-9):", "key": "Balanced Diet", "type": "numeric"},
    {"question": "Rate your Chest Pain Level (0-9):", "key": "Chest Pain", "type": "numeric"},
    {"question": "Rate your Fatigue Level (0-9):", "key": "Fatigue", "type": "numeric"},
    {"question": "Rate your Genetic Risk (0-9):", "key": "Genetic Risk", "type": "numeric"},
]

appointment_questions = [
    {"question": "What is the day of the appointment?", "key": "day", "type": "text"},
    {"question": "What is the department of the appointment?", "key": "department", "type": "text"},
    {"question": "What is the time of the appointment?", "key": "time", "type": "text"},
]

# Store user sessions
user_sessions = {}

def get_embedding_function():
    return OllamaEmbeddings(model="nomic-embed-text")

def book_appointment(params):
    filtered_df = hospital_df[hospital_df['Days'].str.contains(params["day"], case=False, na=False)]

    if filtered_df.empty:
        return "No hospitals found for the selected day."
    
    filtered_df = filtered_df[filtered_df['Department'].str.contains(params["department"], case=False, na=False)]

    if not filtered_df.empty:
        return "No hospitals found for the selected department."
    
    def check_availability(user_time, availability):
        try:
            user_time = user_time.replace('.', ':')
            availability = availability.replace('.', ':')

            start, end = map(lambda t: datetime.datetime.strptime(t.strip(), "%H:%M"), availability.split('-'))
            user_time = datetime.datetime.strptime(user_time.strip(), "%H:%M")

            return start <= user_time <= end
        except ValueError as e:
            print(f"Error parsing times: {e}")
            return False


    def time_filter(row):
        return check_availability(params["time"], row['Time'])

    filtered_df = filtered_df[filtered_df.apply(time_filter, axis=1)]

    if filtered_df.empty:
        return "No hospitals found for the selected time."
    
    available = ""
    for idx, row in filtered_df.iterrows():
        available += f"{idx + 1}. Hospital: {row['Hospital Name']}, Doctor: {row['Doctor']} \n"

    return available

def retrieve_relevant_info(query_text):
    embedding_function = get_embedding_function()
    db = Chroma(persist_directory=CHROMA_DB_PATH, embedding_function=embedding_function)
    results = db.similarity_search_with_score(query_text, k=2)

    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    if results:
        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
        prompt = prompt_template.format(context=context_text, question=query_text)
    else:
        prompt = prompt_template.format(context="<empty>", question=query_text)
       
    return model.invoke(prompt)

def predict_cancer_risk(user_answers):
    input_features = [user_answers[q["key"]] for q in cancer_questions]
    input_array = np.array(input_features).reshape(1, -1)
    input_scaled = scaler.transform(input_array)
    prediction = cancer_model.predict(input_scaled)[0]
    levels = {0: "Low", 1: "Medium", 2: "High"}
    return levels[prediction]

class QueryRequest(BaseModel):
    user_id: str
    question: str

@app.post("/chat/", summary="Chat with AI for health queries and cancer assessment")
async def chat(query: QueryRequest):
    user_id = query.user_id
    user_question = query.question.strip().lower()

    if user_id not in user_sessions:
        user_sessions[user_id] = {"stage": "conversation", "answers": {}, "question_index": None}
    session = user_sessions[user_id]

    if session["stage"] == "appointment":
        current_index = session["question_index"]
        current_question = appointment_questions[current_index]
        key = current_question["key"]
        session["answers"][key] = user_question
        current_index += 1
        if current_index >= len(appointment_questions):
            session["stage"] = "conversation"
            answers = session["answers"]
            response = model.invoke(FORMAT_EXTRACT_TEMPLATE.format(context=json.dumps(answers)))
            params = json.loads(response)
            
            return {"response": book_appointment(params)}
        session["question_index"] = current_index
        return {"response": appointment_questions[current_index]["question"]}

    if session["stage"] == "assessment":
        current_index = session["question_index"]
        current_question = cancer_questions[current_index]
        key = current_question["key"]
        try:
            session["answers"][key] = int(user_question)
        except ValueError:
            return {"response": "Please provide a valid number between 0 and 9."}
        current_index += 1
        if current_index >= len(cancer_questions):
            session["stage"] = "conversation"
            risk = predict_cancer_risk(session["answers"])
            session["stage"] = "conversation"
            return {"response": f"Cancer Risk Assessment Completed. Your predicted risk level: {risk}"}
        session["question_index"] = current_index
        return {"response": cancer_questions[current_index]["question"]}
    
    decision = model.invoke(DECISION_MAKER.format(prompt=user_question))

    print("This is a decision: ", decision)
    
    if(decision == "\"cancer_risk_assessment\""):
        if session["stage"] == "conversation":
            session["stage"] = "assessment"
            session["question_index"] = 0
            return {"response": "Let's begin the cancer risk assessment. " + cancer_questions[0]["question"]}
    
    elif(decision == "\"book_appointment\""):
        session["stage"] = "appointment"
        session["question_index"] = 0
        return {"response": appointment_questions[0]["question"]}

    elif(decision == "\"generic\""):
            return {"response": retrieve_relevant_info(user_question)}
    

if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server...")
    uvicorn.run("query:app", host="127.0.0.1", port=8000, reload=True)
