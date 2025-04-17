import streamlit as st
import pandas as pd
import json
import qrcode
import time
from typing import Dict, Any
from services import (
    ncd_service,
    cancer_service,
    appointment_service,
    rag_service,
    conversation_service
)
from models.schema import QueryRequest
from services.payment_service import process_payment, generate_qr_code
import matplotlib.pyplot as plt
from io import BytesIO
import base64
st.set_page_config(
        page_title="Health Assistant",
        page_icon="🏥",
        layout="centered",
        initial_sidebar_state="expanded"
    )

# Custom CSS to make the window smaller and more compact
st.markdown("""
    <style>
        .main > div {
            max-width: 600px;
            padding: 1rem;
        }
        .stTextInput input, .stSelectbox select, .stNumberInput input {
            padding: 8px !important;
            font-size: 14px !important;
        }
        .stButton button {
            padding: 8px 16px !important;
            font-size: 14px !important;
        }
        .stChatMessage {
            padding: 8px 12px !important;
            margin-bottom: 8px !important;
        }
        .stDataFrame {
            font-size: 14px !important;
        }
        .sidebar .sidebar-content {
            width: 200px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_details' not in st.session_state:
    st.session_state.user_details = {}
if 'current_service' not in st.session_state:
    st.session_state.current_service = None
if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

# Load data files
@st.cache_data
def load_data():
    with open("data/ncd_questions.json", "r") as f:
        ncd_questions = json.load(f)
    with open("data/cancer_questions.json", "r") as f:
        cancer_questions = json.load(f)
    hospital_df = pd.read_excel("HOSPITAL LIST.xlsx")
    return ncd_questions, cancer_questions, hospital_df

ncd_questions, cancer_questions, hospital_df = load_data()

# Helper functions
def display_qr_code(name: str, fee: float):
    """Generate and display QR code for payment"""
    transaction_id = generate_qr_code(name, fee)
    st.session_state.transaction_id = transaction_id
    st.write(f"Please scan the QR code to pay ₹{fee}")
    
    # Generate QR code image
    upi_url = f"upi://pay?pa=bexcybiju0209@oksbi&pn={name}&am={fee}&cu=INR&tr={transaction_id}&tn=HospitalAppointmentFee"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=6, border=2)
    qr.add_data(upi_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Display in Streamlit
    buf = BytesIO()
    qr_img.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    st.image(img_bytes, caption="Scan to Pay", width=150)
    
    return transaction_id

def register_user():
    """Compact user registration form"""
    with st.form("user_registration"):
        st.subheader("User Registration", divider='gray')
        cols = st.columns(2)
        with cols[0]:
            name = st.text_input("Full Name", key="reg_name")
            age = st.number_input("Age", min_value=1, max_value=120, key="reg_age")
        with cols[1]:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"], key="reg_gender")
            phone = st.text_input("Phone Number", key="reg_phone")
        email = st.text_input("Email", key="reg_email")
        
        if st.form_submit_button("Register", use_container_width=True):
            if name and age and gender and email and phone:
                user_id = f"{name}_{int(time.time())}"
                st.session_state.user_id = user_id
                st.session_state.user_details = {
                    "name": name,
                    "age": age,
                    "gender": gender.lower(),
                    "email": email,
                    "phone": phone
                }
                st.success("Registration successful!")
                return True
            else:
                st.error("Please fill all fields")
                return False
    return False

def main_menu():
    """Compact main menu after registration"""
    st.sidebar.markdown("### Menu")
    option = st.sidebar.radio("Services:", [
        "Book Hospital Appointment",
        "NCD Assessment",
        "Cancer Assessment",
        "General Medical Queries"
    ], label_visibility="collapsed")
    
    if option == "Book Hospital Appointment":
        st.session_state.current_service = "appointment"
        book_appointment()
    elif option == "NCD Assessment":
        st.session_state.current_service = "ncd"
        ncd_assessment()
    elif option == "Cancer Assessment":
        st.session_state.current_service = "cancer"
        cancer_assessment()
    elif option == "General Medical Queries":
        st.session_state.current_service = "general"
        general_queries()

def book_appointment():
    """Compact hospital appointment booking flow"""
    st.title("Book Hospital Appointment")
    
    if 'appointment_stage' not in st.session_state:
        st.session_state.appointment_stage = "questions"
        st.session_state.appointment_answers = {}
        st.session_state.question_index = 0
    
    if st.session_state.appointment_stage == "questions":
        current_index = st.session_state.question_index
        questions = appointment_service.appointment_questions
        
        if current_index < len(questions):
            current_question = questions[current_index]
            st.markdown(f"**{current_question['question']}**")
            
            if current_question["key"] == "day":
                options = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
                answer = st.selectbox("Select day", options, key=f"appt_{current_question['key']}", label_visibility="collapsed")
            elif current_question["key"] == "department":
                departments = hospital_df['Department'].unique()
                answer = st.selectbox("Select department", departments, key=f"appt_{current_question['key']}", label_visibility="collapsed")
            elif current_question["key"] == "time":
                answer = st.text_input("Enter time (HH:MM)", key=f"appt_{current_question['key']}", label_visibility="collapsed")
            
            if st.button("Next", use_container_width=True):
                if current_question["key"] == "time" and not appointment_service.validate_time(answer):
                    st.error("Please enter a valid time in HH:MM format (e.g., 10:00)")
                else:
                    st.session_state.appointment_answers[current_question["key"]] = answer
                    st.session_state.question_index += 1
                    st.rerun()
        
        else:
            st.session_state.appointment_stage = "select_hospital"
            st.rerun()
    
    elif st.session_state.appointment_stage == "select_hospital":
        options, filtered_df = appointment_service.get_available_hospitals(st.session_state.appointment_answers)
        
        if filtered_df.empty:
            st.error(options)
            if st.button("Start Over", use_container_width=True):
                st.session_state.appointment_stage = "questions"
                st.session_state.question_index = 0
                st.rerun()
        else:
            st.markdown("**Available hospitals:**")
            st.dataframe(filtered_df[['Hospital Name', 'Doctor', 'Department', 'Time']], hide_index=True, use_container_width=True)
            
            choice = st.selectbox(
                "Select a hospital", 
                range(1, len(filtered_df)+1),
                format_func=lambda x: f"{x}. {filtered_df.iloc[x-1]['Hospital Name']} - {filtered_df.iloc[x-1]['Doctor']}",
                label_visibility="collapsed"
            )
            
            if st.button("Confirm", use_container_width=True):
                st.session_state.selected_hospital = filtered_df.iloc[choice-1].to_dict()
                st.session_state.appointment_stage = "payment"
                st.rerun()
    
    elif st.session_state.appointment_stage == "payment":
        st.markdown("**Appointment Summary:**")
        st.markdown(f"- Hospital: {st.session_state.selected_hospital['Hospital Name']}")
        st.markdown(f"- Doctor: {st.session_state.selected_hospital['Doctor']}")
        st.markdown(f"- Department: {st.session_state.selected_hospital['Department']}")
        st.markdown(f"- Time: {st.session_state.selected_hospital['Time']}")
        
        age = st.session_state.user_details["age"]
        if 18 <= age <= 50:
            st.markdown("**Payment is required for your age group (18-50 years)**")
            fee = 20.00
            
            if 'payment_done' not in st.session_state:
                display_qr_code(st.session_state.user_details["name"], fee)
                
                if st.button("I've made the payment", use_container_width=True):
                    payment_success = True
                    
                    if payment_success:
                        st.session_state.payment_done = True
                        st.success("Payment verified!")
                        st.rerun()
                    else:
                        st.error("Payment verification failed. Please try again.")
            else:
                result = process_payment(
                    age=age,
                    name=st.session_state.user_details["name"],
                    department=st.session_state.appointment_answers["department"],
                    time_slot=st.session_state.appointment_answers["time"],
                    hospital_info=st.session_state.selected_hospital
                )
                st.success(result)
                st.session_state.appointment_stage = "completed"
        else:
            result = process_payment(
                age=age,
                name=st.session_state.user_details["name"],
                department=st.session_state.appointment_answers["department"],
                time_slot=st.session_state.appointment_answers["time"],
                hospital_info=st.session_state.selected_hospital
            )
            st.success(result)
            st.session_state.appointment_stage = "completed"
    
    elif st.session_state.appointment_stage == "completed":
        st.success("Appointment booked successfully!")
        if st.button("Back to Menu", use_container_width=True):
            del st.session_state.appointment_stage
            del st.session_state.appointment_answers
            del st.session_state.question_index
            if 'selected_hospital' in st.session_state:
                del st.session_state.selected_hospital
            if 'payment_done' in st.session_state:
                del st.session_state.payment_done
            st.rerun()

def ncd_assessment():
    """Compact NCD assessment flow"""
    st.title("NCD Risk Assessment")
    
    if 'ncd_stage' not in st.session_state:
        st.session_state.ncd_stage = "start"
        st.session_state.ncd_answers = {}
        st.session_state.ncd_question_index = 0
    
    if st.session_state.ncd_stage == "start":
        st.markdown("This assessment evaluates your risk factors for Non-Communicable Diseases (NCDs).")
        if st.button("Begin Assessment", use_container_width=True):
            st.session_state.ncd_stage = "assessment"
            st.rerun()
    
    elif st.session_state.ncd_stage == "assessment":
        current_index = st.session_state.ncd_question_index
        questions = ncd_questions["questions"]
        
        if current_index < len(questions):
            current_question = questions[current_index]
            
            if "depends_on" in current_question:
                dependency_key = current_question["depends_on"]
                condition = current_question["condition"]
                if st.session_state.ncd_answers.get(dependency_key) != condition:
                    st.session_state.ncd_question_index += 1
                    st.rerun()
                    return
            
            st.markdown(f"**{current_question['question']}**")
            
            if current_question["valid_answers"] == "numeric":
                answer = st.number_input("Enter your answer", min_value=0, key=f"ncd_{current_question['key']}", label_visibility="collapsed")
            else:
                answer = st.radio(
                    "Select your answer", 
                    current_question["valid_answers"],
                    key=f"ncd_{current_question['key']}",
                    label_visibility="collapsed",
                    horizontal=True
                )
            
            if st.button("Next", use_container_width=True):
                st.session_state.ncd_answers[current_question["key"]] = answer
                st.session_state.ncd_question_index += 1
                st.rerun()
        
        else:
            st.session_state.ncd_stage = "results"
            st.rerun()
    
    elif st.session_state.ncd_stage == "results":
        result = ncd_service.generate_assessment_result(st.session_state.ncd_answers)
        st.markdown(result)
        
        if st.button("Complete Assessment", use_container_width=True):
            del st.session_state.ncd_stage
            del st.session_state.ncd_answers
            del st.session_state.ncd_question_index
            st.rerun()

def cancer_assessment():
    """Compact cancer risk assessment flow"""
    st.title("Cancer Risk Assessment")
    
    if 'cancer_stage' not in st.session_state:
        st.session_state.cancer_stage = "start"
        st.session_state.cancer_answers = {}
        st.session_state.cancer_question_index = 0
    
    if st.session_state.cancer_stage == "start":
        st.markdown("This assessment evaluates your risk factors for various types of cancer.")
        if st.button("Begin Assessment", use_container_width=True):
            st.session_state.cancer_stage = "assessment"
            st.rerun()
    
    elif st.session_state.cancer_stage == "assessment":
        current_index = st.session_state.cancer_question_index
        questions = cancer_questions["questions"]
        
        if current_index < len(questions):
            current_question = questions[current_index]
            st.markdown(f"**{current_question['question']}**")
            
            answer = st.slider(
                "Select your rating", 
                min_value=0, 
                max_value=9, 
                key=f"cancer_{current_question['key']}",
                label_visibility="collapsed"
            )
            
            if st.button("Next", use_container_width=True):
                st.session_state.cancer_answers[current_question["key"]] = answer
                st.session_state.cancer_question_index += 1
                st.rerun()
        
        else:
            st.session_state.cancer_stage = "results"
            st.rerun()
    
    elif st.session_state.cancer_stage == "results":
        risk = cancer_service.predict_cancer_risk(st.session_state.cancer_answers)
        detailed_recommendations = cancer_service.generate_detailed_recommendations(st.session_state.cancer_answers)
        
        st.markdown(f"**Your predicted cancer risk level:** {risk}")
        st.markdown(detailed_recommendations)
        
        if st.button("Complete Assessment", use_container_width=True):
            del st.session_state.cancer_stage
            del st.session_state.cancer_answers
            del st.session_state.cancer_question_index
            st.rerun()

def general_queries():
    """Compact general medical queries chat interface"""
    st.title("Medical Assistant")
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    if prompt := st.chat_input("Ask your medical question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        query = QueryRequest(user_id=st.session_state.user_id, question=prompt)
        response = rag_service.retrieve_relevant_info(query.question)
        
        with st.chat_message("assistant"):
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})

# Main app flow
def main():

    if not st.session_state.user_id:
        if register_user():
            st.rerun()
    else:
        st.sidebar.markdown(f"**Welcome, {st.session_state.user_details['name']}!**")
        if st.sidebar.button("Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

        main_menu()

if __name__ == "__main__":
    main()