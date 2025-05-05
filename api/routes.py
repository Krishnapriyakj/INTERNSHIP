# Add to api/routes.py
from fastapi import APIRouter, UploadFile, File
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any
from fastapi import HTTPException
from services.rag_service import retrieve_relevant_info
from services.llm_service import get_llm
from langchain_core.prompts import ChatPromptTemplate
import time

router = APIRouter()

HOSPITAL_DATA = None
HOSPITAL_DATA_PATH = Path('HOSPITAL LIST.xlsx')
def load_hospital_data():
    global HOSPITAL_DATA
    try:
        if HOSPITAL_DATA_PATH.exists():
            HOSPITAL_DATA = pd.read_excel(HOSPITAL_DATA_PATH)
            # Clean up column names (remove extra spaces, etc.)
            HOSPITAL_DATA.columns = HOSPITAL_DATA.columns.str.strip()
            return True
        return False
    except Exception as e:
        print(f"Error loading hospital data: {str(e)}")
        return False
if not load_hospital_data():
    print("Warning: Could not load hospital data")

# Load assessment questions
def load_questions(file_path: str) -> Dict[str, Any]:
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Failed to load questions from {file_path}: {str(e)}")
        return {"questions": []}

NCD_QUESTIONS = load_questions('data/ncd_questions.json')
CANCER_QUESTIONS = load_questions('data/cancer_questions.json')

@router.get("/hospitals/all", summary="Get all hospital data")
async def get_all_hospitals() -> Dict[str, Any]:
    """Returns all hospital data from the Excel file"""
    if HOSPITAL_DATA is None:
        if not load_hospital_data():
            raise HTTPException(
                status_code=503,
                detail="Hospital data not available. Please try again later."
            )
    
    try:
        # Convert to list of dictionaries
        hospitals = HOSPITAL_DATA.to_dict(orient='records')
        
        # Clean data - handle NaN values and format times
        for hospital in hospitals:
            for key, value in hospital.items():
                if pd.isna(value):
                    hospital[key] = None
                elif key == 'Time':
                    # Format time if needed
                    hospital[key] = str(value).replace('.', ':')
        
        return {"hospitals": hospitals}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing hospital data: {str(e)}"
        )

@router.get("/hospitals/departments", summary="Get list of departments")
async def get_departments() -> Dict[str, Any]:
    """Returns unique list of departments"""
    if HOSPITAL_DATA is None:
        if not load_hospital_data():
            return {"departments": []}
    
    try:
        departments = HOSPITAL_DATA['Department'].unique().tolist()
        # Clean department names
        departments = [str(dept).strip() for dept in departments if pd.notna(dept)]
        return {"departments": sorted(departments)}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing departments: {str(e)}"
        )
@router.get("/hospitals/availability", summary="Check availability")
async def check_availability(day: str, department: str, time: str) -> Dict[str, Any]:
    """Check available slots for given criteria"""
    if HOSPITAL_DATA is None:
        if not load_hospital_data():
            return {"available": False, "hospitals": []}
    
    try:
        # Normalize inputs
        department = department.strip().lower()
        time = time.replace(':', '.').strip()
        
        # Filter by department
        dept_data = HOSPITAL_DATA[
            HOSPITAL_DATA['Department'].str.lower().str.contains(department)
        ]
        
        # Filter by day availability
        available_slots = []
        for _, row in dept_data.iterrows():
            days_range = str(row['Days']).strip()
            time_range = str(row['Time']).strip().replace(':', '.')
            
            # Check day availability
            day_match = (
                day in days_range or
                "Mon-Sunday" in days_range or
                ("Mon-Friday" in days_range and day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
            )
            
            # Check time availability (simple contains check)
            time_match = time in time_range
            
            if day_match and time_match:
                available_slots.append({
                    "Hospital Name": str(row['Hospital Name']).strip(),
                    "Department": str(row['Department']).strip(),
                    "Doctor": str(row['Doctor']).strip(),
                    "Time": time_range.replace('.', ':')
                })
        
        return {"available": len(available_slots) > 0, "hospitals": available_slots}
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error checking availability: {str(e)}"
        )

@router.post("/appointments/book", summary="Book appointment")
async def book_appointment(appointment_data: dict):
    """Book appointment with payment verification in terminal"""
    print("\n=== Payment Verification ===")
    print(f"Attempting to book appointment for {appointment_data['user_name']}")
    print(f"Hospital: {appointment_data['Hospital Name']}")
    print(f"Doctor: {appointment_data['Doctor']}")
    print(f"Time: {appointment_data['Time']}")
    
    # Simulate payment verification in terminal
    while True:
        verification = input("Was the payment successful? (yes/no): ").strip().lower()
        if verification in ['yes', 'no']:
            break
        print("Please enter 'yes' or 'no'")
    
    if verification == 'yes':
        # Generate token
        token_number = int(time.time()) % 10000
        print(f"Payment verified! Token number: {token_number}")
        
        return {
            "success": True,
            "message": "Appointment booked successfully",
            "token": token_number,
            "details": appointment_data
        }
    else:
        print("Payment verification failed")
        return {
            "success": False,
            "message": "Payment verification failed"
        }
    
@router.get("/data/ncd_questions", summary="Get NCD questions")
async def get_ncd_questions() -> Dict[str, Any]:
    """Returns NCD assessment questions"""
    return NCD_QUESTIONS

