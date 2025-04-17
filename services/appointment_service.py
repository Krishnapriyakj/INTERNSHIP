import datetime
import pandas as pd
import json
import time
from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from services.llm_service import get_llm

# Load hospital data
file_path = 'HOSPITAL LIST.xlsx'
hospital_df = pd.read_excel(file_path)

# Format extraction prompt template
FORMAT_EXTRACT_TEMPLATE = ChatPromptTemplate.from_template("""
From the given context:
1. Make the day into 3-letter format (Mon, Tue, Wed, Thu, Fri, Sat, Sun).
2. Expand department name (e.g., 'Card' to 'Cardiology').
3. Convert time to HH:MM in 24hr format (e.g., 10:00, 14:00).

Context:
{context}

Output in JSON form with same keys, no explanations:
""")

appointment_questions = [
    {"question": "What is the day of the appointment? (e.g., Mon, Tue)", "key": "day", "type": "text"},
    {"question": "What department do you need? (e.g., Cardiology, ENT)", "key": "department", "type": "text"},
    {"question": "What time do you prefer? (e.g., 10:00, 14:00)", "key": "time", "type": "text"},
]

user_sessions: Dict[str, Dict[str, Any]] = {}

def is_user_in_appointment_booking(user_id: str) -> bool:
    return user_id in user_sessions and user_sessions[user_id]["stage"] == "appointment"

def validate_day(day: str) -> bool:
    valid_days = {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}
    return day.lower() in valid_days

def validate_time(time_str: str) -> bool:
    try:
        datetime.datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def check_availability(user_time: str, availability: str) -> bool:
    try:
        start, end = map(lambda t: datetime.datetime.strptime(t.strip(), "%H:%M"), availability.replace('.', ':').split('-'))
        user_time_dt = datetime.datetime.strptime(user_time.strip(), "%H:%M")
        return start <= user_time_dt <= end
    except ValueError:
        return False

def get_available_hospitals(params: Dict[str, str]) -> tuple[str, pd.DataFrame]:
    day = params["day"].capitalize()
    dept = params["department"]
    
    filtered_df = hospital_df[hospital_df['Days'].str.contains(day, case=False, na=False)]
    if filtered_df.empty:
        return "No hospitals available on the selected day.", pd.DataFrame()
    
    filtered_df = filtered_df[filtered_df['Department'].str.contains(dept, case=False, na=False)]
    if filtered_df.empty:
        return "No hospitals found for the selected department.", pd.DataFrame()
    
    filtered_df = filtered_df[filtered_df.apply(lambda row: check_availability(params["time"], row['Time']), axis=1)]
    if filtered_df.empty:
        return "No hospitals available at the selected time.", pd.DataFrame()
    
    options = "Available options (enter the number to select):\n"
    for idx, row in filtered_df.reset_index().iterrows():
        options += f"{idx + 1}. {row['Hospital Name']} - {row['Doctor']} ({row['Time']})\n"
    return options, filtered_df

async def appointment_booking(user_id: str, user_question: str) -> Dict[str, str]:
    user_question = user_question.strip().lower()
    
    if user_question in ["stop", "exit", "cancel"]:
        if user_id in user_sessions:
            del user_sessions[user_id]
        return {"response": "Appointment booking cancelled."}
    
    if user_id not in user_sessions:
        user_sessions[user_id] = {"stage": "appointment", "answers": {}, "question_index": 0, "step": "questions"}
        return {"response": appointment_questions[0]["question"]}
    
    session = user_sessions[user_id]
    current_index = session["question_index"]
    
    if session["step"] == "questions":
        if current_index < len(appointment_questions):
            key = appointment_questions[current_index]["key"]
            
            # Validation
            if key == "day" and not validate_day(user_question):
                return {"response": "Please enter a valid day (e.g., Mon, Tue, Wed)."}
            elif key == "time" and not validate_time(user_question):
                return {"response": "Please enter a valid time in HH:MM format (e.g., 10:00)."}
            
            session["answers"][key] = user_question
            current_index += 1
            
            if current_index >= len(appointment_questions):
                llm = get_llm()
                formatted_response = llm.invoke(FORMAT_EXTRACT_TEMPLATE.format(context=json.dumps(session["answers"])))
                session["answers"] = json.loads(formatted_response)
                options, filtered_df = get_available_hospitals(session["answers"])
                session["filtered_df"] = filtered_df
                session["step"] = "select_hospital"
                return {"response": options}
            
            session["question_index"] = current_index
            return {"response": appointment_questions[current_index]["question"]}
    
    elif session["step"] == "select_hospital":
        try:
            choice = int(user_question) - 1
            filtered_df = session["filtered_df"]
            if 0 <= choice < len(filtered_df):
                session["selected_hospital"] = filtered_df.iloc[choice].to_dict()
                session["step"] = "personal_info"
                return {"response": "Please provide your name."}
            return {"response": "Invalid selection. Please choose a number from the list."}
        except ValueError:
            return {"response": "Please enter a valid number from the list."}
    
    elif session["step"] == "personal_info":
        if "name" not in session["answers"]:
            session["answers"]["name"] = user_question
            return {"response": "Please provide your age."}
        elif "age" not in session["answers"]:
            try:
                age = int(user_question)
                if 0 < age < 150:
                    session["answers"]["age"] = age
                    session["step"] = "payment"
                    from services.payment_service import process_payment
                    result = process_payment(age, session["answers"]["name"], 
                                          session["answers"]["department"], 
                                          session["answers"]["time"],
                                          session["selected_hospital"])
                    del user_sessions[user_id]
                    return {"response": result}
                return {"response": "Please enter a valid age (1-149)."}
            except ValueError:
                return {"response": "Please enter a numeric age."}
    
    return {"response": "Something went wrong. Please try again."}