@router.get("/data/cancer_questions", summary="Get Cancer questions")
async def get_cancer_questions() -> Dict[str, Any]:
    """Returns Cancer assessment questions"""
    return CANCER_QUESTIONS

@router.post("/assessments/ncd", summary="Process NCD assessment")
async def process_ncd_assessment(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process NCD assessment answers and return results with risks and recommendations"""
    try:
        # Load questions and recommendations
        with open('data/ncd_questions.json', 'r') as f:
            questions_data = json.load(f)
        with open('data/ncd_risks_recommendations.json', 'r') as f:
            risks_data = json.load(f)
        
        answers = data.get('answers', {})
        results = "NCD Risk Assessment Results:\n\n"
        
        # Generate risk assessment
        for category, has_risk in risks_data.get('risks', {}).items():
            category_risks = []
            category_recommendations = []
            
            # Check each risk factor in the category
            for factor_key, factor_value in answers.items():
                if factor_key in risks_data.get('risk_details', {}).get(category, {}):
                    risk_detail = risks_data['risk_details'][category][factor_key]
                    recommendation = risks_data['recommendations'][category].get(factor_key, "")
                    
                    # For numeric answers (like alcohol frequency)
                    if isinstance(factor_value, (int, float)):
                        threshold = 3  # Example threshold - adjust as needed
                        if factor_value > threshold:
                            category_risks.append(risk_detail)
                            category_recommendations.append(recommendation)
                    # For yes/no answers
                    elif factor_value.lower() == 'yes':
                        category_risks.append(risk_detail)
                        category_recommendations.append(recommendation)
            
            if category_risks:
                results += f"🔴 {category} Risks:\n"
                for risk in category_risks:
                    results += f"- {risk}\n"
                
                results += "\n🟢 Recommendations:\n"
                for rec in category_recommendations:
                    results += f"- {rec}\n"
                results += "\n"
        
        if len(results) == len("NCD Risk Assessment Results:\n\n"):
            results += "Your responses don't indicate significant risk factors. Maintain your healthy habits!\n"
        
        return {"results": results}
    
    except Exception as e:
        return {"error": f"Failed to process assessment: {str(e)}"}

@router.post("/assessments/cancer", summary="Process Cancer assessment")
async def process_cancer_assessment(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process Cancer assessment answers and return results with risks and recommendations"""
    try:
        # Load questions and recommendations
        with open('data/cancer_questions.json', 'r') as f:
            questions_data = json.load(f)
        with open('data/cancer_risks_recommendation.json', 'r') as f:
            risks_data = json.load(f)
        
        answers = data.get('answers', {})
        results = "Cancer Risk Assessment Results:\n\n"
        risk_categories = set()
        
        # Determine which risk categories apply
        for question in questions_data.get('questions', []):
            q_key = question.get('key')
            answer = answers.get(q_key, 0)
            
            # Check if answer indicates risk (score >= 5)
            if isinstance(answer, (int, float)) and answer >= 5:
                # Find which categories this factor affects
                for category, factors in risks_data.get('risk_details', {}).items():
                    if q_key in factors:
                        risk_categories.add(category)
        
        # Generate detailed results for each relevant category
        for category in risk_categories:
            results += f"⚠️ {category} Risk:\n"
            
            # List risk factors
            for factor_key, factor_detail in risks_data['risk_details'][category].items():
                if factor_key in answers and (
                    (isinstance(answers[factor_key], (int, float)) and answers[factor_key] >= 5) or
                    (isinstance(answers[factor_key], str) and answers[factor_key].lower() == 'yes')
                ):
                    results += f"- {factor_detail}\n"
            
            # Add recommendations
            results += "\n✅ Recommendations:\n"
            for factor_key, recommendation in risks_data['recommendations'][category].items():
                if factor_key in answers and (
                    (isinstance(answers[factor_key], (int, float)) and answers[factor_key] >= 5) or
                    (isinstance(answers[factor_key], str) and answers[factor_key].lower() == 'yes')
                ):
                    results += f"- {recommendation}\n"
            
            results += "\n"
        
        if not risk_categories:
            results += "Your responses indicate low risk across all categories. Maintain healthy habits!\n"
        else:
            results += "Remember: This assessment is not a diagnosis. Consult a healthcare professional for personalized advice."
        
        return {"results": results}
    
    except Exception as e:
        return {"error": f"Failed to process assessment: {str(e)}"}

@router.post("/appointments/book", summary="Book appointment")
async def book_appointment(data: Dict[str, Any]) -> Dict[str, Any]:
    """Book a hospital appointment"""
    # In a real app, you'd save to database
    # This is a mock implementation
    return {
        "success": True,
        "message": f"Appointment booked with {data.get('doctor', 'doctor')} at {data.get('hospital', 'hospital')}",
        "details": data
    }

@router.post("/chat/query", summary="Handle medical query")
async def handle_medical_query(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process medical query using RAG + LLM"""
    try:
        question = data.get("question", "").strip()
        if not question:
            return {"response": "Please provide a question to answer"}
        
        # Get response from RAG service
        rag_response = retrieve_relevant_info(question)
        
        # Format the response
        response = {
            "response": rag_response,
            "type": "text",
            "options": []
        }
        
        return response
    
    except Exception as e:
        return {"response": f"Error processing your query: {str(e)}"}